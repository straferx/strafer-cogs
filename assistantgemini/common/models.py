from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class GuildSettings(BaseModel):
    """Guild-specific settings for the assistant"""
    api_key: str = ""
    model: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 1000
    max_conversation_tokens: int = 4000
    system_prompt: str = "You are a helpful AI assistant."
    enabled: bool = False
    
    def get_user_model(self, member=None) -> str:
        """Get the model for a specific user (placeholder for future user-specific models)"""
        return self.model
    
    def get_user_max_response_tokens(self, member=None) -> Optional[int]:
        """Get max response tokens for a specific user"""
        return self.max_tokens


class Conversation(BaseModel):
    """Represents a conversation between a user and the assistant"""
    messages: List[Dict[str, str]] = Field(default_factory=list)
    token_count: int = 0
    message_count: int = 0


class Embedding(BaseModel):
    """Represents an embedding for memory search"""
    text: str
    embedding: List[float]
    metadata: Dict[str, str] = Field(default_factory=dict)


class EmbeddingEntryExists(Exception):
    """Raised when trying to create an embedding that already exists"""
    pass


class NoAPIKey(Exception):
    """Raised when no API key is configured"""
    pass


class DB(BaseModel):
    """Main database model for the assistant"""
    guilds: Dict[int, GuildSettings] = Field(default_factory=dict)
    conversations: Dict[str, Conversation] = Field(default_factory=dict)
    embeddings: Dict[str, Embedding] = Field(default_factory=dict)
    endpoint_override: Optional[str] = None 