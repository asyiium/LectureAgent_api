import {
  BaseResponse,
  MessageSchema,
  QuestionCreateSchema,
  LLMAnswerResponseSchema,
  MediaCreateSchema,
  ChatHistorySchema,
  ChatListItem,
  ChatListResponse,
  CreateChatResponse,
  AddMediaResponse,
  DeleteMediaResponse,
  DeleteChatResponse,
} from "./types";

const API_BASE_URL = "http://localhost:8000";
export async function createChat(
  user_id?: string,
): Promise<BaseResponse<CreateChatResponse>> {
  const url = user_id
    ? `${API_BASE_URL}/create_chat?user_id=${encodeURIComponent(user_id)}`
    : `${API_BASE_URL}/create_chat`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to create chat: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    data,
    success: true,
  };
}

export async function deleteChat(
  chat_id: string,
): Promise<BaseResponse<DeleteChatResponse>> {
  const response = await fetch(
    `${API_BASE_URL}/delete_chat/${encodeURIComponent(chat_id)}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to delete chat: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    data,
    success: true,
  };
}

export async function askQuestion(
  chat_id: string,
  question: QuestionCreateSchema,
): Promise<BaseResponse<LLMAnswerResponseSchema>> {
  const response = await fetch(
    `${API_BASE_URL}/ask/${encodeURIComponent(chat_id)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(question),
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to ask question: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    data,
    success: true,
  };
}

export async function getChatList(
  user_id: string,
): Promise<BaseResponse<ChatListResponse>> {
  const response = await fetch(
    `${API_BASE_URL}/chat_list/${encodeURIComponent(user_id)}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to get chat list: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    data,
    success: true,
  };
}

export async function addMedia(
  media: MediaCreateSchema,
): Promise<BaseResponse<AddMediaResponse>> {
  const response = await fetch(`${API_BASE_URL}/add_media`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(media),
  });

  if (!response.ok) {
    throw new Error(`Failed to add media: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    data,
    success: true,
  };
}

export async function deleteMedia(
  media_id: string,
): Promise<BaseResponse<DeleteMediaResponse>> {
  const response = await fetch(
    `${API_BASE_URL}/delete_media/${encodeURIComponent(media_id)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to delete media: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    data,
    success: true,
  };
}
