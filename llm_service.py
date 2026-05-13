import asyncio
import aiofiles

import logging
import os
import datetime

from typing import List, Dict

from langchain_deepseek import ChatDeepSeek
from langchain_gigachat import GigaChat

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.text_llm_key = os.getenv('TEXT_LLM_API_KEY', '')
        self.audio_llm_key = os.getenv('AUDIO_LLM_API_KEY', '')

        self.text_llm = ChatDeepSeek(
            api_key=self.text_llm_key,
            model="deepseek-chat",
            temperature=0.5
        )

        self.audio_llm = GigaChat(
            credentials=self.audio_llm_key,
            scope="GIGACHAT_API_PERS",
            model=os.getenv('GIGACHAT_MODEL'),
            verify_ssl_certs=False
        )
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name='intfloat/multilingual-e5-small',
            model_kwargs={'device':'cpu'},
            encode_kwargs={'normalize_embeddings': True}
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

        self.rag_chain = self.create_rag_chain()


    def create_rag_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ('system', '''Ты - научный ассистент. Отвечай на пользовательские вопросы при помощи истории предыдущего диалога и необходимых частей из базы знаний.
             Обрати внимание:
             1. Отвечай конкретно по вопросу
             2. Учитывай предыдущий контекст диалога'''),
            ('human', 'История диалога: {chat_history}, релевантный контекст из базы знаний: {context}, текущий вопрос пользователя: {question}')
        ])
        chain = prompt | self.text_llm | StrOutputParser()
        return chain
    
    def format_history(self, history: List[Dict]):
        new_history = []
        for message in history:
            role = 'Пользователь'if message['role'] == 'user'else 'Ассистент'
            new_history.append(f"{role}: {message['content']}")
        return '\n'.join(new_history) if new_history else ""
    
    async def get_context(self, question: str):
        try:
            documents = await self.vector_base.asimilarity_search(question, k=3)
            context = '\n'.join(document.page_content for document in documents)
            return context if context else ""
        
        except Exception as e:
            logger.error(f"Error getting context: {e}")


    async def get_answer(self, question_text: str, history: List[Dict]) -> str:
        logger.info(f'Started processing text: {question_text}')
        try:
            prompt_history = self.format_history(history)
            db_context = await self.get_context(question_text)

            response = await self.rag_chain.ainvoke({
                "question" : question_text,
                "context" : db_context if db_context else "",
                "chat_history" : prompt_history
            })

            logger.info(f'Got answer for: {question_text}')
            return response
        
        except Exception as e:
            logger.error(f"Error processing text: {e}")

    async def add_media(self, media_id: str, media_path: str) -> bool:
        logger.info(f'Adding new media to LLM base: {media_id}')
        try:
            extention = os.path.splitext(media_path)[1].lower()
            
            metadata = {
                'media_id': media_id, # [TBD]: api generates this
                'source': media_path,
                'filename': os.path.basename(media_path),
                'type': extention[1:],
            }

            if (extention in ['.txt', '.md']): # [!] TEXT EXTENTIONS
                loader = TextLoader(media_path)
                documents = await loader.aload()
                
                for document in documents:
                    document.metadata.update(metadata)

                chunks = self.text_splitter.split_documents(documents)

                await self.vector_base.aadd_documents(chunks)
                logger.info(f" Success adding chunks from {media_id}")
                return True
            
            elif (extention in ['.mp3']): # [!] AUDIO EXTENTIONS
                # [TBD]: audio transcribtion
                return False
            elif (extention in ['.mp4']): # [!] VIDEO EXTENTIONS
                # [TBD]: video analysis
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
