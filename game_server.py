"""
Chronicle Weave - Game Server with Model Protocol Server integration

This module provides the FastAPI server for the Digital DM game.
"""
from typing import Dict, Any, List, Optional, Set
import logging
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from agents import SupervisorAgent, IntentAgent, RuleAgent, NarrativeAgent, WorldAgent
from models.game_models import GameState, PlayerCharacter, Location, Combat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("game_server.log")
    ]
)
logger = logging.getLogger('game_server')

class GameServer:
    """
    Main game server that handles WebSocket connections and game state.
    """
    
    def __init__(self):
        self.app = FastAPI()
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
        )
        
        # Modified to support multiple connections per user
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.game_state = GameState()
        
        # Initialize agents with required name parameters
        self.supervisor_agent = SupervisorAgent(name="supervisor")
        self.intent_agent = IntentAgent(name="intent")
        self.rule_agent = RuleAgent(name="rule")
        self.narrative_agent = NarrativeAgent(name="narrative")
        self.world_agent = WorldAgent(name="world")
        
        # Register agents with supervisor
        self.supervisor_agent.register_agent("intent", self.intent_agent)
        self.supervisor_agent.register_agent("rule", self.rule_agent)
        self.supervisor_agent.register_agent("narrative", self.narrative_agent)
        self.supervisor_agent.register_agent("world", self.world_agent)
        
        # Set up routes
        self.setup_routes()
        
        # Initialize starting location
        self.initialize_game_world()
    
    def setup_routes(self):
        """Set up API routes and WebSocket endpoint."""
        # Serve static files
        self.app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
        
        # Root route returns the chat interface
        @self.app.get("/", response_class=HTMLResponse)
        async def get_root():
            with open("frontend/index.html", "r") as f:
                return f.read()
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "ok"}
        
        # WebSocket endpoint for chat
        @self.app.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            await self.handle_websocket_connection(websocket, user_id)
    
    async def handle_websocket_connection(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket connection for a user."""
        logger.info(f"New WebSocket connection request from user: {user_id}")
        
        try:
            await websocket.accept()
            logger.info(f"WebSocket connection accepted for user: {user_id}")
            
            # Add connection to list of active connections for this user
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
            
            # Send connection confirmation
            await self.send_message_to_socket(websocket, {
                "type": "connection_status",
                "data": {
                    "status": "connected",
                    "message": "Connected to the game server!"
                }
            })
            
            # Check if player character exists
            player_character = self.get_player_character(user_id)
            
            if not player_character:
                # Create new player character
                player_character = self.create_new_player_character(user_id)
                await self.send_message_to_socket(websocket, {
                    "type": "system_message",
                    "data": {
                        "text": "Welcome to Chronicle Weave! You are about to embark on an adventure. What is your character's name?"
                    }
                })
            else:
                # Send welcome back message
                await self.send_message_to_socket(websocket, {
                    "type": "system_message",
                    "data": {
                        "text": f"Welcome back, {player_character.name}! Your adventure continues."
                    }
                })
                
                # Send current game state
                await self.send_game_state_to_socket(websocket, user_id)
            
            # Process messages
            while True:
                try:
                    data = await websocket.receive_text()
                    logger.info(f"Received message from user {user_id}: {data[:100]}...")
                    await self.process_message(user_id, data, websocket)
                except WebSocketDisconnect:
                    # Handle disconnection within the loop
                    logger.info(f"WebSocket disconnected for user: {user_id}")
                    if user_id in self.active_connections and websocket in self.active_connections[user_id]:
                        self.active_connections[user_id].remove(websocket)
                        # Clean up empty lists
                        if not self.active_connections[user_id]:
                            del self.active_connections[user_id]
                    # Break out of the receive loop on disconnect
                    break
                except Exception as e:
                    logger.error(f"Error processing message from user {user_id}: {str(e)}")
                    try:
                        await self.send_message_to_socket(websocket, {
                            "type": "system_message",
                            "data": {
                                "text": f"Error processing your message: {str(e)}"
                            }
                        })
                    except:
                        # If sending fails, socket is likely closed
                        logger.info(f"Failed to send error message, socket likely closed for user: {user_id}")
                        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
                            self.active_connections[user_id].remove(websocket)
                            # Clean up empty lists
                            if not self.active_connections[user_id]:
                                del self.active_connections[user_id]
                        # Break out of the receive loop if we can't send
                        break
                
        except WebSocketDisconnect:
            # Handle disconnection outside the loop (during setup)
            logger.info(f"WebSocket disconnected during setup for user: {user_id}")
            if user_id in self.active_connections and websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                # Clean up empty lists
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {str(e)}")
            if user_id in self.active_connections and websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                # Clean up empty lists
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
    
    async def process_message(self, user_id: str, message: str, websocket: WebSocket = None):
        """Process a message from a user."""
        try:
            # Parse message as JSON
            data = json.loads(message)
            message_type = data.get("type", "")
            
            if message_type == "message":
                # Process player input through agent system
                player_input = data.get("data", {}).get("text", "")
                
                # Get player character
                player_character = self.get_player_character(user_id)
                
                if not player_character:
                    # Create new player character if it doesn't exist
                    player_character = self.create_new_player_character(user_id)
                
                # Check if in character creation
                if not player_character.name:
                    # Handle character creation
                    await self.handle_character_creation(user_id, player_input, websocket)
                else:
                    # Process normal game input
                    await self.process_game_input(user_id, player_input, websocket)
            
        except json.JSONDecodeError:
            # Handle plain text input
            logger.warning(f"Received non-JSON message from user {user_id}: {message[:100]}...")
            await self.process_game_input(user_id, message, websocket)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if websocket:
                try:
                    await self.send_message_to_socket(websocket, {
                        "type": "system_message",
                        "data": {
                            "text": f"Error processing your message: {str(e)}"
                        }
                    })
                except:
                    logger.error(f"Failed to send error message to socket for user {user_id}")
            else:
                await self.send_message(user_id, {
                    "type": "system_message",
                    "data": {
                        "text": f"Error processing your message: {str(e)}"
                    }
                })
    
    async def handle_character_creation(self, user_id: str, player_input: str, websocket: WebSocket = None):
        """Handle character creation process."""
        player_character = self.get_player_character(user_id)
        
        if not player_character.name:
            # Set character name
            player_character.name = player_input
            
            # Ask for race
            message = {
                "type": "system_message",
                "data": {
                    "text": f"Welcome, {player_character.name}! What race are you? (Human, Elf, Dwarf, Halfling)"
                }
            }
            if websocket:
                await self.send_message_to_socket(websocket, message)
            else:
                await self.send_message(user_id, message)
        elif not player_character.race:
            # Set character race
            player_character.race = player_input
            
            # Ask for class
            message = {
                "type": "system_message",
                "data": {
                    "text": f"A {player_character.race}, excellent! What class are you? (Fighter, Wizard, Rogue, Cleric)"
                }
            }
            if websocket:
                await self.send_message_to_socket(websocket, message)
            else:
                await self.send_message(user_id, message)
        elif not player_character.class_name:
            # Set character class
            player_character.class_name = player_input
            
            # Finalize character creation
            self.finalize_character_creation(player_character)
            
            # Send welcome message
            message = {
                "type": "system_message",
                "data": {
                    "text": f"Character creation complete! You are {player_character.name}, a {player_character.race} {player_character.class_name}. Your adventure begins in the town of Eigengrau."
                }
            }
            if websocket:
                await self.send_message_to_socket(websocket, message)
            else:
                await self.send_message(user_id, message)
            
            # Send initial game state
            if websocket:
                await self.send_game_state_to_socket(websocket, user_id)
            else:
                await self.send_game_state(user_id)
            
            # Send initial location description
            current_location = self.get_location(player_character.current_location_id)
            if current_location:
                message = {
                    "type": "narrative",
                    "data": {
                        "text": f"You find yourself in {current_location.name}.\n\n{current_location.description}"
                    }
                }
                if websocket:
                    await self.send_message_to_socket(websocket, message)
                else:
                    await self.send_message(user_id, message)
    
    def finalize_character_creation(self, player_character: PlayerCharacter):
        """Finalize character creation with default values based on class."""
        # Set default stats based on class
        if player_character.class_name.lower() == "fighter":
            player_character.strength = 16
            player_character.constitution = 14
            player_character.dexterity = 12
            player_character.wisdom = 10
            player_character.intelligence = 8
            player_character.charisma = 10
            player_character.hp = 12
            player_character.max_hp = 12
            player_character.ac = 16  # Chain mail and shield
        elif player_character.class_name.lower() == "wizard":
            player_character.strength = 8
            player_character.constitution = 12
            player_character.dexterity = 14
            player_character.wisdom = 10
            player_character.intelligence = 16
            player_character.charisma = 10
            player_character.hp = 8
            player_character.max_hp = 8
            player_character.ac = 12  # Mage armor
            
            # Add basic spells
            player_character.known_spells = [
                {
                    "id": "spell_magic_missile",
                    "name": "Magic Missile",
                    "level": 1,
                    "type": "damage",
                    "damage_dice": "3d4+3"
                },
                {
                    "id": "spell_shield",
                    "name": "Shield",
                    "level": 1,
                    "type": "defense"
                }
            ]
            
            # Add spell slots
            player_character.spell_slots = {
                "1": 2  # 2 first-level spell slots
            }
        elif player_character.class_name.lower() == "rogue":
            player_character.strength = 10
            player_character.constitution = 12
            player_character.dexterity = 16
            player_character.wisdom = 10
            player_character.intelligence = 14
            player_character.charisma = 8
            player_character.hp = 10
            player_character.max_hp = 10
            player_character.ac = 14  # Leather armor
        elif player_character.class_name.lower() == "cleric":
            player_character.strength = 14
            player_character.constitution = 12
            player_character.dexterity = 8
            player_character.wisdom = 16
            player_character.intelligence = 10
            player_character.charisma = 10
            player_character.hp = 10
            player_character.max_hp = 10
            player_character.ac = 18  # Chain mail and shield
            
            # Add basic spells
            player_character.known_spells = [
                {
                    "id": "spell_cure_wounds",
                    "name": "Cure Wounds",
                    "level": 1,
                    "type": "healing",
                    "healing_dice": "1d8+3"
                },
                {
                    "id": "spell_guiding_bolt",
                    "name": "Guiding Bolt",
                    "level": 1,
                    "type": "damage",
                    "damage_dice": "4d6"
                }
            ]
            
            # Add spell slots
            player_character.spell_slots = {
                "1": 2  # 2 first-level spell slots
            }
        
        # Add starting location
        player_character.current_location_id = "town_square"
        
        # Update game state
        self.game_state.player_characters[player_character.id] = player_character
    
    async def process_game_input(self, user_id: str, player_input: str, websocket: WebSocket = None):
        """Process game input through the agent system."""
        # Get player character
        player_character = self.get_player_character(user_id)
        
        if not player_character:
            # Create new player character if it doesn't exist
            player_character = self.create_new_player_character(user_id)
            await self.handle_character_creation(user_id, player_input, websocket)
            return
        
        # Convert game state to dictionary for agents
        game_state_dict = self.get_game_state_dict(player_character)
        
        # Process through supervisor agent
        result = await self.supervisor_agent.process({
            "player_input": player_input,
            "user_id": user_id,
            "game_state": game_state_dict
        })
        
        # Update game state based on agent response
        if "game_state_update" in result:
            self.update_game_state(player_character, result["game_state_update"])
        
        # Send response to user
        if "message" in result:
            message = {
                "type": result.get("response_type", "narrative"),
                "data": {
                    "text": result["message"]
                }
            }
            if websocket:
                await self.send_message_to_socket(websocket, message)
            else:
                await self.send_message(user_id, message)
        
        # Send updated game state
        if websocket:
            await self.send_game_state_to_socket(websocket, user_id)
        else:
            await self.send_game_state(user_id)
    
    def get_game_state_dict(self, player_character: PlayerCharacter) -> Dict[str, Any]:
        """Convert game state to dictionary for agents."""
        # Get current location
        current_location = self.get_location(player_character.current_location_id)
        current_location_dict = current_location.to_dict() if current_location else {}
        
        # Get active combat
        active_combat = None
        if player_character.active_combat_id:
            active_combat = self.game_state.active_combats.get(player_character.active_combat_id)
        active_combat_dict = active_combat.to_dict() if active_combat else None
        
        # Build game state dictionary
        return {
            "player_character": player_character.to_dict(),
            "current_location": current_location_dict,
            "active_combat": active_combat_dict,
            "locations": {loc_id: loc.to_dict() for loc_id, loc in self.game_state.locations.items()}
        }
    
    def update_game_state(self, player_character: PlayerCharacter, updates: Dict[str, Any]):
        """Update game state based on agent response."""
        # Update player character
        if "player_character" in updates:
            pc_updates = updates["player_character"]
            for key, value in pc_updates.items():
                if hasattr(player_character, key):
                    setattr(player_character, key, value)
        
        # Update current location
        if "current_location" in updates:
            current_location = self.get_location(player_character.current_location_id)
            if current_location:
                loc_updates = updates["current_location"]
                for key, value in loc_updates.items():
                    if hasattr(current_location, key):
                        setattr(current_location, key, value)
        
        # Update combat state
        if "in_combat" in updates:
            if updates["in_combat"] and "combat" in updates:
                # Create or update combat
                combat_data = updates["combat"]
                combat_id = combat_data.get("id", f"combat_{player_character.current_location_id}")
                
                if combat_id in self.game_state.active_combats:
                    combat = self.game_state.active_combats[combat_id]
                    for key, value in combat_data.items():
                        if hasattr(combat, key):
                            setattr(combat, key, value)
                else:
                    combat = Combat(
                        id=combat_id,
                        location_id=player_character.current_location_id,
                        round=combat_data.get("round", 1),
                        current_turn=combat_data.get("current_turn", player_character.id),
                        initiative_order=combat_data.get("initiative_order", [])
                    )
                    self.game_state.active_combats[combat_id] = combat
                
                player_character.active_combat_id = combat_id
            elif not updates["in_combat"]:
                # End combat
                if player_character.active_combat_id:
                    self.game_state.active_combats.pop(player_character.active_combat_id, None)
                    player_character.active_combat_id = None
    
    async def send_message_to_socket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {str(e)}")
            # Don't attempt to remove from connections here - let the main loop handle it
            # Just re-raise to be caught by the caller
            raise
    
    async def send_message(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a user."""
        if user_id in self.active_connections:
            disconnected_sockets = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    disconnected_sockets.append(websocket)
            
            # Clean up disconnected sockets
            for websocket in disconnected_sockets:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_game_state_to_socket(self, websocket: WebSocket, user_id: str):
        """Send current game state to a specific WebSocket."""
        player_character = self.get_player_character(user_id)
        if not player_character:
            return
        
        # Get current location
        current_location = self.get_location(player_character.current_location_id)
        
        # Get active combat
        active_combat = None
        if player_character.active_combat_id:
            active_combat = self.game_state.active_combats.get(player_character.active_combat_id)
        
        # Build game state for client
        game_state = {
            "player_character": player_character.to_dict(),
            "current_location": current_location.to_dict() if current_location else {},
            "in_combat": bool(player_character.active_combat_id),
            "combat": active_combat.to_dict() if active_combat else None
        }
        
        # Send game state
        try:
            await self.send_message_to_socket(websocket, {
                "type": "game_state",
                "data": game_state
            })
        except Exception as e:
            logger.error(f"Failed to send game state to socket: {str(e)}")
            # Let the main loop handle disconnection
    
    async def send_game_state(self, user_id: str):
        """Send current game state to all connections for a user."""
        player_character = self.get_player_character(user_id)
        if not player_character:
            return
        
        # Get current location
        current_location = self.get_location(player_character.current_location_id)
        
        # Get active combat
        active_combat = None
        if player_character.active_combat_id:
            active_combat = self.game_state.active_combats.get(player_character.active_combat_id)
        
        # Build game state for client
        game_state = {
            "player_character": player_character.to_dict(),
            "current_location": current_location.to_dict() if current_location else {},
            "in_combat": bool(player_character.active_combat_id),
            "combat": active_combat.to_dict() if active_combat else None
        }
        
        # Send game state
        await self.send_message(user_id, {
            "type": "game_state",
            "data": game_state
        })
    
    def get_player_character(self, user_id: str) -> Optional[PlayerCharacter]:
        """Get player character for a user."""
        return self.game_state.player_characters.get(user_id)
    
    def create_new_player_character(self, user_id: str) -> PlayerCharacter:
        """Create a new player character for a user."""
        player_character = PlayerCharacter(
            id=user_id,
            name="",
            race="",
            class_name="",
            level=1,
            hp=10,
            max_hp=10,
            ac=10,
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            inventory=[],
            current_location_id="town_square"
        )
        
        self.game_state.player_characters[user_id] = player_character
        return player_character
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """Get location by ID."""
        return self.game_state.locations.get(location_id)
    
    def initialize_game_world(self):
        """Initialize the game world with starting locations."""
        # Create town square
        town_square = Location(
            id="town_square",
            name="Town Square",
            description="You stand in the center of a bustling town square. Merchants hawk their wares, and townsfolk go about their daily business. The town seems peaceful, but rumors of trouble in the nearby forest have been circulating.",
            exits={
                "north": "tavern",
                "east": "market",
                "south": "town_gate",
                "west": "blacksmith"
            },
            npcs=[
                {
                    "id": "mayor",
                    "name": "Mayor Thornton",
                    "description": "A portly man with a friendly smile and a well-groomed mustache."
                }
            ],
            items=[]
        )
        
        # Create tavern
        tavern = Location(
            id="tavern",
            name="The Prancing Pony",
            description="A warm, inviting tavern filled with the sounds of laughter and music. The air is thick with the smell of ale and roasted meat.",
            exits={
                "south": "town_square",
                "up": "tavern_rooms"
            },
            npcs=[
                {
                    "id": "bartender",
                    "name": "Giles the Bartender",
                    "description": "A burly man with a thick beard and a quick laugh."
                },
                {
                    "id": "bard",
                    "name": "Melody the Bard",
                    "description": "A slender elf with a beautiful voice and a mischievous smile."
                }
            ],
            items=[]
        )
        
        # Create market
        market = Location(
            id="market",
            name="Market District",
            description="A bustling market filled with stalls selling everything from fresh produce to exotic trinkets.",
            exits={
                "west": "town_square",
                "north": "general_store",
                "east": "alchemist"
            },
            npcs=[
                {
                    "id": "merchant",
                    "name": "Trader Johan",
                    "description": "A shrewd-looking man with a keen eye for valuable goods."
                }
            ],
            items=[]
        )
        
        # Create town gate
        town_gate = Location(
            id="town_gate",
            name="Town Gate",
            description="The main gate leading out of town. Guards stand watch, keeping an eye out for trouble.",
            exits={
                "north": "town_square",
                "south": "forest_path"
            },
            npcs=[
                {
                    "id": "guard",
                    "name": "Guard Captain Harlow",
                    "description": "A stern-looking woman with a weathered face and sharp eyes."
                }
            ],
            items=[]
        )
        
        # Create blacksmith
        blacksmith = Location(
            id="blacksmith",
            name="Blacksmith's Forge",
            description="The heat from the forge is intense. The rhythmic sound of hammer on anvil fills the air.",
            exits={
                "east": "town_square"
            },
            npcs=[
                {
                    "id": "blacksmith",
                    "name": "Grimhammer the Blacksmith",
                    "description": "A dwarf with massive arms and a beard singed from the forge."
                }
            ],
            items=[
                {
                    "id": "sword",
                    "name": "Steel Sword",
                    "description": "A well-crafted steel sword.",
                    "value": 15
                }
            ]
        )
        
        # Add locations to game state
        self.game_state.locations = {
            "town_square": town_square,
            "tavern": tavern,
            "market": market,
            "town_gate": town_gate,
            "blacksmith": blacksmith
        }

# Create game server instance
game_server = GameServer()

# Get FastAPI app
app = game_server.app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
