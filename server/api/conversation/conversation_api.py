from fastapi import APIRouter, HTTPException

from data.models.conversation.conversation_ops import get_conversation_history, get_conversation_metadata, list_conversations


conversation_router = APIRouter(
    prefix="/conversation",
    tags=["Agent", "Conversation"],
)

@conversation_router.get("/{conversation_id}/messages/")
async def get_conversation_messages(conversation_id: str):
    conversation = get_conversation_history(conversation_id, 500)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@conversation_router.get("/{conversation_id}/")
async def get_conversation(conversation_id: str):
    conversation_metadata = get_conversation_metadata(conversation_id)
    if conversation_metadata is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation_metadata

@conversation_router.get("/")
async def list_conversations_api():
    return list_conversations()
