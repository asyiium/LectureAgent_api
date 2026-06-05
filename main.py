import logging
import uuid
import json

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from typing import List, Annotated, Dict

from schemas import *
from llm_service import LLMService
from redis_client import RedisClient

from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = LLMService()
redis = RedisClient()

async def lifespan(app: FastAPI):
    await redis.connect()
    logger.info('API startup ended')

    yield

    await redis.disconnect()
    logger.info('API closed')


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)



@app.post("/create_chat")
async def create_chat(request: CreateChatSchema):
    try:
        user_id = request.user_id if request.user_id else str(uuid.uuid4())
        chat_id = str(uuid.uuid4())
        
        chat_title = "New chat"
        # chat_title = await llm.generate_chat_title(request.first_message)
        
        await redis.client.sadd(f"user:{user_id}:chats", chat_id)
        await redis.create_chat(chat_id)
        await redis.set_chat_title(chat_id, chat_title)

        # await redis.add_message(chat_id, 'user', request.first_message)
        
        logger.info(f'Created chat {chat_id} with title: {chat_title}')
        
        return {
            'chat_id': chat_id,
            'user_id': user_id,
            'chat_title': chat_title,
            'message': 'Chat created successfully'
        }
    
    except Exception as e:
        logger.error(f'Error creating new chat: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error creating new chat: {str(e)}'
        )


@app.delete("/delete_chat/{chat_id}")
async def delete_chat(chat_id: str, user_id: str = None):
    if (not await redis.check_chat(chat_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Chat with id {chat_id} not found"
        )
    
    try:
        await redis.delete_chat(chat_id, user_id)
        logger.info(f'Deleted chat with id {chat_id}')
        return {"message" : "Chat with id {chat_id} deleted."}
    
    except Exception as e:
        logger.error(f'Error deleting chat with id {chat_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error deleting chat with id {chat_id}: {str(e)}"
        )

@app.post("/ask/{chat_id}")
async def ask_question(chat_id: str, question: QuestionCreateSchema):
    if (not await redis.check_chat(chat_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No chat with that id found'
        )

    try:
        history = await redis.get_history(chat_id)
        logger.info(f'Got history for chat {chat_id}')
        
        async def event_generator():
            given_answer = ""
            async for chunk in llm.get_answer(question.question_text, history):
                given_answer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            await redis.add_message(chat_id, 'user', question.question_text)
            await redis.add_message(chat_id, 'assistant', given_answer)
            
            logger.info(f'History {history}')
            
            new_title = None
            if len(history) <= 1:
                chat_title = await llm.generate_chat_title(question.question_text)
                await redis.set_chat_title(chat_id, chat_title)
                new_title = chat_title
                
            payload = {'type': 'done'}
            if new_title:
                payload['title'] = new_title
                
            yield f"data: {json.dumps(payload)}\n\n"
            
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f'Error generating answer: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error generating answer: {str(e)}"
        )

@app.get('/chat_list/{user_id}')
async def chat_list(user_id: str):
    chat_ids = await redis.client.smembers(f'user:{user_id}:chats')

    chat_list = []
    for chat_id in chat_ids:
        metadata = await redis.get_metadata(chat_id)
        if metadata:
            chat_list.append({
                "chat_id": chat_id,
                "created_at": metadata.get('created_at'),
                "chat_title": metadata.get('chat_title'),
                "message_count": int(metadata.get('message_count', 0))
            })
    
    chat_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {"chat_list": chat_list}

@app.get('/chat_history/{chat_id}')
async def chat_history(chat_id: str):
    if not await redis.check_chat(chat_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with id {chat_id} not found"
        )
    chat_history = await redis.get_history(chat_id)
    return {"chat_history": chat_history}


@app.post("/add_media")
async def add_media(media: MediaCreateSchema) -> Dict:
    try:
        media_id = str(uuid.uuid4())

        success = await llm.add_media(media_id, media.media_path)
        if (not success):
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error adding media"
        )  

        return {'media_id': media_id, 'status': 'added'}

    except Exception as e:
        logger.error(f'Error adding media: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error adding media: {str(e)}"
        ) 
    
@app.post("/delete_media/{media_id}")
async def delete_media(media_id: str):
    try:
        success = await llm.delete_media(media_id)

        if (not success):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error deleting media"
            )
        
        return {'media_id': media_id, 'status': 'deleted'}
          
    except Exception as e:
        logger.error(f'Error deleting media: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error deleting media: {str(e)}"
        )


# [TBD] @app.post('/edit_question/{question_id})
