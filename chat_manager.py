import logging
import asyncio

from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
import uuid

from llm_service import LLMService
from redis_client import RedisClient

logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self, llm_service: LLMService, redis_client: RedisClient):
        self.llm = llm_service
        self.redis = redis_client
        self.active_streams: Dict[str, asyncio.Task] = {}
    
    async def create_chat(self, user_id: Optional[str] = None, first_message: str = None) -> Dict:
        user_id = user_id or str(uuid.uuid4())
        chat_id = str(uuid.uuid4())
        
        chat_title = "Новый чат"
        if first_message:
            chat_title = await self.llm.generate_chat_title(first_message)
        
        await self.redis.client.sadd(f"user:{user_id}:chats", chat_id)
        await self.redis.create_chat(chat_id)
        await self.redis.set_chat_title(chat_id, chat_title)
        
        logger.info(f'Created chat {chat_id} for user {user_id} with title: {chat_title}')
        
        return {
            'chat_id': chat_id,
            'user_id': user_id,
            'chat_title': chat_title,
            'created_at': datetime.now().isoformat()
        }
    
    async def send_message(
        self, 
        chat_id: str, 
        message: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None] or str:
        
        if not await self.redis.check_chat(chat_id):
            raise ValueError(f"Chat {chat_id} not found")
        
        history = await self.redis.get_history(chat_id)

        await self.redis.add_message(chat_id, 'user', message)
        
        if stream:
            async def stream_generator():
                full_response = ""
                try:
                    async for chunk in self.llm.get_answer(
                        question_text=message,
                        history=history,
                        chat_id=chat_id
                    ):
                        full_response += chunk
                        yield chunk
                    
                    await self.redis.add_message(chat_id, 'assistant', full_response)
                    
                    if len(history) <= 1:
                        new_title = await self.llm.generate_chat_title(message)
                        await self.redis.set_chat_title(chat_id, new_title)
                        yield f"[TITLE]{new_title}[/TITLE]"
                        
                except Exception as e:
                    logger.error(f"Error in stream for chat {chat_id}: {e}")
                    yield f"Ошибка: {str(e)}"
            
            return stream_generator()
        else:
            full_response = ""
            async for chunk in self.llm.get_answer(message, history, chat_id):
                full_response += chunk
            
            await self.redis.add_message(chat_id, 'assistant', full_response)
            
            if len(history) <= 1:
                new_title = await self.llm.generate_chat_title(message)
                await self.redis.set_chat_title(chat_id, new_title)
            
            return full_response
    
    async def get_chat_history(self, chat_id: str, limit: int = 50) -> List[Dict]:
        if not await self.redis.check_chat(chat_id):
            raise ValueError(f"Chat {chat_id} not found")
        
        return await self.redis.get_history(chat_id, limit)
    
    async def get_user_chats(self, user_id: str) -> List[Dict]:
        chat_ids = await self.redis.client.smembers(f"user:{user_id}:chats")
        
        chats = []
        for chat_id in chat_ids:
            metadata = await self.redis.get_metadata(chat_id)
            if metadata:
                chats.append({
                    "chat_id": chat_id,
                    "chat_title": metadata.get('chat_title', 'Новый чат'),
                    "created_at": metadata.get('created_at'),
                    "message_count": int(metadata.get('message_count', 0))
                })
        
        chats.sort(key=lambda x: x['created_at'], reverse=True)
        return chats
    
    async def delete_chat(self, chat_id: str, user_id: Optional[str] = None) -> bool:
        if not await self.redis.check_chat(chat_id):
            return False
        
        media_ids = await self.redis.client.smembers(f"chat:{chat_id}:media")
        
        for media_id in media_ids:
            await self.llm.delete_media(media_id)
            await self.redis.client.delete(f"media:{media_id}")
        
        await self.redis.delete_chat(chat_id, user_id)
        
        logger.info(f"Deleted chat {chat_id} with {len(media_ids)} media files")
        return True
    
    async def add_media_to_chat(self, chat_id: str, file_path: str, filename: str) -> Dict:
        if not await self.redis.check_chat(chat_id):
            raise ValueError(f"Chat {chat_id} not found")
        
        media_id = str(uuid.uuid4())
        
        success = await self.llm.add_media(media_id, file_path, chat_id)
        
        if not success:
            raise RuntimeError("Failed to process media file")
        
        await self.redis.client.sadd(f"chat:{chat_id}:media", media_id)
        await self.redis.client.hset(f"media:{media_id}", mapping={
            "chat_id": chat_id,
            "filename": filename,
            "uploaded_at": datetime.now().isoformat(),
            "file_path": file_path
        })
        
        return {
            "media_id": media_id,
            "filename": filename,
            "chat_id": chat_id
        }