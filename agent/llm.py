"""LLM client for Unagi using OpenAI-compatible API."""
import time
from typing import List, Dict, Optional
from openai import OpenAI
from config import get_settings


class LLMError(Exception):
    """Raised when LLM operations fail."""
    pass


class LLMClient:
    """OpenAI-compatible LLM client supporting multiple backends."""
    
    def __init__(self):
        """Initialize the LLM client with settings."""
        settings = get_settings()
        
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model_name
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """Send a chat completion request to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            The assistant's response text
            
        Raises:
            LLMError: If the request fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                
                if stream:
                    # For streaming, return the full response after collecting chunks
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                    return full_response
                else:
                    return response.choices[0].message.content
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Rate limit hit. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMError(
                            "Rate limit exceeded. Please wait a moment and try again."
                        )
                
                # Check if it's an authentication error
                if "auth" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
                    raise LLMError(
                        "Authentication failed. Please check your LLM_API_KEY in .env file.\n"
                        "Get your API key from: https://aistudio.google.com/app/apikey (for Gemini)"
                    )
                
                # For other errors, retry or raise
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise LLMError(f"LLM request failed: {error_msg}")
        
        raise LLMError("Max retries exceeded")
    
    def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7
    ) -> str:
        """Send a chat request with system prompt and conversation history.
        
        Args:
            system_prompt: System prompt defining agent behavior
            user_message: Current user message
            conversation_history: Previous messages in the conversation
            temperature: Sampling temperature
            
        Returns:
            The assistant's response text
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return self.chat(messages, temperature=temperature)
    
    def test_connection(self) -> bool:
        """Test if the LLM connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.chat(
                messages=[
                    {"role": "user", "content": "Hello! Please respond with just 'OK'."}
                ],
                temperature=0,
                max_tokens=10
            )
            return "ok" in response.lower()
        except Exception:
            return False


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client(reload: bool = False) -> LLMClient:
    """Get the global LLM client instance.
    
    Args:
        reload: If True, create a new client instance
        
    Returns:
        LLMClient instance
    """
    global _llm_client
    if _llm_client is None or reload:
        _llm_client = LLMClient()
    return _llm_client

# Made with Bob
