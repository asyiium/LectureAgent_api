from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

""" MISC """
class MessageSchema(BaseModel):
    role: str
    content: str
    timestamp: datetime


""" QUESTION """

class QuestionCreateSchema(BaseModel):
    question_text: str
    

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