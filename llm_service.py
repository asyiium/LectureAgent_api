import asyncio
import aiofiles

import logging
import os
import datetime

from typing import List, Dict
from enum import Enum
from langchain_gigachat import GigaChat, GigaChatEmbeddings

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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
            ca_bundle_file=os.getenv('CA_BUNDLE_PATH')
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
        def get_base_context(question_text: str):
            try:
                documents = self.vector_base.asimilarity_search(question_text, k=3)
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
                    
                    Правила ответов:
                    1. Отвечай конкретно по вопросу, но достаточно подробно
                    2. Учитывай предыдущий контекст 
                    3. При просьбе пользователя или при отсутствии информации в базе данных, ты можешь воспользоваться поиском в интернете
                    4. Если не знаешь ответа, честно напиши об этом.
                    
                    '''

        return create_agent(
            model=self.text_llm,
            tools=self.tools,
            system_prompt=prompt
        )
    
    def create_test_agent(self):
        prompt = '''Ты - научный ассистент-эксперт. Составляй тесты для проверки знаний пользователя и оценивай ответы пользователя.
                    
                    1. Придумывай конкретные вопросы из базы знаний
                    2. Указывай на ошибки и говори правильные ответы в случае неудачи пользователя
                    3. Оценивай каждый ответ по правильности в шкале от 1 до 5 (школьная оценка)
                    4. Не используй интернет ни при каком случае, только информация из базы данных
                    
                    '''

        return create_agent(
            model=self.text_llm,
            tools=self.tools,
            system_prompt=prompt
        )
    
    async def router_process(self, question_text: str, history: List[Dict]) -> InteractionType:
        history_text = ""
        if (history):
            last_messages = history[-3:]
            history_text = "\n".join([f"{message['role']}: {message['content'][:100]}" for message in last_messages])

        prompt = ''' Твоя задача - классифицировать вопрос пользователя в одну из двух категорий: "general" или "test"
                
                    Правила "general":
                    1. Спрашивают общую информацию
                    2. Спрашивают вопросы о нынешних трендах
                    3. Просят помощи в решение задачи
                    4. Все, что не содежит указаний на создание теста
                    
                    Правила "test":
                    1. Просьба поставить оценку
                    2. Желание пользователя проверить свои знания
                    3. Вопросы "проверь меня", "протестируй меня" и т.п
                
                '''
        try:
            response = await self.router_llm.ainvoke(prompt)
            result = response.content.strip().lower()

            if ('test' in result):
                logger.info(f'Got "test" answer from router LLM: {question_text}')
                return InteractionType.TEST
            else:
                logger.info(f'Got "no test" answer from router LLM: {question_text}')
                return InteractionType.GENERAL
        except Exception as e:
            logger.error(f'Error with router LLM: {e}')
            return InteractionType.GENERAL
        
    async def get_answer(self, question_text: str, history: List[Dict]) -> str:
        logger.info(f'Started processing text: {question_text}')
        try:
            interaction_type = self.router_process(question_text, history)
            chosen_agent = self.general_agent

            if (interaction_type == InteractionType.TEST):
                chosen_agent = self.test_agent

            messages = []
            for message in history[-5:]:
                if message.get('role') == 'user':
                    messages.append(HumanMessage(content=message['content']))
                elif message.get('role') == 'assistant':
                    messages.append(AIMessage(content=message['content']))

            messages.append(HumanMessage(content=question_text))

            response = await chosen_agent.ainvoke({'messages' : messages})

            if ('messages' in response and response['messages']):
                last_message = response["messages"][-1]
                answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                answer = "Агент не произвел ответ"

            logger.info(f'Got answer for: {question_text}')
            return answer
        
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return f'Ошибка при работе агента: str({e})'

    async def add_media(self, media_id: str, media_path: str) -> bool:
        logger.info(f'Adding new media to LLM base: {media_id}')
        try:
            extention = os.path.splitext(media_path)[1].lower()
            
            metadata = {
                'media_id': media_id,
                'source': media_path,
                'filename': os.path.basename(media_path),
                'type': extention[1:],
            }

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
            
            elif (extention in ['.mp3']): 
                try:
                    client = SaluteSpeechClient(client_credentials=self.audio_llm_key)
                    with open(media_path, "rb") as audio_file:
                        result = await client.audio.transcriptions.create(
                            file=audio_file,
                            language="ru-RU"
                        )
                    if (result and result.text):
                        documents = await loader.aload()
                
                        for document in documents:
                            document.metadata.update(metadata)

                        chunks = self.text_splitter.split_documents(documents)

                        await self.vector_base.aadd_documents(chunks)
                        logger.info(f" Success adding chunks from {media_id}")
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
