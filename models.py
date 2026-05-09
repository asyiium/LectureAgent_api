
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, ForeignKey

from database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)

class UserQuestion(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))

    question_type = Column(Integer) # хочу сделать здесь states: image, audio, video
    quesiton_text = Column(String)
    media_path = Column(String) # we will just save path to mp4 or img

class UserChat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    

class LLMAnswer(Base):
    __tablename__ = 'llm_answers'

    id = Column(Integer, primary_key=True, index=True) 
    quesion_id = Column(Integer, ForeignKey('questions.id'))

    content = Column(String)