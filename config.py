import os
import logging
from typing import Optional # For Python < 3.10, use Optional[str] instead of str | None

# Configure a basic logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers: # Avoid adding multiple handlers if reloaded
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO) # Set default logging level

class Config:
    def __init__(self):
        logger.info("Initializing configuration and checking for API keys...")
        self.openai_api_key = self._get_api_key("OPENAI_API_KEY", "OpenAI")
        self.anthropic_api_key = self._get_api_key("ANTHROPIC_API_KEY", "Anthropic")
        self.google_api_key = self._get_api_key("GOOGLE_API_KEY", "Google Gemini")
        # You can add other configurations here

    def _get_api_key(self, env_var_name: str, provider_name: str) -> Optional[str]: # Using Optional[str] for broader compatibility
        key = os.getenv(env_var_name)
        if key:
            logger.info(f"Found API key for {provider_name} in environment variable {env_var_name}.")
            return key
        else:
            logger.warning(f"Environment variable {env_var_name} for {provider_name} not found.")
            try:
                key_input = input(f"Please enter your {provider_name} API key (or press Enter to skip): ").strip()
                if key_input:
                    logger.info(f"API key for {provider_name} provided via user input.")
                    return key_input
                else:
                    logger.warning(f"No API key provided for {provider_name}. Features requiring this provider may be limited or use mocks.")
                    return None
            except EOFError: # Handles non-interactive environments
                logger.warning(f"Could not read input for {provider_name} API key (EOFError). Assuming no key provided.")
                return None
            except Exception as e:
                logger.error(f"An error occurred while trying to get {provider_name} API key: {e}", exc_info=True)
                return None

# Global config instance, to be imported by other modules
app_config = Config()