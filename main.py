import logging
import uuid
import json
import os
import datetime
import aiofiles

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from typing import List, Annotated, Dict

from schemas import *
from llm_service import LLMService
from redis_client import RedisClient

from pathlib import Path
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


@app.post("/add_media/{chat_id}")
async def add_media(chat_id: str, file: UploadFile = File(...)):
    if not await redis.check_chat(chat_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Chat with id {chat_id} not found'
        )
    
    ext = Path(file.filename).suffix.lower()

    if ext not in ['.txt', '.pdf', '.pptx', '.mp3', '.md']:
        raise HTTPException(400, f"Unsupported file type: {ext}")
    
    media_id = str(uuid.uuid4())
    temp_dir = os.getenv('TEMP_DIR', '/tmp')
    file_path = os.path.join(temp_dir, f'{media_id}{ext}')

    os.makedirs(temp_dir, exist_ok=True)

    try:
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        success = await llm.add_media(media_id, file_path, chat_id)
        
        if not success:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process media file"
            )
        
        await redis.client.sadd(f"chat:{chat_id}:media", media_id)
        await redis.client.hset(f"media:{media_id}", mapping={
            "chat_id": chat_id,
            "filename": file.filename,
            "file_size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "file_path": file_path
        })
        
        # os.remove(file_path)

        logger.info(f"Media {media_id} uploaded and linked to chat {chat_id}")
        
        return {
            "media_id": media_id,
            "filename": file.filename,
            "message": f"File {file.filename} uploaded and processed"
        }
        
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading media: {str(e)}"
        )

@app.delete("/delete_media/{chat_id}/{media_id}")
async def delete_media(chat_id: str, media_id: str):
    try:
        is_member = await redis.client.sismember(f"chat:{chat_id}:media", media_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found in chat {chat_id}"
            )
        
        success = await llm.delete_media(media_id)
        
        if success:
            await redis.client.srem(f"chat:{chat_id}:media", media_id)
            await redis.client.delete(f"media:{media_id}")
            
            logger.info(f"Media {media_id} deleted from chat {chat_id}")
            return {"status": "deleted", "media_id": media_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete media from vector database"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting media: {str(e)}"
        )