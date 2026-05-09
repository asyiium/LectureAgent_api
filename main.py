import logging

from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Annotated

from models import User, UserChat, UserQuestion, LLMAnswer
from schemas import *
from database import SessionLocal, engine, get_db
from llm_service import LLMService

from sqlalchemy.orm import Session

app = FastAPI()
llm = LLMService()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/create_chat")
async def create_chat(chat: ChatSchema, db: db_dependency):
    try:
        new_chat = UserChat(**chat.model_dump())
        db.add(new_chat)
        db.commit()

        db.refresh(new_chat)
        logger.info(f'Created chat, id: {new_chat.id}')

        return new_chat
    
    except Exception as e:
        db.rollback()

        logger.error(f'Error creating new chat: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error creating new chat: {str(e)}'
        )


@app.delete("/delete_chat/{chat_id}")
async def delete_chat(chat_id: int, db: db_dependency):
    found_chat = db.get(UserChat, chat_id)

    if (not found_chat):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Chat with id {chat_id} not found"
        )
    
    try:
        db.delete(found_chat)
        db.commit()

        logger.info(f'Deleted chat with id {chat_id}')
        return {"message" : "Chat with id {chat_id} deleted."}
    
    except Exception as e:
        db.rollback()
        logger.error(f'Error deleting chat with id {chat_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error deleting chat with id {chat_id}: {str(e)}"
        )

@app.post("/ask")
async def ask_question(question: QuestionSchema, db: db_dependency):
    # [TBD] check chat_id existence if we already deleted it

    new_question = UserQuestion(**question.model_dump())
    db.add(new_question)
    db.flush()
    
    try:
        given_answer = await llm.generate_answer(
            question.question_text,
            question.media_path,
            question.question_type
        )

        new_answer = LLMAnswer(
            new_question.id,
            given_answer
        )

        db.add(new_answer)
        db.commit()

        db.refresh(new_answer)
        logger.info(f'Generated answer for question with id {new_question.id}')

        return LLMAnswerSchema(
            new_answer.id,
            new_answer.question_id,
            new_answer.content
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f'Error generating answer for question with id {new_question.id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error generating answer for question with id {new_question.id}: {str(e)}"
        )

# [TBD] @app.post('/edit_question/{question_id})

# [TBD] @app.get('/chat_list/{user_id})