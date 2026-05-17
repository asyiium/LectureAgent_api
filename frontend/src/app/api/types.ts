// Base response interface
export interface BaseResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  success: boolean;
}

export interface MessageSchema {
  role: string;
  content: string;
  timestamp: string;
}

export interface QuestionCreateSchema {
  question_text: string;
}

export interface LLMAnswerResponseSchema {
  answer: string;
  chat_id: string;
}

export interface MediaCreateSchema {
  media_path: string;
}

export interface ChatHistorySchema {
  chat_id: string;
  messages: MessageSchema[];
}

export interface ChatListItem {
  chat_id: string;
  created_at: string;
  message_count: number;
}

export interface ChatListResponse {
  chat_list: ChatListItem[];
}

export interface CreateChatResponse {
  chat_id: string;
  device_id: string;
  message: string;
}

export interface AddMediaResponse {
  media_id: string;
  status: string;
}

export interface DeleteMediaResponse {
  media_id: string;
  status: string;
}

export interface DeleteChatResponse {
  message: string;
}
