import asyncio
import aiofiles

import logging
import os

from schemas import QuestionType

from langchain_deepseek import ChatDeepSeek
from langchain_gigachat import GigaChat

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_community.document_loaders import TextLoader

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

        self.text_chain = self.create_text_chain()
        self.audio_chain = self.create_audio_chain()
        
        #self.rag_chain = self.create_rag_chain()

        self.embed = {}
        self.vector_base = {}


    '''def create_rag_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ('system', 'аааааааааа')
            ('human', 'История диалога: {chat_history}, релевантный контекст из базы знаний: {context}, вопрос пользователя: {question}')
        ])
        chain = prompt | self.text_llm | StrOutputParser()
        return chain'''
    
    def create_audio_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ('system', 'Ты - научный ассистент, который анализирует расшифровки аудио лекций и отвечает по ним на вопросы пользователя. Необходимо различать интонации речи и на чём акцентирует внимание говорящий.'),
            ('human', 'Вопрос пользователя: {question} , расшифровка аудио: {transcription}')
        ])
        chain = prompt | self.audio_llm | StrOutputParser()
        return chain

    def create_text_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ('system', 'Ты - научный ассистент, который отвечает на вопросы пользователя. Необходимо отвечать по сути и четко, не забывая контекст.'),
            ('human', 'Вопрос пользователя: {question}, контекст {context}')
        ])
        chain = prompt | self.text_llm | StrOutputParser()
        return chain
    
    async def generate_answer(self, question_text: str, media_path: str, question_type: int) -> str:
        match question_type:
            case QuestionType.TEXT:
                return await self.process_text(question_text, media_path)
            
            case QuestionType.AUDIO:
                return await self.process_audio(question_text, media_path)
            
            case QuestionType.VIDEO:
                return await self.process_video(question_text, media_path)
            
            case _:
                return "Incorrect content type"
            
    async def process_text(self, question_text: str, media_path: str) -> str:
        logger.info('Started processing text: {question_text}')
        try:
            loader = TextLoader(media_path)
            documents = await loader.aload()

            context = documents[0].page_content if documents else ""

            response = await self.text_chain.ainvoke({
                "question" : question_text,
                "context" : context
            })
            logger.info('Ended processing text: {question_text}')
            return response
        
        except Exception as e:
            logger.error(f"Error processing text: {e}")

    async def process_audio(self, question_text: str, media_path: str) -> str:
        logger.info('Started processing audio: {media_path}')
        try:
            with open(media_path, 'rb'):
                responce = await self.audio_chain.ainvoke({
                    'input' : [
                        {'type' : 'text', 'text' : question_text},
                        {'type' : 'audio_url', 'audio_url' : {'url' : f'file://{media_path}'}}
                    ]
                })
                logger.info('Ended processing audio: {media_path}')
                return responce
        
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
    