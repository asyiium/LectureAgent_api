import os
import logging
import json

import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client = None
        self.session_ttl = int(os.getenv('REDIS_SESSION_TTL', 3600)) # [!] поставила один час (3600 сек), но можно поменять для теста
        
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = os.getenv('REDIS_PORT', 6379)
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
    
    async def connect(self):
        self.client = await redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password,
            decode_responses=True
        )
        await self.client.ping()
        logger.info(' Client connected')
    
    async def disconnect(self):
        if (self.client):
            await self.client.close()
            logger.info(' Client closed')

    async def create_chat(self, chat_id: str):
        metadata_key = f"chat:{chat_id}:metadata"
        
        metadata = {
            'chat_id' : chat_id,
            'created_at' : datetime.datetime.now().isoformat(),
            'message_count' : 0
        }

        await self.client.hset(metadata_key, mapping=metadata)
        await self.client.expire(metadata_key, self.session_ttl)
        
        history_key = f"chat:{chat_id}:history"
        
        await self.client.rpush(history_key, json.dumps({
            'role' : 'rds_client',
            'content' : 'Chat startup message',
            'timestamp' : datetime.datetime.now().isoformat()
        }))
        await self.client.expire(history_key, self.session_ttl)

        logger.info(f'Chat {chat_id} created')

    async def check_chat(self, chat_id: str):
        metadata_key = f"chat:{chat_id}:metadata"
        return await self.client.exists(metadata_key) > 0

    async def delete_chat(self, chat_id: str, user_id: str = None):
        history_key = f"chat:{chat_id}:history"
        metadata_key = f"chat:{chat_id}:metadata"
        await self.client.delete(metadata_key, history_key)
        
        if user_id:
            await self.client.srem(f"user:{user_id}:chats", chat_id)
        
        logger.info(f'Chat {chat_id} deleted')


    async def add_message(self, chat_id: str, role: str, content: str):
        history_key = f"chat:{chat_id}:history"

        message = json.dumps({
            'role' : role,
            'content' : content,
            'timestamp' : datetime.datetime.now().isoformat()
        })

        await self.client.rpush(history_key, message)
        await self.client.expire(history_key, self.session_ttl)

        metadata_key = f"chat:{chat_id}:metadata"
        await self.client.hincrby(metadata_key, 'message_count', 1)
        await self.client.expire(metadata_key, self.session_ttl)
        
        logger.info(f' Message to {chat_id} added')

    async def get_history(self, chat_id: str, max_messages: int = 50):
        messages = await self.client.lrange(f"chat:{chat_id}:history", -max_messages, -1)
        history = []
        for message in messages:
            history.append(json.loads(message))
        return history
    
    async def clear_history(self, chat_id: str):
        history_key = f"chat:{chat_id}:history"
        await self.client.delete(history_key)

        await self.client.rpush(history_key, json.dumps({
            'role' : 'rds_client',
            'content' : 'Chat startup message',
            'timestamp' : datetime.datetime.now().isoformat()
        }))
        await self.client.expire(history_key, self.session_ttl)

        metadata_key = f'chat:{chat_id}:metadata'
        await self.client.hset(metadata_key, 'message_count', 0)

        logger.info(f' Chat {chat_id} cleared')

    async def list_all_chats(self):
        mask = 'chat:*:metadata'
        keys = await self.client.keys(mask)
        return [key.split(':')[1] for key in keys]

    async def get_metadata(self, chat_id: str):
        metadata_key = f'chat:{chat_id}:metadata'
        return await self.client.hgetall(metadata_key)
    
    async def set_chat_title(self, chat_id: str, chat_title: str):
        await self.client.hset(f"chat:{chat_id}:metadata", "chat_title", chat_title)
        logger.info(f'Set title for chat {chat_id}: {chat_title}')
    
    async def get_chat_title(self, chat_id: str):
        title = await self.client.hget(f"chat:{chat_id}:metadata", "chat_title")
        if not title:
            return "Новый чат"
        return title.decode('utf-8') if isinstance(title, bytes) else title
    
    async def update_chat_list_with_title(self, user_id: str, chat_id: str, chat_title: str):
        await self.client.hset(f"user:{user_id}:chat:{chat_id}", "chat_title", chat_title)
