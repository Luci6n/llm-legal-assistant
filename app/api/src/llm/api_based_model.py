from langchain.chat_models import init_chat_model

class LegalBasedModel:
    def __init__(self, model_name="openai:gpt-4o-mini", temperature=0.3, max_tokens=5000):
        """
        Initialize the legal assistant model with optimized parameters for legal tasks.
        
        Args:
            model_name: The model to use (default: gpt-4o-mini for cost efficiency)
            temperature: Lower temperature for more consistent legal advice (default: 0.3)
            max_tokens: Maximum tokens for comprehensive legal responses (default: 5000)
        """
        self.llm = init_chat_model(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=60,
            max_retries=3
        )
    
    def get_model(self):
        """
        Get the initialized model instance.
        
        Returns:
            The initialized language model
        """
        return self.llm