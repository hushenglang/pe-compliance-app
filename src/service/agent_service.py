"""Agent Service using OpenAI Agents SDK."""

import logging
import os
import httpx
from openai import OpenAI, AsyncOpenAI
from typing import Optional
from agents import Agent, Runner, OpenAIChatCompletionsModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentService:
    """Service for handling AI agent interactions using OpenAI Agents SDK with OpenRouter."""
    
    def __init__(self, agent_name: str, system_prompt: str):
        """
        Initialize the AgentService.
        Args:
            agent_name: The name of the agent
            system_prompt: The pre-defined system prompt for the agent
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.model = os.getenv("OPENROUTER_MODEL")
        self.base_url = os.getenv("OPENROUTER_BASE_URL")
        self.open_router_api_key = os.getenv("OPENROUTER_API_KEY")
        # Configure the agent
        self._setup_agent()
        
    
    def _setup_agent(self):
        """Setup the agent with OpenRouter configuration."""
        try:
            http_client = httpx.AsyncClient(verify=False)
            open_router_client = AsyncOpenAI(base_url=self.base_url, api_key=self.open_router_api_key, http_client=http_client)
            openAIModel = OpenAIChatCompletionsModel(model=self.model, openai_client=open_router_client)
            self.agent = Agent(name=self.agent_name, instructions=self.system_prompt, model=openAIModel)    
            logger.info(f"Agent service initialized successfully for {self.agent_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup agent: {str(e)}")
            raise

    
    async def chat(self, user_prompt: str) -> str:
        """
        Send a chat message to the agent.
        
        Args:
            user_prompt: The user's message/prompt
            
        Returns:
            The agent's response as a string
        """
        try:
          result = await Runner.run(self.agent, user_prompt)
          return result.final_output
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise
    
    def update_system_prompt(self, new_system_prompt: str):
        """
        Update the system prompt and reinitialize the agent.
        
        Args:
            new_system_prompt: The new system prompt to use
        """
        self.system_prompt = new_system_prompt
        self._setup_agent()
        logger.info("System prompt updated and agent reinitialized")
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        return self.system_prompt

   