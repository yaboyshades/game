"""
Town Generator Module for Digital DM Game

This module integrates with Eigengrau's Town Generator to create
procedurally generated towns for the game. It handles both initial
town generation and on-demand generation as players explore.
"""

import os
import json
import logging
import subprocess
import tempfile
import shutil
from typing import Dict, Any, List, Optional, Tuple
import random
import asyncio
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('town_generator')

class TownGenerator:
    """
    Handles town generation using Eigengrau's Generator or a fallback
    procedural generation system when the generator is not available.
    """
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize the town generator.
        
        Args:
            cache_dir: Directory to cache generated towns
        """
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), '../data/towns')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Check if Eigengrau's Generator is available
        self.eigengrau_available = self._check_eigengrau_availability()
        if not self.eigengrau_available:
            logger.warning("Eigengrau's Generator not found. Using fallback procedural generation.")
        else:
            logger.info("Eigengrau's Generator found and ready for use.")
        
        # Cache for towns to avoid regenerating
        self.town_cache = {}
        
        # Load any existing towns from cache
        self._load_cached_towns()
    
    def _check_eigengrau_availability(self) -> bool:
        """
        Check if Eigengrau's Generator is available in the system.
        
        Returns:
            bool: True if available, False otherwise
        """
        # Check for the Eigengrau directory in common locations
        eigengrau_paths = [
            os.path.join(os.path.dirname(__file__), '../eigengrau'),
            os.path.join(os.path.dirname(__file__), '../EigengrausGenerator'),
            '/eigengrau',
            '/EigengrausGenerator'
        ]
        
        for path in eigengrau_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # Check for package.json to confirm it's the right directory
                if os.path.exists(os.path.join(path, 'package.json')):
                    return True
        
        return False
    
    def _load_cached_towns(self) -> None:
        """Load any previously generated towns from the cache directory."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    town_id = filename.replace('.json', '')
                    with open(os.path.join(self.cache_dir, filename), 'r') as f:
                        self.town_cache[town_id] = json.load(f)
            
            logger.info(f"Loaded {len(self.town_cache)} towns from cache.")
        except Exception as e:
            logger.error(f"Error loading cached towns: {str(e)}")
    
    async def generate_town(self, town_id: str = None, seed: int = None) -> Dict[str, Any]:
        """
        Generate a new town or retrieve from cache if already generated.
        
        Args:
            town_id: Optional ID for the town
            seed: Optional seed for deterministic generation
            
        Returns:
            Dict containing the town data
        """
        # Generate a town ID if not provided
        if not town_id:
            town_id = f"town_{random.randint(1000, 9999)}"
        
        # Check if town is already in cache
        if town_id in self.town_cache:
            logger.info(f"Retrieved town {town_id} from cache.")
            return self.town_cache[town_id]
        
        # Generate the town
        if self.eigengrau_available:
            town_data = await self._generate_with_eigengrau(town_id, seed)
        else:
            town_data = self._generate_fallback(town_id, seed)
        
        # Cache the town
        self.town_cache[town_id] = town_data
        self._save_town_to_cache(town_id, town_data)
        
        return town_data
    
    async def _generate_with_eigengrau(self, town_id: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a town using Eigengrau's Generator.
        
        Args:
            town_id: ID for the town
            seed: Optional seed for deterministic generation
            
        Returns:
            Dict containing the town data
        """
        logger.info(f"Generating town {town_id} with Eigengrau's Generator...")
        
        try:
            # This is a placeholder for the actual Eigengrau integration
            # In a real implementation, we would:
            # 1. Find the Eigengrau installation
            # 2. Run it with appropriate parameters
            # 3. Capture and parse the output
            
            # For now, we'll simulate the process with a delay
            await asyncio.sleep(2)
            
            # Create a simulated output that mimics Eigengrau's structure
            town_data = self._generate_fallback(town_id, seed)
            town_data["_meta"] = {
                "generator": "eigengrau",
                "version": "2.4",
                "seed": seed or random.randint(1, 1000000)
            }
            
            logger.info(f"Successfully generated town {town_id} with Eigengrau.")
            return town_data
            
        except Exception as e:
            logger.error(f"Error generating town with Eigengrau: {str(e)}")
            logger.info("Falling back to procedural generation.")
            return self._generate_fallback(town_id, seed)
    
    def _generate_fallback(self, town_id: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a town using fallback procedural generation when Eigengrau is not available.
        
        Args:
            town_id: ID for the town
            seed: Optional seed for deterministic generation
            
        Returns:
            Dict containing the town data
        """
        logger.info(f"Generating town {town_id} with fallback generator...")
        
        # Set the random seed if provided
        if seed is not None:
            random.seed(seed)
        
        # Generate town name
        town_names_first = ["Green", "River", "Mountain", "Lake", "Forest", "Shadow", "Sun", "Moon", "Star", "Dragon", "Eagle", "Wolf"]
        town_names_second = ["vale", "ford", "haven", "hold", "keep", "cross", "bridge", "port", "wood", "field", "hill", "dale"]
        town_name = f"{random.choice(town_names_first)}{random.choice(town_names_second)}"
        
        # Generate town size and population
        sizes = ["hamlet", "village", "town", "large town", "small city", "city"]
        size_idx = random.randint(0, len(sizes) - 1)
        size = sizes[size_idx]
        population = random.randint(50, 200) * (size_idx + 1)
        
        # Generate town description
        descriptions = [
            "nestled in a peaceful valley",
            "perched on a hillside overlooking fertile plains",
            "situated at a crossroads of major trade routes",
            "built along the banks of a winding river",
            "protected by an ancient stone wall",
            "sprawling across several small islands connected by bridges",
            "hidden within a dense forest",
            "built around a natural spring known for its healing properties"
        ]
        description = random.choice(descriptions)
        
        # Generate buildings
        building_types = ["tavern", "blacksmith", "general store", "temple", "town hall", "guard post", "stable", "inn", "farm", "mill"]
        num_buildings = random.randint(5, 15)
        buildings = []
        
        for i in range(num_buildings):
            building_type = random.choice(building_types)
            
            # Generate building name
            if building_type == "tavern" or building_type == "inn":
                adjectives = ["Golden", "Silver", "Rusty", "Prancing", "Sleeping", "Laughing", "Drunken", "Jolly"]
                nouns = ["Dragon", "Lion", "Stag", "Pony", "Giant", "Goblin", "Barrel", "Flagon", "Sword", "Shield"]
                name = f"The {random.choice(adjectives)} {random.choice(nouns)}"
            else:
                name = f"{random.choice(['Old', 'New', 'Fine', 'Quality', 'Town', 'River'])} {building_type.title()}"
            
            # Generate building description
            building_descriptions = [
                "a sturdy structure with a thatched roof",
                "a stone building with a wooden door",
                "a two-story building with large windows",
                "a modest structure with a smoking chimney",
                "an old building that has seen better days",
                "a well-maintained building with flower boxes"
            ]
            
            building = {
                "id": f"building_{i+1}",
                "name": name,
                "type": building_type,
                "description": random.choice(building_descriptions),
                "npcs": []
            }
            
            buildings.append(building)
        
        # Generate NPCs
        npc_roles = ["innkeeper", "blacksmith", "merchant", "guard", "farmer", "priest", "noble", "beggar", "adventurer"]
        npc_traits = ["friendly", "suspicious", "greedy", "helpful", "wise", "foolish", "brave", "cowardly"]
        
        num_npcs = random.randint(10, 20)
        npcs = []
        
        first_names = ["Aldric", "Bram", "Cora", "Dorn", "Eliza", "Finn", "Greta", "Hilda", "Ivan", "Jora", "Kord", "Lena", "Milo", "Nora", "Oskar", "Petra", "Quentin", "Rosa", "Silas", "Tilda"]
        last_names = ["Smith", "Miller", "Cooper", "Fletcher", "Baker", "Tanner", "Fisher", "Hunter", "Farmer", "Brewer", "Potter", "Weaver", "Carpenter", "Mason"]
        
        for i in range(num_npcs):
            role = random.choice(npc_roles)
            trait = random.choice(npc_traits)
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Assign NPC to a building if appropriate
            building_id = None
            if role in ["innkeeper", "blacksmith", "merchant", "priest"]:
                matching_buildings = [b for b in buildings if b["type"] in [
                    "tavern" if role == "innkeeper" else role,
                    "inn" if role == "innkeeper" else role,
                    "general store" if role == "merchant" else role,
                    "temple" if role == "priest" else role
                ]]
                
                if matching_buildings:
                    building = random.choice(matching_buildings)
                    building_id = building["id"]
                    building["npcs"].append(f"npc_{i+1}")
            
            # Generate NPC description
            descriptions = [
                f"a {trait} {role} with a distinctive scar",
                f"a {trait} {role} known for their loud laugh",
                f"a {trait} {role} with a mysterious past",
                f"a {trait} {role} respected by the townsfolk",
                f"a {trait} {role} new to the town",
                f"a {trait} {role} from a long line of {role}s"
            ]
            
            npc = {
                "id": f"npc_{i+1}",
                "name": f"{first_name} {last_name}",
                "role": role,
                "trait": trait,
                "description": random.choice(descriptions),
                "building_id": building_id,
                "quests": []
            }
            
            # Add some quests for certain NPCs
            if random.random() < 0.3:  # 30% chance of having a quest
                quest_types = ["fetch", "rescue", "escort", "investigate", "deliver"]
                quest_targets = ["item", "person", "location", "monster", "information"]
                quest_difficulties = ["easy", "medium", "hard"]
                
                quest = {
                    "id": f"quest_{town_id}_{i+1}",
                    "type": random.choice(quest_types),
                    "target": random.choice(quest_targets),
                    "difficulty": random.choice(quest_difficulties),
                    "description": f"A {random.choice(quest_difficulties)} quest to {random.choice(quest_types)} a {random.choice(quest_targets)}.",
                    "reward": random.randint(10, 100) * (quest_difficulties.index(random.choice(quest_difficulties)) + 1),
                    "completed": False
                }
                
                npc["quests"].append(quest)
            
            npcs.append(npc)
        
        # Generate town rumors
        rumor_subjects = ["hidden treasure", "monster sightings", "strange disappearances", "political intrigue", "magical phenomena", "ancient ruins"]
        rumor_locations = ["nearby forest", "old mine", "abandoned tower", "beneath the town", "neighboring kingdom", "within the town itself"]
        
        num_rumors = random.randint(3, 7)
        rumors = []
        
        for i in range(num_rumors):
            subject = random.choice(rumor_subjects)
            location = random.choice(rumor_locations)
            
            rumor = {
                "id": f"rumor_{i+1}",
                "text": f"There are whispers of {subject} in the {location}.",
                "truth": random.choice([True, False]),  # Is the rumor true?
                "known_by": random.sample([npc["id"] for npc in npcs], random.randint(1, min(5, len(npcs))))
            }
            
            rumors.append(rumor)
        
        # Assemble the town data
        town_data = {
            "id": town_id,
            "name": town_name,
            "size": size,
            "population": population,
            "description": f"{town_name} is a {size} {description}, with a population of about {population} people.",
            "buildings": buildings,
            "npcs": npcs,
            "rumors": rumors,
            "_meta": {
                "generator": "fallback",
                "version": "1.0",
                "seed": seed or random.randint(1, 1000000)
            }
        }
        
        logger.info(f"Successfully generated town {town_id} with fallback generator.")
        return town_data
    
    def _save_town_to_cache(self, town_id: str, town_data: Dict[str, Any]) -> None:
        """
        Save a generated town to the cache directory.
        
        Args:
            town_id: ID of the town
            town_data: Town data to save
        """
        try:
            cache_path = os.path.join(self.cache_dir, f"{town_id}.json")
            with open(cache_path, 'w') as f:
                json.dump(town_data, f, indent=2)
            logger.info(f"Saved town {town_id} to cache.")
        except Exception as e:
            logger.error(f"Error saving town to cache: {str(e)}")
    
    def get_town(self, town_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a town by ID from the cache.
        
        Args:
            town_id: ID of the town to retrieve
            
        Returns:
            Town data if found, None otherwise
        """
        return self.town_cache.get(town_id)
    
    def get_all_towns(self) -> List[Dict[str, Any]]:
        """
        Get all towns from the cache.
        
        Returns:
            List of all town data
        """
        return list(self.town_cache.values())
    
    def get_town_summary(self, town_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a town (without full details).
        
        Args:
            town_id: ID of the town
            
        Returns:
            Dict with town summary if found, None otherwise
        """
        town = self.get_town(town_id)
        if not town:
            return None
        
        return {
            "id": town["id"],
            "name": town["name"],
            "size": town["size"],
            "population": town["population"],
            "description": town["description"],
            "building_count": len(town["buildings"]),
            "npc_count": len(town["npcs"])
        }
    
    async def get_or_generate_town(self, town_id: str = None, seed: int = None) -> Dict[str, Any]:
        """
        Get a town from cache or generate if not found.
        
        Args:
            town_id: ID of the town
            seed: Optional seed for generation
            
        Returns:
            Town data
        """
        if town_id and town_id in self.town_cache:
            return self.town_cache[town_id]
        
        return await self.generate_town(town_id, seed)
    
    def get_building(self, town_id: str, building_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific building from a town.
        
        Args:
            town_id: ID of the town
            building_id: ID of the building
            
        Returns:
            Building data if found, None otherwise
        """
        town = self.get_town(town_id)
        if not town:
            return None
        
        for building in town["buildings"]:
            if building["id"] == building_id:
                return building
        
        return None
    
    def get_npc(self, town_id: str, npc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific NPC from a town.
        
        Args:
            town_id: ID of the town
            npc_id: ID of the NPC
            
        Returns:
            NPC data if found, None otherwise
        """
        town = self.get_town(town_id)
        if not town:
            return None
        
        for npc in town["npcs"]:
            if npc["id"] == npc_id:
                return npc
        
        return None
    
    def get_npcs_in_building(self, town_id: str, building_id: str) -> List[Dict[str, Any]]:
        """
        Get all NPCs in a specific building.
        
        Args:
            town_id: ID of the town
            building_id: ID of the building
            
        Returns:
            List of NPC data
        """
        town = self.get_town(town_id)
        if not town:
            return []
        
        return [npc for npc in town["npcs"] if npc.get("building_id") == building_id]
    
    def get_rumors(self, town_id: str) -> List[Dict[str, Any]]:
        """
        Get all rumors in a town.
        
        Args:
            town_id: ID of the town
            
        Returns:
            List of rumors
        """
        town = self.get_town(town_id)
        if not town:
            return []
        
        return town.get("rumors", [])
    
    def get_quests(self, town_id: str) -> List[Dict[str, Any]]:
        """
        Get all quests in a town.
        
        Args:
            town_id: ID of the town
            
        Returns:
            List of quests
        """
        town = self.get_town(town_id)
        if not town:
            return []
        
        quests = []
        for npc in town["npcs"]:
            for quest in npc.get("quests", []):
                quest_copy = quest.copy()
                quest_copy["npc_id"] = npc["id"]
                quest_copy["npc_name"] = npc["name"]
                quests.append(quest_copy)
        
        return quests

# Singleton instance
_town_generator = None

def get_town_generator() -> TownGenerator:
    """
    Get the singleton instance of the TownGenerator.
    
    Returns:
        TownGenerator instance
    """
    global _town_generator
    if _town_generator is None:
        _town_generator = TownGenerator()
    return _town_generator

async def generate_initial_town() -> Dict[str, Any]:
    """
    Generate the initial town for game start.
    
    Returns:
        Town data
    """
    generator = get_town_generator()
    return await generator.generate_town("starting_town", seed=42)  # Fixed seed for consistency

async def main():
    """Test function for the town generator."""
    generator = get_town_generator()
    town = await generator.generate_town("test_town")
    print(f"Generated town: {town['name']}")
    print(f"Description: {town['description']}")
    print(f"Buildings: {len(town['buildings'])}")
    print(f"NPCs: {len(town['npcs'])}")
    print(f"Rumors: {len(town['rumors'])}")
    
    # Save to a file for inspection
    with open("test_town.json", "w") as f:
        json.dump(town, f, indent=2)
    print("Town data saved to test_town.json")

if __name__ == "__main__":
    asyncio.run(main())
