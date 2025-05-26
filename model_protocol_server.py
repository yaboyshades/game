"""
Model Protocol Server for Chronicle Weave

This module provides a standardized interface for agent communication with
various language model backends. It abstracts away the specifics of different
model providers and handles context management, caching, and error handling.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
import hashlib
import aiohttp
from datetime import datetime, timedelta
import google.generativeai as genai # For Gemini

# Import the centralized app_config for API keys
from config import app_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_protocol_server')

class ModelBackend(ABC):
    """Abstract base class for model backends"""
    
    @abstractmethod
    async def generate(self, 
                       prompt: str, 
                       params: Dict[str, Any], 
                       system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the model
        
        Args:
            prompt: The input prompt
            params: Generation parameters
            system_prompt: Optional system prompt or instruction
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def generate_with_json(self, 
                               prompt: str, 
                               json_schema: Dict[str, Any], 
                               params: Dict[str, Any],
                               system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a JSON response from the model
        
        Args:
            prompt: The input prompt
            json_schema: JSON schema for the expected response
            params: Generation parameters
            system_prompt: Optional system prompt or instruction
            
        Returns:
            Generated JSON response
        """
        pass

class OpenAIBackend(ModelBackend):
    """OpenAI API backend implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI backend
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (defaults to gpt-4)
        """
        self.api_key = api_key # API key is now passed in
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Using mock responses.")
        
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    async def generate(self, 
                       prompt: str, 
                       params: Dict[str, Any], 
                       system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from OpenAI
        Includes handling for an optional system prompt.
        
        Args:
            prompt: The input prompt
            params: Generation parameters
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            return self._mock_generate(prompt)
        
        # Set up the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set up parameters
        request_params = {
            "model": params.get("model", self.model),
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
            "top_p": params.get("top_p", 1.0),
            "frequency_penalty": params.get("frequency_penalty", 0.0),
            "presence_penalty": params.get("presence_penalty", 0.0)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=request_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return self._mock_generate(prompt)
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return self._mock_generate(prompt)
    
    async def generate_with_json(self, 
                               prompt: str, 
                               json_schema: Dict[str, Any], 
                               params: Dict[str, Any],
                               system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a JSON response from OpenAI
        
        Args:
            prompt: The input prompt
            json_schema: JSON schema for the expected response
            params: Generation parameters
            system_prompt: Optional system prompt or instruction
            
        Returns:
            Generated JSON response
        """
        if not self.api_key:
            return self._mock_generate_json(prompt, json_schema)
        
        # Set up the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set up parameters
        request_params = {
            "model": params.get("model", self.model),
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
            "top_p": params.get("top_p", 1.0),
            "frequency_penalty": params.get("frequency_penalty", 0.0),
            "presence_penalty": params.get("presence_penalty", 0.0),
            "response_format": {"type": "json_object"}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=request_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return self._mock_generate_json(prompt, json_schema)
                    
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return self._mock_generate_json(prompt, json_schema)
    
    def _mock_generate(self, prompt: str) -> str:
        """Generate a mock response for testing"""
        logger.info("Using mock response generator")
        
        if "attack" in prompt.lower():
            return "You swing your sword with precision, striking the goblin for 8 damage."
        elif "cast" in prompt.lower():
            return "You channel arcane energy, casting a powerful fireball that deals 15 damage to the enemies."
        elif "move" in prompt.lower():
            return "You move cautiously through the dungeon, finding yourself in a new chamber with flickering torches."
        elif "examine" in prompt.lower():
            return "You carefully examine your surroundings. The room is dusty with cobwebs in the corners. There's an old chest against the far wall and a wooden door to the north."
        elif "talk" in prompt.lower():
            return "The merchant smiles at you. 'Welcome traveler! I have many fine wares for sale. What catches your eye?'"
        else:
            return "The Dungeon Master considers your action carefully..."
    
    def _mock_generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock JSON response for testing"""
        logger.info("Using mock JSON response generator")
        
        if "intent" in prompt.lower():
            return {
                "success": True,
                "confidence": 0.9,
                "parsed_intent": {
                    "action": "attack" if "attack" in prompt.lower() else "examine",
                    "target_id": "monster_1" if "attack" in prompt.lower() else "location",
                    "target_name": "goblin" if "attack" in prompt.lower() else "room"
                }
            }
        elif "rule" in prompt.lower():
            return {
                "success": True,
                "narrative_summary": "You attack the goblin and hit for 8 damage.",
                "game_state_changes": {
                    "current_location": {
                        "monsters": [
                            {"id": "monster_1", "hp": 7, "max_hp": 15}
                        ]
                    }
                }
            }
        elif "narrative" in prompt.lower():
            return {
                "narrative": "You swing your sword with precision, striking the goblin for 8 damage. The creature howls in pain but remains standing, its red eyes fixed on you with malice."
            }
        elif "world" in prompt.lower():
            return {
                "success": True,
                "game_state_changes": {
                    "locations": {
                        "loc_2": {
                            "id": "loc_2",
                            "name": "Abandoned Library",
                            "description": "Dusty bookshelves line the walls of this forgotten library. Ancient tomes and scrolls are scattered across the floor."
                        }
                    }
                }
            }
        else:
            # Return a basic structure that matches the schema
            return {key: "mock value" for key in schema.get("properties", {}).keys()}

class AnthropicBackend(ModelBackend):
    """Anthropic API backend implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize Anthropic backend
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (defaults to claude-3-opus)
        """
        self.api_key = api_key # API key is now passed in
        if not self.api_key:
            logger.warning("No Anthropic API key provided. Using mock responses.")
        
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        
    async def generate(self, 
                       prompt: str, 
                       params: Dict[str, Any], 
                       system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from Anthropic
        Includes handling for an optional system prompt.
        
        Args:
            prompt: The input prompt
            params: Generation parameters
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            return self._mock_generate(prompt)
        
        # Set up the request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Set up parameters
        request_params = {
            "model": params.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": params.get("max_tokens", 1000),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 1.0),
        }
        if system_prompt:
            request_params["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=request_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Anthropic API error: {response.status} - {error_text}")
                        return self._mock_generate(prompt)
                    
                    result = await response.json()
                    return result["content"][0]["text"]
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            return self._mock_generate(prompt)
    
    async def generate_with_json(self, 
                               prompt: str, 
                               json_schema: Dict[str, Any], 
                               params: Dict[str, Any],
                               system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a JSON response from Anthropic
        
        Args:
            prompt: The input prompt
            json_schema: JSON schema for the expected response
            params: Generation parameters
            system_prompt: Optional system prompt or instruction
            
        Returns:
            Generated JSON response
        """
        if not self.api_key:
            return self._mock_generate_json(prompt, json_schema)
        
        # Set up the request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Add JSON schema to prompt
        schema_prompt = f"{prompt}\n\nRespond with a JSON object that follows this schema:\n{json.dumps(json_schema, indent=2)}"
        
        # Set up parameters
        request_params = {
            "model": params.get("model", self.model),
            "messages": [{"role": "user", "content": schema_prompt}],
            "max_tokens": params.get("max_tokens", 1000),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 1.0),
        }
        if system_prompt:
            request_params["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=request_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Anthropic API error: {response.status} - {error_text}")
                        return self._mock_generate_json(prompt, json_schema)
                    
                    result = await response.json()
                    content = result["content"][0]["text"]
                    
                    # Extract JSON from the response
                    try:
                        # Try to find JSON block in the response
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0].strip()
                        else:
                            # Just try to parse the whole thing
                            json_str = content
                        
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from Anthropic response: {content}")
                        return self._mock_generate_json(prompt, json_schema)
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            return self._mock_generate_json(prompt, json_schema)
    
    def _mock_generate(self, prompt: str) -> str:
        """Generate a mock response for testing"""
        logger.info("Using mock response generator")
        
        if "attack" in prompt.lower():
            return "You swing your sword with precision, striking the goblin for 8 damage."
        elif "cast" in prompt.lower():
            return "You channel arcane energy, casting a powerful fireball that deals 15 damage to the enemies."
        elif "move" in prompt.lower():
            return "You move cautiously through the dungeon, finding yourself in a new chamber with flickering torches."
        elif "examine" in prompt.lower():
            return "You carefully examine your surroundings. The room is dusty with cobwebs in the corners. There's an old chest against the far wall and a wooden door to the north."
        elif "talk" in prompt.lower():
            return "The merchant smiles at you. 'Welcome traveler! I have many fine wares for sale. What catches your eye?'"
        else:
            return "The Dungeon Master considers your action carefully..."
    
    def _mock_generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock JSON response for testing"""
        logger.info("Using mock JSON response generator")
        
        if "intent" in prompt.lower():
            return {
                "success": True,
                "confidence": 0.9,
                "parsed_intent": {
                    "action": "attack" if "attack" in prompt.lower() else "examine",
                    "target_id": "monster_1" if "attack" in prompt.lower() else "location",
                    "target_name": "goblin" if "attack" in prompt.lower() else "room"
                }
            }
        elif "rule" in prompt.lower():
            return {
                "success": True,
                "narrative_summary": "You attack the goblin and hit for 8 damage.",
                "game_state_changes": {
                    "current_location": {
                        "monsters": [
                            {"id": "monster_1", "hp": 7, "max_hp": 15}
                        ]
                    }
                }
            }
        elif "narrative" in prompt.lower():
            return {
                "narrative": "You swing your sword with precision, striking the goblin for 8 damage. The creature howls in pain but remains standing, its red eyes fixed on you with malice."
            }
        elif "world" in prompt.lower():
            return {
                "success": True,
                "game_state_changes": {
                    "locations": {
                        "loc_2": {
                            "id": "loc_2",
                            "name": "Abandoned Library",
                            "description": "Dusty bookshelves line the walls of this forgotten library. Ancient tomes and scrolls are scattered across the floor."
                        }
                    }
                }
            }
        else:
            # Return a basic structure that matches the schema
            return {key: "mock value" for key in schema.get("properties", {}).keys()}

class LocalModelBackend(ModelBackend):
    """Local model backend implementation (using a local API or library)"""
    
    def __init__(self, model_path: str = ""):
        """
        Initialize local model backend
        
        Args:
            model_path: Path to the local model
        """
        self.model_path = model_path
        logger.info(f"Initializing local model backend with path: {model_path}")
        logger.warning("Local model backend is using mock responses for now")
    
    async def generate(self, 
                       prompt: str, 
                       params: Dict[str, Any], 
                       system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from local model
        
        Args:
            prompt: The input prompt
            params: Generation parameters
            system_prompt: Optional system prompt (may be ignored by mock)
            
        Returns:
            Generated text response
        """
        # This is a placeholder for actual local model implementation
        # In a real implementation, this would use a library like transformers
        return self._mock_generate(prompt)
    
    async def generate_with_json(self, 
                               prompt: str, 
                               json_schema: Dict[str, Any], 
                               params: Dict[str, Any],
                               system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a JSON response from local model
        
        Args:
            prompt: The input prompt
            json_schema: JSON schema for the expected response
            params: Generation parameters
            system_prompt: Optional system prompt (may be ignored by mock)
            
        Returns:
            Generated JSON response
        """
        # This is a placeholder for actual local model implementation
        return self._mock_generate_json(prompt, json_schema)
    
    def _mock_generate(self, prompt: str) -> str:
        """Generate a mock response for testing"""
        logger.info("Using mock response generator")
        
        if "attack" in prompt.lower():
            return "You swing your sword with precision, striking the goblin for 8 damage."
        elif "cast" in prompt.lower():
            return "You channel arcane energy, casting a powerful fireball that deals 15 damage to the enemies."
        elif "move" in prompt.lower():
            return "You move cautiously through the dungeon, finding yourself in a new chamber with flickering torches."
        elif "examine" in prompt.lower():
            return "You carefully examine your surroundings. The room is dusty with cobwebs in the corners. There's an old chest against the far wall and a wooden door to the north."
        elif "talk" in prompt.lower():
            return "The merchant smiles at you. 'Welcome traveler! I have many fine wares for sale. What catches your eye?'"
        else:
            return "The Dungeon Master considers your action carefully..."
    
    def _mock_generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock JSON response for testing"""
        logger.info("Using mock JSON response generator")
        
        if "intent" in prompt.lower():
            return {
                "success": True,
                "confidence": 0.9,
                "parsed_intent": {
                    "action": "attack" if "attack" in prompt.lower() else "examine",
                    "target_id": "monster_1" if "attack" in prompt.lower() else "location",
                    "target_name": "goblin" if "attack" in prompt.lower() else "room"
                }
            }
        elif "rule" in prompt.lower():
            return {
                "success": True,
                "narrative_summary": "You attack the goblin and hit for 8 damage.",
                "game_state_changes": {
                    "current_location": {
                        "monsters": [
                            {"id": "monster_1", "hp": 7, "max_hp": 15}
                        ]
                    }
                }
            }
        elif "narrative" in prompt.lower():
            return {
                "narrative": "You swing your sword with precision, striking the goblin for 8 damage. The creature howls in pain but remains standing, its red eyes fixed on you with malice."
            }
        elif "world" in prompt.lower():
            return {
                "success": True,
                "game_state_changes": {
                    "locations": {
                        "loc_2": {
                            "id": "loc_2",
                            "name": "Abandoned Library",
                            "description": "Dusty bookshelves line the walls of this forgotten library. Ancient tomes and scrolls are scattered across the floor."
                        }
                    }
                }
            }
        else:
            # Return a basic structure that matches the schema
            return {key: "mock value" for key in schema.get("properties", {}).keys()}

class GeminiBackend(ModelBackend):
    """Google Gemini API backend implementation"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash-latest"):
        """
        Initialize Gemini backend

        Args:
            api_key: Google API key
            model: Model to use (e.g., "gemini-1.5-flash-latest", "gemini-pro")
        """
        self.api_key = api_key # API key is now passed in
        self.model_name = model
        self.client = None

        if not self.api_key:
            logger.warning("No Google API key provided for Gemini. Using mock responses.")
        else:
            try:
                genai.configure(api_key=self.api_key)
                # System instruction is handled differently for Gemini 1.5 models
                # It's a param to GenerativeModel, so we'll handle it in generate methods
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini client configured successfully for model {self.model_name}.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini client: {e}", exc_info=True)
                self.client = None # Ensure client is None if setup fails

    async def generate(self, 
                       prompt: str, 
                       params: Dict[str, Any], 
                       system_prompt: Optional[str] = None) -> str:
        if not self.client or not self.api_key: # Check if client initialized and key exists
            return self._mock_generate(prompt)

        generation_config = genai.types.GenerationConfig(
            candidate_count=params.get("candidate_count", 1),
            max_output_tokens=params.get("max_tokens", 1000),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 1.0)
        )
        
        # For Gemini 1.5 models, system_instruction is part of the model config
        # For older models, it's typically prepended or part of chat history.
        # This example assumes we might re-init or use a specific client if system_prompt changes often.
        # For simplicity, if system_prompt is provided and model is 1.5, we use it.
        model_to_use = self.client
        if system_prompt and ("1.5" in self.model_name or "gemini-pro" in self.model_name): # Gemini Pro also supports system instructions in chat
            # This is a simplified way; for frequent system_prompt changes, consider chat sessions
            # or re-initializing the model if it's a one-off with system_instruction.
            # For chat structure:
            # contents = []
            # if system_prompt: contents.append({'role': 'system', 'parts': [{'text': system_prompt}]})
            # contents.append({'role': 'user', 'parts': [{'text': prompt}]})
            # For gemini-1.5-*:
            if "1.5" in self.model_name:
                 model_to_use = genai.GenerativeModel(self.model_name, system_instruction=system_prompt)
            else: # gemini-pro (non-1.5)
                 prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:" # Basic prepend

        try:
            response = await model_to_use.generate_content_async(
                prompt, # Or `contents` if using chat structure
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
            return self._mock_generate(prompt)

    async def generate_with_json(self, 
                               prompt: str, 
                               json_schema: Dict[str, Any], 
                               params: Dict[str, Any],
                               system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.client or not self.api_key:
            return self._mock_generate_json(prompt, json_schema)

        # Instruct Gemini to respond in JSON format, including the schema
        # This is a common way to guide models for JSON output.
        json_prompt = (
            f"{prompt}\n\n"
            "Please provide your response strictly in JSON format. "
            "The JSON object must conform to the following schema:\n"
            f"{json.dumps(json_schema, indent=2)}"
        )

        generation_config_params = {
            "candidate_count": params.get("candidate_count", 1),
            "max_output_tokens": params.get("max_tokens", 2048), # JSON can be verbose
            "temperature": params.get("temperature", 0.5), # Lower temp for structured output
            "top_p": params.get("top_p", 1.0)
        }
        # For Gemini 1.5 models, we can specify response_mime_type
        if "1.5" in self.model_name:
            generation_config_params["response_mime_type"] = "application/json"
        
        generation_config = genai.types.GenerationConfig(**generation_config_params)

        model_to_use = self.client
        if system_prompt and ("1.5" in self.model_name or "gemini-pro" in self.model_name):
            if "1.5" in self.model_name:
                 model_to_use = genai.GenerativeModel(self.model_name, system_instruction=system_prompt)
            else: # gemini-pro (non-1.5)
                 json_prompt = f"{system_prompt}\n\nUser: {json_prompt}\nAssistant:"

        try:
            response = await model_to_use.generate_content_async(
                json_prompt,
                generation_config=generation_config
            )
            # Gemini (especially with response_mime_type) should return clean JSON.
            # If not, we might need to extract from ```json ... ``` blocks.
            raw_text = response.text
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif raw_text.startswith("```") and raw_text.endswith("```"): # Handle if only ``` not ```json
                raw_text = raw_text[3:-3].strip()
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {response.text[:500]}... Error: {e}", exc_info=True)
            return self._mock_generate_json(prompt, json_schema)
        except Exception as e:
            logger.error(f"Error calling Gemini API for JSON: {str(e)}", exc_info=True)
            return self._mock_generate_json(prompt, json_schema)

    def _mock_generate(self, prompt: str) -> str:
        logger.info("Using Gemini mock response generator")
        return f"Mock Gemini response for: {prompt}"

    def _mock_generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Using Gemini mock JSON response generator")
        return {key: f"mock gemini value for {key}" for key in schema.get("properties", {}).keys()}

class ResponseCache:
    """Cache for model responses to avoid redundant API calls"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize response cache
        
        Args:
            max_size: Maximum number of items in cache
            ttl: Time to live in seconds
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached item or None if not found
        """
        if key in self.cache:
            # Check if item has expired
            if time.time() - self.access_times[key]["created"] > self.ttl:
                # Remove expired item
                del self.cache[key]
                del self.access_times[key]
                return None
            
            # Update last access time
            self.access_times[key]["accessed"] = time.time()
            return self.cache[key]
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Check if cache is full
        if len(self.cache) >= self.max_size:
            # Remove least recently used item
            lru_key = min(self.access_times.items(), key=lambda x: x[1]["accessed"])[0]
            del self.cache[lru_key]
            del self.access_times[lru_key]
        
        # Add new item
        self.cache[key] = value
        self.access_times[key] = {
            "created": time.time(),
            "accessed": time.time()
        }
    
    def clear(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        self.access_times.clear()

class ModelProtocolServer:
    """
    Model Protocol Server for agent communication
    
    This class provides a standardized interface for agent communication with
    various language model backends. It handles context management, caching,
    and error handling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Model Protocol Server
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize backends
        self.backends = {}
        self._initialize_backends()
        
        # Initialize cache
        self.cache = ResponseCache(
            max_size=self.config.get("cache_max_size", 1000),
            ttl=self.config.get("cache_ttl", 3600)
        )
        
        # Initialize context store
        self.context_store = {}
    
    def _initialize_backends(self) -> None:
        """Initialize model backends based on configuration"""
        # Default backend configuration
        backend_configs = self.config.get("backends", {
            "openai": {
                "type": "openai",
                "api_key": app_config.openai_api_key, # Use app_config
                "model": "gpt-4"
            },
            "anthropic": {
                "type": "anthropic",
                "api_key": app_config.anthropic_api_key, # Use app_config
                "model": "claude-3-opus-20240229"
            },
            "gemini": {
                "type": "gemini",
                "api_key": app_config.google_api_key, # Use app_config
                "model": "gemini-1.5-flash-latest"
            },
            "local": {
                "type": "local",
                "model_path": self.config.get("local_model_path", "")
            }
        })

        # Initialize each backend
        for name, config in backend_configs.items():
            backend_type = config.get("type", "").lower()
            
            if backend_type == "openai":
                self.backends[name] = OpenAIBackend(
                    api_key=config.get("api_key"),
                    model=config.get("model", "gpt-4")
                )
            elif backend_type == "anthropic":
                self.backends[name] = AnthropicBackend(
                    api_key=config.get("api_key"),
                    model=config.get("model", "claude-3-opus-20240229")
                )
            elif backend_type == "gemini":
                self.backends[name] = GeminiBackend(
                    api_key=config.get("api_key"),
                    model=config.get("model", "gemini-1.5-flash-latest")
                )
            elif backend_type == "local":
                self.backends[name] = LocalModelBackend(
                    model_path=config.get("model_path", "")
                )
            else:
                logger.warning(f"Unknown backend type: {backend_type}")
        
        # Set default backend
        self.default_backend = self.config.get("default_backend", "openai")
        if self.default_backend not in self.backends:
            logger.warning(f"Default backend {self.default_backend} not found. Using first available backend.")
            self.default_backend = next(iter(self.backends.keys())) if self.backends else None
    
    def _get_backend(self, backend_name: Optional[str] = None) -> ModelBackend:
        """
        Get model backend by name
        
        Args:
            backend_name: Backend name
            
        Returns:
            Model backend
            
        Raises:
            ValueError: If backend not found
        """
        backend_name = backend_name or self.default_backend
        
        if not backend_name or backend_name not in self.backends:
            available_backends = ", ".join(self.backends.keys())
            raise ValueError(f"Backend '{backend_name}' not found. Available backends: {available_backends}")
        
        return self.backends[backend_name]
    
    def _get_cache_key(self, prompt: str, params: Dict[str, Any], backend_name: str) -> str:
        """
        Generate cache key for a request
        
        Args:
            prompt: Input prompt
            params: Generation parameters
            backend_name: Backend name
            
        Returns:
            Cache key
        """
        # Create a string representation of the request
        request_str = f"{backend_name}:{prompt}:{json.dumps(params, sort_keys=True)}"
        
        # Generate hash
        return hashlib.md5(request_str.encode()).hexdigest()
    
    async def generate(self, 
                     prompt: str, 
                     params: Optional[Dict[str, Any]] = None, 
                     backend_name: Optional[str] = None,
                     system_prompt: Optional[str] = None,
                     use_cache: bool = True) -> str:
        """
        Generate a response from a model
        
        Args:
            prompt: Input prompt
            params: Generation parameters
            backend_name: Backend to use
            system_prompt: Optional system prompt
            use_cache: Whether to use cache
            
        Returns:
            Generated text response
        """
        params = params or {}
        backend_name = backend_name or self.default_backend
        backend = self._get_backend(backend_name)
        
        # Check cache if enabled
        if use_cache:
            cache_key = self._get_cache_key(prompt, params, backend_name)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for key: {cache_key[:8]}...")
                return cached_response
        
        # Generate response
        response = await backend.generate(prompt, params, system_prompt)
        
        # Cache response if enabled
        if use_cache:
            cache_key = self._get_cache_key(prompt, params, backend_name)
            self.cache.set(cache_key, response)
        
        return response
    
    async def generate_with_json(self, 
                               prompt: str, 
                               json_schema: Dict[str, Any],
                               params: Optional[Dict[str, Any]] = None, 
                               backend_name: Optional[str] = None,
                               system_prompt: Optional[str] = None,
                               use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate a JSON response from a model
        
        Args:
            prompt: Input prompt
            json_schema: JSON schema for the expected response
            params: Generation parameters
            backend_name: Backend to use
            system_prompt: Optional system prompt
            use_cache: Whether to use cache
            
        Returns:
            Generated JSON response
        """
        params = params or {}
        backend_name = backend_name or self.default_backend
        backend = self._get_backend(backend_name)
        
        # Check cache if enabled
        if use_cache:
            cache_key = self._get_cache_key(prompt, params, backend_name) + ":json"
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for key: {cache_key[:8]}...")
                return cached_response
        
        # Generate response
        response = await backend.generate_with_json(prompt, json_schema, params, system_prompt)
        
        # Cache response if enabled
        if use_cache:
            cache_key = self._get_cache_key(prompt, params, backend_name) + ":json"
            self.cache.set(cache_key, response)
        
        return response
    
    def store_context(self, context_id: str, context_data: Dict[str, Any]) -> None:
        """
        Store context data for future use
        
        Args:
            context_id: Context identifier
            context_data: Context data to store
        """
        self.context_store[context_id] = {
            "data": context_data,
            "timestamp": datetime.now()
        }
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored context data
        
        Args:
            context_id: Context identifier
            
        Returns:
            Stored context data or None if not found
        """
        if context_id in self.context_store:
            return self.context_store[context_id]["data"]
        return None
    
    def clear_old_contexts(self, max_age_hours: int = 24) -> None:
        """
        Clear contexts older than specified age
        
        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Find old contexts
        old_contexts = [
            context_id for context_id, context in self.context_store.items()
            if context["timestamp"] < cutoff_time
        ]
        
        # Remove old contexts
        for context_id in old_contexts:
            del self.context_store[context_id]
        
        if old_contexts:
            logger.info(f"Cleared {len(old_contexts)} old contexts")
    
    def get_available_backends(self) -> List[str]:
        """
        Get list of available backends
        
        Returns:
            List of backend names
        """
        return list(self.backends.keys())
    
    def get_backend_info(self, backend_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a backend
        
        Args:
            backend_name: Backend name
            
        Returns:
            Backend information
        """
        backend_name = backend_name or self.default_backend
        backend = self._get_backend(backend_name)
        
        return {
            "name": backend_name,
            "type": backend.__class__.__name__,
            "model": getattr(backend, "model", "unknown")
        }
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        self.cache.clear()
        logger.info("Response cache cleared")

# Singleton instance
_instance = None

def get_model_server(config: Optional[Dict[str, Any]] = None) -> ModelProtocolServer:
    """
    Get or create the ModelProtocolServer singleton instance
    
    Args:
        config: Configuration dictionary (only used when creating new instance)
        
    Returns:
        ModelProtocolServer instance
    """
    global _instance
    
    if _instance is None:
        _instance = ModelProtocolServer(config)
    
    return _instance
