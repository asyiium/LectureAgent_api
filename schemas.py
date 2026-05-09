from pydantic import BaseModel
from enum import IntEnum


""" USER """

class UserCreateSchema(BaseModel):
    username: str
    password: str


class UserSchema(BaseModel):
    id: int
    username: str
    password: str

    class Config:
        from_attributes = True # db to pydantic conversion

""" QUESTION """

class QuestionType(IntEnum):
    AUDIO = 0
    IMAGE = 1
    TEXT = 2

class QuestionCreateSchema(BaseModel):
    user_id: int
    chat_id: int
    question_type: QuestionType
    question_text: str
    media_path: str

class QuestionSchema(BaseModel):
    id: int
    user_id: int
    chat_id: int
    question_type: QuestionType
    question_text: str
    media_path: str

    class Config:
        from_attributes = True # db to pydantic conversion


""" CHAT  """

class ChatCreateSchema(BaseModel):
    user_id: int

class ChatSchema(BaseModel):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True # db to pydantic conversion



""" LLM PART """

class LLMAnswerCreateSchema(BaseModel):
    question_id: int
    content: str


class LLMAnswerSchema(BaseModel):
    id: int
    quesion_id: int
    content: str
    
    class Config:
        from_attributes = True # db to pydantic conversion