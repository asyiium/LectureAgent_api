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
from chat_manager import ChatManager

from pathlib import Path
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = LLMService()
redis = RedisClient()
chat_manager = ChatManager(llm, redis)

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
        result = await chat_manager.create_chat(
            user_id=request.user_id,
            first_message=request.first_message
        )
        return result
    except Exception as e:
        logger.error(f'Error creating new chat: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error creating new chat: {str(e)}'
        )

@app.delete("/delete_chat/{chat_id}")
async def delete_chat(chat_id: str, user_id: str = None):
    try:
        success = await chat_manager.delete_chat(chat_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with id {chat_id} not found"
            )
        return {"message": f"Chat {chat_id} deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting chat: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting chat: {str(e)}"
        )

@app.post("/ask/{chat_id}")
async def ask_question(chat_id: str, question: QuestionCreateSchema):
    try:
        stream_generator = await chat_manager.send_message(
            chat_id=chat_id,
            message=question.question_text,
            stream=True
        )
        
        async def sse_generator():
            async for chunk in stream_generator:
                if chunk.startswith("[TITLE]") and chunk.endswith("[/TITLE]"):
                    title = chunk[7:-8]
                    yield f"data: {json.dumps({'type': 'title', 'content': title})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(sse_generator(), media_type="text/event-stream")
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Error generating answer: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )

@app.get('/chat_list/{user_id}')
async def chat_list(user_id: str):
    try:
        chats = await chat_manager.get_user_chats(user_id)
        return {"chat_list": chats}
    except Exception as e:
        logger.error(f'Error getting chat list: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting chat list: {str(e)}"
        )
    
@app.get('/chat_history/{chat_id}')
async def chat_history(chat_id: str):
    try:
        history = await chat_manager.get_chat_history(chat_id)
        return {"chat_history": history}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Error getting chat history: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting chat history: {str(e)}"
        )

@app.post("/add_media/{chat_id}")
async def add_media(chat_id: str, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    
    if ext not in ['.txt', '.md', '.docx', '.doc', '.pdf', '.pptx', '.ppt', '.mp3', '.ogg', '.wav']:
        raise HTTPException(400, f"Unsupported file type: {ext}")
    
    temp_dir = os.getenv('TEMP_DIR', '/tmp')
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, f'{uuid.uuid4()}{ext}')
    
    try:
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        result = await chat_manager.add_media_to_chat(
            chat_id=chat_id,
            file_path=file_path,
            filename=file.filename
        )
        
        return {
            "media_id": result["media_id"],
            "filename": result["filename"],
            "message": f"File uploaded and processed"
        }
        
    except ValueError as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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