"""Agent Service using OpenAI Agents SDK."""

import logging
import time
import httpx
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from util.logging_util import get_logger
from config.settings import settings

# Configure logging
logger = get_logger(__name__)


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
        # Use centralized settings instead of direct os.getenv()
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
        self.open_router_api_key = settings.openrouter_api_key
        
        logger.info(f"Initializing AgentService for '{agent_name}' (env: {settings.app_env})")
        logger.debug(f"Model: {self.model}")
        logger.debug(f"Base URL: {self.base_url}")
        logger.debug(f"System prompt length: {len(system_prompt)} characters")
        
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
            logger.debug(f"Agent instructions set with {len(self.system_prompt)} characters")
            
        except Exception as e:
            logger.error(f"Failed to setup agent: {str(e)}")
            logger.error(f"Agent name: {self.agent_name}")
            logger.error(f"Model: {self.model}")
            logger.error(f"Base URL: {self.base_url}")
            raise

    
    async def chat(self, user_prompt: str) -> str:
        """
        Send a chat message to the agent.
        
        Args:
            user_prompt: The user's message/prompt
            
        Returns:
            The agent's response as a string
        """
        start_time = time.time()
        
        logger.info(f"Starting LLM chat request for agent: {self.agent_name}")
        logger.debug(f"User prompt length: {len(user_prompt)} characters")
        logger.debug(f"User prompt preview: {user_prompt[:200]}{'...' if len(user_prompt) > 200 else ''}")
        
        try:
            logger.info("Calling Runner.run() to execute LLM request")
            llm_start_time = time.time()
            
            result = await Runner.run(self.agent, user_prompt)
            
            llm_end_time = time.time()
            llm_duration = llm_end_time - llm_start_time
            
            logger.info(f"LLM call completed successfully in {llm_duration:.2f} seconds")
            logger.debug(f"Response length: {len(result.final_output)} characters")
            logger.debug(f"Response preview: {result.final_output[:200]}{'...' if len(result.final_output) > 200 else ''}")
            
            # Log full response in debug mode for detailed tracing
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("=== FULL LLM RESPONSE ===")
                logger.debug(result.final_output)
                logger.debug("=== END LLM RESPONSE ===")
            
            total_duration = time.time() - start_time
            logger.info(f"Total chat request completed in {total_duration:.2f} seconds")
            
            return result.final_output
            
        except Exception as e:
            error_duration = time.time() - start_time
            logger.error(f"Error in LLM chat after {error_duration:.2f} seconds: {str(e)}")
            logger.error(f"Agent: {self.agent_name}")
            logger.error(f"Model: {self.model}")
            logger.error(f"User prompt length: {len(user_prompt)}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise
    
    def update_system_prompt(self, new_system_prompt: str):
        """
        Update the system prompt and reinitialize the agent.
        
        Args:
            new_system_prompt: The new system prompt to use
        """
        logger.info(f"Updating system prompt for agent: {self.agent_name}")
        logger.debug(f"Old prompt length: {len(self.system_prompt)} characters")
        logger.debug(f"New prompt length: {len(new_system_prompt)} characters")
        
        self.system_prompt = new_system_prompt
        self._setup_agent()
        logger.info("System prompt updated and agent reinitialized successfully")
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        logger.debug(f"Retrieved system prompt for agent: {self.agent_name}")
        return self.system_prompt

   