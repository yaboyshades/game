# Chronicle Weave: Digital DM Game - Setup and Running Instructions

## Overview

Chronicle Weave is an agent-based Digital Dungeon Master game that uses AI to create immersive D&D 5e adventures. The system features:

1. **Agent-Based Architecture**:
   - Intent Agent: Understands natural language player commands
   - Rule Agent: Processes D&D 5e rules and game mechanics
   - Narrative Agent: Generates immersive storytelling
   - World Agent: Creates dynamic game content with town generation
   - Agent Supervisor: Orchestrates all agents

2. **Model Protocol Server**:
   - Standardized API for all LLM interactions
   - Support for multiple model backends (OpenAI, Anthropic, local models)
   - Caching and request batching for efficiency

3. **Town Generator**:
   - Procedurally generates detailed towns with buildings, NPCs, and local history
   - Supports both pre-generated and on-demand town creation
   - Includes NPCs with personalities, quests, and dialogue

4. **Game Features**:
   - Character creation and customization
   - Dynamic world exploration
   - NPC interactions
   - Combat system
   - Spell casting
   - Item management

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Extract the zip file**:
   ```bash
   unzip digital_dm_game.zip
   cd digital_dm_game
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys (optional)**:
   For enhanced AI capabilities, you can set up API keys for OpenAI or Anthropic:
   ```bash
   # For OpenAI
   export OPENAI_API_KEY=your_openai_api_key
   
   # For Anthropic
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   ```
   
   If no API keys are provided, the system will use mock responses for testing.

## Running the Game

### Local Development

1. **Start the game server**:
   ```bash
   python main.py
   ```

2. **Access the game**:
   Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

### Cloud Shell Deployment

If you're using Google Cloud Shell:

1. **Make scripts executable**:
   ```bash
   chmod +x setup.sh run_local.sh deploy_cloud_run.sh
   ```

2. **Run setup script**:
   ```bash
   ./setup.sh
   ```

3. **Start the game locally**:
   ```bash
   ./run_local.sh
   ```
   Then click the Web Preview icon (eye icon) in the Cloud Shell toolbar.

4. **Deploy to Google Cloud Run** (for smartphone access):
   ```bash
   ./deploy_cloud_run.sh
   ```
   This will give you a public URL you can access from any device.

## Using the Town Generator

The town generator creates detailed towns with buildings, NPCs, and quests. Here's how to use it:

1. **Initial Town**:
   The game starts with a pre-generated town. You can explore it immediately.

2. **On-Demand Towns**:
   New towns are generated as you explore the world. Each town includes:
   - Unique name and description
   - Various buildings (taverns, shops, temples, etc.)
   - NPCs with personalities and backstories
   - Local rumors and quests

3. **Town Exploration**:
   - Look around to see buildings and NPCs
   - Enter buildings to find NPCs inside
   - Talk to NPCs to learn about the town
   - Ask about rumors to discover quests
   - Accept quests from NPCs

## Development Guide

### Project Structure

- `agents/`: Agent modules for game logic
- `models/`: Data models and game state
- `data/`: Game data and cached towns
- `frontend/`: Web interface
- `utils/`: Utility functions
- `town_generator.py`: Town generation module
- `model_protocol_server.py`: LLM integration
- `game_server.py`: FastAPI server
- `main.py`: Entry point

### Adding New Features

1. **New Agent Types**:
   Create a new agent class in the `agents/` directory that inherits from `Agent`.

2. **Custom Town Generation**:
   Modify `town_generator.py` to add new town features or generation methods.

3. **Game Mechanics**:
   Update the Rule Agent to implement new game mechanics.

## Troubleshooting

1. **Port Already in Use**:
   If you see "error while attempting to bind on address 0.0.0.0", try:
   ```bash
   # Check for processes using the port
   lsof -i :8000
   
   # Kill the process
   kill -9 [PID]
   
   # Or use a different port
   python -m uvicorn game_server:app --host 0.0.0.0 --port 8080
   ```

2. **Missing Module Errors**:
   Ensure you've installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **API Key Issues**:
   If using real LLM APIs, verify your API keys are set correctly:
   ```bash
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
