from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

""" MISC """
class MessageSchema(BaseModel):
    role: Literal["user", "assistant", "test"]
    content: str
    timestamp: datetime


""" QUESTION """

class QuestionCreateSchema(BaseModel):
    question_text: str
    

""" TEST """

class TestQuestionSchema(BaseModel):
    question_text: str
    options: List[str]
    explanation: str
    user_answer: Optional[int] = None

class TestSchema(BaseModel):
    test_id: str
    test_title: str
    questions: List[TestQuestionSchema]
    
class UpdateTestAnswerSchema(BaseModel):
    question_index: int
    user_answer: int
    

""" LLM """

class LLMAnswerResponseSchema(BaseModel):
    answer: str
    chat_id: str

""" MEDIA """

class MediaCreateSchema(BaseModel):
    media_path: str


""" CHAT  """

class ChatHistorySchema(BaseModel):
    chat_id: str
    messages: List[MessageSchema]

class CreateChatSchema(BaseModel):
    first_message: Optional[str] = None
    user_id: Optional[str] = None
