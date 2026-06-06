import asyncio
import aiofiles

import logging
import os
import datetime

from typing import List, Dict
from enum import Enum
from langchain_gigachat import GigaChat, GigaChatEmbeddings

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.documents import Document

from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredPowerPointLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from langchain.agents import create_agent
from langchain.tools import tool

from langchain_tavily import TavilySearch

from salute_speech.speech_recognition import SaluteSpeechClient 

logger = logging.getLogger(__name__)

class InteractionType(str, Enum):
    TEST = "test"
    GENERAL = "general"

class LLMService:
    def __init__(self):
        self.text_llm_key = os.getenv('TEXT_LLM_API_KEY', '')
        self.audio_llm_key = os.getenv('AUDIO_LLM_API_KEY', '')

        self.text_llm = GigaChat(
            credentials=self.text_llm_key,
            scope="GIGACHAT_API_PERS",
            ca_bundle_file=os.getenv('CA_BUNDLE_PATH'),
            streaming=True
        )
        
        self.router_llm = GigaChat(
            credentials=self.text_llm_key,
            scope="GIGACHAT_API_PERS",
            ca_bundle_file=os.getenv('CA_BUNDLE_PATH'),
            temperature=0.1
        )


        self.embeddings = GigaChatEmbeddings(
            credentials=self.text_llm_key,
            scope="GIGACHAT_API_PERS",
            model='Embeddings',
            ca_bundle_file=os.getenv('CA_BUNDLE_PATH')
        )

        self.vector_base = Chroma(
            persist_directory=os.getenv('VECTOR_STORE_PATH', './chroma_db'),
            embedding_function=self.embeddings,
            collection_name='lecture_knowledge_db'
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            separators=['\n\n', '\n', ' ']
        )

        self.tools = self.create_agent_tools()
        self.general_agent = self.create_general_agent()
        self.test_agent = self.create_test_agent()


    def create_agent_tools(self):
        @tool(description="Ищем информацию в векторной базе данных")
        def get_base_context(question_text: str, config: RunnableConfig):
            try:
                chat_id = config.get("configurable", {}).get("chat_id")
                logger.info(f"Searching chat_id={chat_id}, query={question_text[:100]}")
                
                documents = self.vector_base.similarity_search(question_text, k=3, filter={"chat_id" : chat_id})
                logger.info(f"Found {len(documents)} documents for chat_id={chat_id}")
                context = '\n'.join(document.page_content for document in documents)

                return f"Результат из базы данных:{context}" if context else "Нет информации из базы данных"
            
            except Exception as e:
                logger.error(f"Error getting vector base context: {e}")
                return ""

        @tool(description="Ищем информацию в сети интернет")
        def get_internet_context(question_text: str):
            try:
                tavily = TavilySearch(
                    api_key=os.getenv('TAVILY_API_KEY', ""),
                    max_results=3,
                    search_depth='basic'
                )

                result = tavily.invoke({'query' : question_text})
                if (result and result.get('results')):
                    compact_text = []
                    for s in result['results']:
                        compact_text.append(f'Источник: {s["url"]} \n {s["content"][:200]}')
                    return "Результат из интернета:" + '\n'.join(compact_text)
                return "Нет информации из интернета"
            except Exception as e:
                logger.error(f"Error getting internet context: {e}")
                return ""
            
        return [get_base_context, get_internet_context]

    def create_general_agent(self):
        prompt = '''Ты - научный ассистент. Отвечай на пользовательские вопросы при помощи истории предыдущего диалога и необходимых частей из базы знаний.
                
                ВАЖНЫЕ ПРАВИЛА:
                1. Если пользователь просит "транскрибируй", "расшифруй аудио" или подобное:
                - Вызови get_base_context с вопросом "транскрипция аудио"
                - Верни ПОЛНОСТЬЮ текст из базы данных, который содержит расшифровку
                - Не добавляй от себя "я не могу транскрибировать" - ты уже это сделал при загрузке!
                
                2. Если пользователь загрузил файлы в этот чат (chat_id: {chat_id}), ОБЯЗАТЕЛЬНО используй инструмент get_base_context для поиска информации
                
                3. Отвечай конкретно по вопросу, но достаточно подробно
                
                4. Учитывай предыдущий контекст
                
                5. При просьбе пользователя или при отсутствии информации в базе данных, ты можешь воспользоваться поиском в интернете
                
                6. Если не знаешь ответа, честно напиши об этом.
                
                ПРИМЕР:
                Пользователь: "Транскрибируй"
                Твои действия:
                1. get_base_context("транскрипция аудио")
                2. Если в ответе есть "Результат из базы данных:" - верни этот текст пользователю
                3. Не говори, что не можешь транскрибировать - файл уже обработан!
            
            '''

        return create_agent(
            model=self.text_llm,
            tools=self.tools,
            system_prompt=prompt
        )
    
    def create_test_agent(self):
        prompt = '''Ты - научный ассистент. Отвечай на пользовательские вопросы.
                    
                    АЛГОРИТМ РАБОТЫ (строго последовательно):
                    1. Сначала ОБЯЗАТЕЛЬНО вызови get_base_context
                    2. Проанализируй результат:
                    - Если есть "Результат из базы данных" и есть конкретная информация - используй её
                    - Если результат "Нет информации из базы данных" - вызови get_internet_context
                    3. Только после этого отвечай пользователю
                    
                    НЕЛЬЗЯ:
                    - Отвечать без вызова get_base_context
                    - Вызывать get_internet_context до get_base_context
                    - Вызывать инструменты повторно
                    
                    Пример правильной последовательности:
                    1. Вызов get_base_context("вопрос пользователя")
                    2. Если пусто → вызов get_internet_context("вопрос пользователя")  
                    3. Формирование ответа на основе полученной информации

                '''

        return create_agent(
            model=self.text_llm,
            tools=self.tools,
            system_prompt=prompt
        )
    
    
    async def generate_chat_title(self, first_message: str):
        logger.info(f'Generating chat title for: {first_message[:50]}...')
        
        prompt = f'''Твоя задача - создать короткое и информативное название для чата на основе первого сообщения пользователя.
        
        Правила:
        1. Не используй специальные символы в роде подчеркиваний (*, ^, & и так далее)
        2. Название должно быть на русском языке
        3. Рекомендуемая длина: 2-4 слова, максимальная - 50 символов
        4. Название должно пояснять и суммаризировать суть вопроса/темы
        5. Будь конкретным, но кратким

        Первое сообщение пользователя: "{first_message}"
        
        Название чата:'''
        
        try:
            response = await self.router_llm.ainvoke(prompt)

            title = response.content.strip()
            title = title.strip('"\',.?!;:')
            title = title.strip('»«›‹()[]{}')
            title = ' '.join(title.split())

            if len(title) > 50:
                title = title[:47] + "..."
            
            logger.info(f'Generated title: {title}')
            return title
            
        except Exception as e:
            logger.error(f'Error generating chat title: {e}')
            return f"Чат от {datetime.datetime.now().strftime('%d.%m %H:%M')}"

    async def router_process(self, question_text: str, history: List[Dict]) -> InteractionType:
        prompt = f''' Твоя задача - классифицировать вопрос пользователя в одну из двух категорий: "general" или "test". В ответе не используй кавычки или другие специальные символы (!, ", etc.)

                    Правила "general":
                    1. Спрашивают общую информацию
                    2. Спрашивают вопросы о нынешних трендах
                    3. Просят помощи в решение задачи
                    4. Сообщение "протестируй меня" должно ссылать на "test", но "протестируй что-то/какую-то возможность" должно приводить к "general"
                    5. Все, что не содежит указаний на создание теста
                    
                    Правила "test":
                    1. Просьба поставить оценку
                    2. Желание пользователя проверить свои знания
                    3. Вопросы "проверь меня", "протестируй меня", "помоги составить тест" и т.п

                    Вопрос пользователя: {question_text}
                '''
        try:
            response = await self.router_llm.ainvoke(prompt)
            result = response.content.strip().lower()
            
            logger.info(result)

            if ('test' in result):
                logger.info(f'Got "test" answer from router LLM: {question_text}')
                return InteractionType.TEST
            else:
                logger.info(f'Got "no test" answer from router LLM: {question_text}')
                return InteractionType.GENERAL
        except Exception as e:
            logger.error(f'Error with router LLM: {e}')
            return InteractionType.GENERAL
        
    async def get_answer(self, question_text: str, history: List[Dict], chat_id: str = None):
        logger.info(f'Started streaming for: {question_text}')
        
        try:
            interaction_type = await self.router_process(question_text, history)
            chosen_agent = self.general_agent if interaction_type == InteractionType.GENERAL else self.test_agent
            
            messages = []
            for m in history[-5:]:
                if m.get('role') == 'user':
                    messages.append(HumanMessage(content=m['content']))
                elif m.get('role') == 'assistant':
                    messages.append(AIMessage(content=m['content']))
            messages.append(HumanMessage(content=question_text))

            config = {"configurable": {"chat_id": chat_id}}

            async for chunk in chosen_agent.astream(
                {"messages": messages}, 
                config=config,
                stream_mode="messages"
            ):
                msg = chunk[0] if isinstance(chunk, tuple) else chunk
                if isinstance(msg, AIMessage) and msg.content:
                    yield msg.content
                    
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f'Ошибка при работе агента: {str(e)}'

    async def add_media(self, media_id: str, media_path: str, chat_id: str = None) -> bool:
        logger.info(f'Adding new media to LLM base: {media_id}')
        try:
            extention = os.path.splitext(media_path)[1].lower()
            
            metadata = {
                'media_id': media_id,
                'chat_id' : chat_id,
                'source': media_path,
                'filename': os.path.basename(media_path),
                'type': extention[1:],
            }

            logger.info(f"Processing file with extension: {extention}")
            logger.info(f"File path: {media_path}")
            logger.info(f"File exists: {os.path.exists(media_path)}")

            if (extention in ['.txt', '.md']):
                loader = TextLoader(media_path)
                documents = await loader.aload()
                
                for document in documents:
                    document.metadata.update(metadata)

                chunks = self.text_splitter.split_documents(documents)

                await self.vector_base.aadd_documents(chunks)
                logger.info(f" Success adding chunks from {media_id}")
                return True
            
            elif (extention in ['.pdf']):
                loader = PyPDFLoader(media_path)
                documents = await loader.aload()
                
                for document in documents:
                    document.metadata.update(metadata)

                chunks = self.text_splitter.split_documents(documents)

                await self.vector_base.aadd_documents(chunks)
                logger.info(f" Success adding chunks from {media_id}")
                return True
            
            elif (extention in ['.pptx', '.ppt']):
                loader = UnstructuredPowerPointLoader(
                    media_path,
                    mode='elements'
                )
                documents = await loader.aload()
                
                for document in documents:
                    document.metadata.update(metadata)

                chunks = self.text_splitter.split_documents(documents)

                await self.vector_base.aadd_documents(chunks)
                logger.info(f" Success adding chunks from {media_id}")
                return True
            
            elif (extention in ['.ogg', '.mp3', '.flac', '.wav']): 
                try:
                    client = SaluteSpeechClient(client_credentials=self.audio_llm_key)
                    with open(media_path, "rb") as audio_file:
                        result = await client.audio.transcriptions.create(
                            file=audio_file,
                            language="ru-RU"
                        )
                    if (result and result.text):
                        document = Document(
                            page_content=result.text,
                            metadata=metadata
                        )
                        
                        chunks = self.text_splitter.split_documents([document])
                        await self.vector_base.aadd_documents(chunks)
                        
                        logger.info(f"Success adding transcribed audio from {media_id}")
                        return True
                    else:
                        logger.info(f" Got no text from audio {media_id}")
                        return False
                    
                except Exception as e:
                    logger.error(f" Error with Salute client: {e}")
                    return False
            else:
                logger.warning(f" Unsupported media type")
                return False

        except Exception as e:
            logger.error(f" Error adding media: {e}")
            return False  

    async def delete_media(self, media_id: str) -> bool:
        logger.info(f'Deleting media for id: {media_id}')
        try:
            collection = self.vector_base._collection
            all_chunks = collection.get(
                where={'media_id': media_id}
            )

            if (all_chunks['ids']):
                collection.delete(ids=all_chunks['ids'])
                logger.info(f'Success deleting chunks for {media_id}')
            else:
                logger.warning(f'No chunks found for {media_id}')
            return True
        
        except Exception as e:
            logger.error(f'Error deleting media: {e}')
            return False
