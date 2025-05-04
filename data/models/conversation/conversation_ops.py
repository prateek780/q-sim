from datetime import datetime
from typing import Dict, List, Optional
from redis_om import NotFoundError

from data.models.conversation.conversation_model import (
    AgentExecutionStatus,
    AgentTurn,
    ChatLogMetadata,
    ChatMessage,
    HistoryItem,
    MessageRole,
)


def create_conversation_metadata(
     pk: str, user_id: Optional[str] = None, title: Optional[str] = None,
) -> ChatLogMetadata:
    """Creates a new conversation metadata entry."""
    convo = ChatLogMetadata(user_id=user_id, title=title, pk=pk, conversation_id=pk)
    convo.save()
    return convo


def get_conversation_metadata(conversation_id: str) -> Optional[ChatLogMetadata]:
    """Retrieves conversation metadata by its ID."""
    try:
        # .get() uses the primary key defined in the model
        return ChatLogMetadata.get(conversation_id)
    except NotFoundError:
        return None


def update_conversation_metadata(
    conversation_id: str,
    title: Optional[str] = None,
    last_updated: Optional[datetime] = None,
) -> Optional[ChatLogMetadata]:
    """Updates conversation metadata."""
    try:
        convo = ChatLogMetadata.get(conversation_id)
        if title is not None:
            convo.title = title
        convo.last_updated = last_updated or datetime.now()
        convo.save()
        return convo
    except NotFoundError:
        print(f"Metadata not found for update: {conversation_id}")
        return None


def list_conversations(
    user_id: Optional[str] = None, limit: int = 20, skip: int = 0
) -> List[ChatLogMetadata]:
    """Lists conversation metadata, optionally filtered by user_id, sorted by last_updated."""
    find_expr = None
    if user_id:
        find_expr = ChatLogMetadata.user_id == user_id

    query = (
        ChatLogMetadata.find(find_expr)
        if find_expr is not None
        else ChatLogMetadata.find()
    )
    results = query.sort_by("-last_updated").page(skip, limit)
    return results


def delete_conversation_metadata(conversation_id: str) -> bool:
    """Deletes only the conversation metadata entry."""
    # .delete uses the primary key
    deleted_count = ChatLogMetadata.delete(conversation_id)
    return deleted_count > 0


# --- Chat Messages ---
def add_chat_message(
    conversation_id: str, role: MessageRole, content: str
) -> Optional[ChatMessage]:
    """Adds a chat message to a conversation and updates metadata."""
    metadata = update_conversation_metadata(conversation_id)
    if not metadata:
        print(
            f"Warning: Conversation metadata not found for {conversation_id} when adding message."
        )
        raise ValueError("Failed to update conversation metadata.")

    message = ChatMessage(conversation_id=conversation_id, role=role, content=content)
    message.save()
    return message


def get_message(message_id: str) -> Optional[ChatMessage]:
    """Retrieves a specific chat message by its ID."""
    try:
        return ChatMessage.get(message_id)
    except NotFoundError:
        return None


def delete_message(message_id: str) -> bool:
    """Deletes a specific chat message."""
    deleted_count = ChatMessage.delete(message_id)
    return deleted_count > 0


# --- Agent Turns ---
def start_agent_turn(
    conversation_id: str, agent_id: str, task_id: Optional[str], agent_input: Dict
) -> Optional[AgentTurn]:
    """Logs the start of an agent turn and updates metadata."""
    metadata = update_conversation_metadata(conversation_id)
    if not metadata:
        print(
            f"Warning: Conversation metadata not found for {conversation_id} when starting agent turn."
        )
        raise ValueError("Failed to update conversation metadata in start_agent_turn.")

    turn = AgentTurn(
        conversation_id=conversation_id,
        agent_id=agent_id,
        task_id=task_id,
        agent_input=agent_input,
        status=AgentExecutionStatus.PENDING,
    )
    turn.save()
    return turn


def finish_agent_turn(
    turn_id: str,
    status: AgentExecutionStatus,
    agent_output: Optional[Dict] = None,
    error_message: Optional[str] = None,
) -> Optional[AgentTurn]:
    """Updates an agent turn with its final status, output, or error."""
    try:
        turn = AgentTurn.get(turn_id)
        turn.status = status
        turn.agent_output = agent_output
        turn.error_message = error_message
        turn.timestamp = datetime.now()  # Update timestamp to completion time
        turn.save()

        # Update conversation metadata timestamp
        update_conversation_metadata(turn.conversation_id, last_updated=turn.timestamp)

        return turn
    except NotFoundError:
        print(f"AgentTurn not found for update: {turn_id}")
        return None


def get_agent_turn(turn_id: str) -> Optional[AgentTurn]:
    """Retrieves a specific agent turn by its ID."""
    try:
        return AgentTurn.get(turn_id)
    except NotFoundError:
        return None


def delete_agent_turn(turn_id: str) -> bool:
    """Deletes a specific agent turn."""
    deleted_count = AgentTurn.delete(turn_id)
    return deleted_count > 0


# --- Combined History ---
def get_conversation_history(
    conversation_id: str, limit: int = 50, skip: int = 0
) -> List[HistoryItem]:
    """Retrieves messages and agent turns for a conversation, sorted by timestamp."""
    try:
        msg_query = ChatMessage.conversation_id == conversation_id
        turn_query = AgentTurn.conversation_id == conversation_id

        # Fetch all matching items first
        messages = ChatMessage.find(msg_query).all()
        agent_turns = AgentTurn.find(turn_query).all()

        # Combine and sort in Python
        history: List[HistoryItem] = sorted(
            messages + agent_turns, key=lambda item: item.timestamp
        )

        # Apply pagination after sorting
        start_index = skip
        end_index = skip + limit
        paginated_history = history[start_index:end_index]

        return paginated_history

    except Exception as e:
        print(f"Error retrieving conversation history for {conversation_id}: {e}")
        # Log error appropriately
        return []


# --- Full Conversation Deletion ---
def delete_full_conversation(conversation_id: str) -> bool:
    """Deletes metadata, all messages, and all agent turns for a conversation."""
    print(f"Attempting to delete full conversation: {conversation_id}")
    success = True  # Assume success initially

    # 1. Delete Messages
    msg_query = ChatMessage.conversation_id == conversation_id
    messages_to_delete = ChatMessage.find(msg_query).all()
    print(f"Found {len(messages_to_delete)} messages to delete.")
    pks_to_delete = [msg.pk for msg in messages_to_delete]
    if pks_to_delete:
        deleted_count = ChatMessage.delete(pks_to_delete)
        print(f"Deleted {deleted_count} messages.")
        if deleted_count != len(pks_to_delete):
            print("Warning: Mismatch in deleted message count.")
            # Handle potential partial deletion if needed
            success = False

    # 2. Delete Agent Turns
    turn_query = AgentTurn.conversation_id == conversation_id
    turns_to_delete = AgentTurn.find(turn_query).all()
    print(f"Found {len(turns_to_delete)} agent turns to delete.")
    pks_to_delete = [turn.pk for turn in turns_to_delete]
    if pks_to_delete:
        deleted_count = AgentTurn.delete(pks_to_delete)
        print(f"Deleted {deleted_count} agent turns.")
        if deleted_count != len(pks_to_delete):
            print("Warning: Mismatch in deleted agent turn count.")
            success = False

    # 3. Delete Metadata
    print(f"Deleting metadata for conversation: {conversation_id}")
    metadata_deleted = delete_conversation_metadata(conversation_id)
    if not metadata_deleted:
        # Check if it just wasn't found (which is okay if messages/turns were also missing)
        if get_conversation_metadata(conversation_id) is not None:
            print("Error: Failed to delete metadata, but it still exists.")
            success = False
        else:
            print("Metadata already deleted or never existed.")

    print(
        f"Deletion result for {conversation_id}: {'Success' if success else 'Failed/Partial'}"
    )
    return success
