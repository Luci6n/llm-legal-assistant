# from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI

class LegalBasedModel:
    def __init__(self, model_name="gpt-4.1", agent_type="default", temperature=None, max_tokens=None, presence_penalty=None, frequency_penalty=None):
        """
        Initialize the legal assistant model with optimized parameters for different agent types.
        
        Args:
            model_name: The model to use (default: gpt-4.1)
            agent_type: Type of agent (research, summarization, prediction, supervisor, judge_research, judge_summarization, judge_prediction)
            temperature: Override default temperature for the agent type
            max_tokens: Override default max_tokens for the agent type
            presence_penalty: Override default presence_penalty for the agent type
            frequency_penalty: Override default frequency_penalty for the agent type
        """
        # Agent-specific parameter configurations
        agent_configs = {
            "research": {"temperature": 0.3, "max_tokens": 6000, "presence_penalty": 0.0, "frequency_penalty": 0.2},
            "summarization": {"temperature": 0.4, "max_tokens": 8000, "presence_penalty": 0.0, "frequency_penalty": 0.3},
            "prediction": {"temperature": 0.1, "max_tokens": 10000, "presence_penalty": 0.0, "frequency_penalty": 0.1},
            "supervisor": {"temperature": 0.0, "max_tokens": 300, "presence_penalty": 0.0, "frequency_penalty": 0.0},
            "judge_research": {"temperature": 0.0, "max_tokens": 500, "presence_penalty": 0.0, "frequency_penalty": 0.0},
            "judge_summarization": {"temperature": 0.0, "max_tokens": 500, "presence_penalty": 0.0, "frequency_penalty": 0.0},
            "judge_prediction": {"temperature": 0.0, "max_tokens": 500, "presence_penalty": 0.0, "frequency_penalty": 0.0},
            "default": {"temperature": 0.3, "max_tokens": 5000, "presence_penalty": 0.0, "frequency_penalty": 0.0}
        }
        
        # Get configuration for the specified agent type
        config = agent_configs.get(agent_type, agent_configs["default"])
        
        # Use provided parameters or fall back to agent-specific defaults
        final_temperature = temperature if temperature is not None else config["temperature"]
        final_max_tokens = max_tokens if max_tokens is not None else config["max_tokens"]
        final_presence_penalty = presence_penalty if presence_penalty is not None else config["presence_penalty"]
        final_frequency_penalty = frequency_penalty if frequency_penalty is not None else config["frequency_penalty"]
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=final_temperature,
            max_tokens=final_max_tokens,
            request_timeout=180,  # Increased from 60 to 180 seconds
            max_retries=5,        # Increased from 3 to 5 retries
            presence_penalty=final_presence_penalty,
            frequency_penalty=final_frequency_penalty
        )
    
    def get_model(self):
        """
        Get the initialized model instance.
        
        Returns:
            The initialized language model
        """
        return self.llm