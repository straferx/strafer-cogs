import logging
import typing as t
from typing import List, Optional, Dict, Any

import httpx
import google.generativeai as genai
from aiocache import cached
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

log = logging.getLogger("red.vrt.assistantgemini.calls")


@retry(
    retry=retry_if_exception_type(
        t.Union[
            httpx.TimeoutException,
            httpx.ReadTimeout,
            Exception,
        ]
    ),
    wait=wait_random_exponential(min=1, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def request_chat_completion_raw(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    api_key: str,
    max_tokens: Optional[int] = None,
    functions: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Make a request to the Gemini API for chat completion
    """
    try:
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Create the model
        gemini_model = genai.GenerativeModel(model)
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Gemini doesn't have system messages, prepend to user message
                continue
            elif msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg["content"]]})
        
        # Prepare generation config
        generation_config = {
            "temperature": temperature,
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        # Handle functions if supported
        tools = None
        if functions and model in ["gemini-1.5-pro", "gemini-2.0-pro", "gemini-2.5-flash", "gemini-2.5-pro"]:
            tools = []
            for func in functions:
                tool = {
                    "function_declarations": [{
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {})
                    }]
                }
                tools.append(tool)
        
        # Generate content
        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=generation_config,
            tools=tools if tools else None
        )
        
        # Convert response to OpenAI-like format
        result = {
            "id": "gemini_response",
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.text,
                    "function_call": None,
                    "tool_calls": None
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,  # Gemini doesn't provide token counts in free tier
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        
        # Handle function calls if present
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        result["choices"][0]["message"]["function_call"] = {
                            "name": part.function_call.name,
                            "arguments": part.function_call.args
                        }
        
        return result
        
    except Exception as e:
        log.error(f"Error calling Gemini API: {e}")
        raise


@retry(
    retry=retry_if_exception_type(
        t.Union[
            httpx.TimeoutException,
            httpx.ReadTimeout,
            Exception,
        ]
    ),
    wait=wait_random_exponential(min=1, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def request_embedding_raw(
    text: str,
    api_key: str,
    model: str = "embedding-001"
) -> List[float]:
    """
    Generate embeddings using Gemini (placeholder - Gemini doesn't have embedding models)
    For now, return a simple hash-based embedding
    """
    # Simple hash-based embedding for compatibility
    import hashlib
    hash_obj = hashlib.md5(text.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convert hex to list of floats
    embedding = []
    for i in range(0, len(hash_hex), 2):
        if i + 1 < len(hash_hex):
            val = int(hash_hex[i:i+2], 16) / 255.0
            embedding.append(val)
    
    # Pad to 1536 dimensions for compatibility
    while len(embedding) < 1536:
        embedding.append(0.0)
    
    return embedding[:1536]


async def count_tokens(text: str, model: str) -> int:
    """
    Count tokens in text (placeholder - Gemini doesn't provide token counting in free tier)
    """
    # Rough estimation: 1 token ≈ 4 characters
    return len(text) // 4 