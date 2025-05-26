# Chronicle Weave - Digital DM Game

## Overview

Chronicle Weave is an agent-based digital dungeon master system that provides an interactive text-based RPG experience. The game combines traditional RPG elements with modern AI techniques to create a dynamic and engaging storytelling environment.

## Features

- **Character Creation**: Create and customize your character with different races, classes, and abilities
- **Dynamic World**: Explore a procedurally generated town with various locations and NPCs
- **Interactive Storytelling**: Engage with a responsive narrative that adapts to your choices
- **Mini-Map System**: Visual representation of the game world that updates as you explore
- **Save/Load System**: Save your progress and resume your adventure later
- **Mobile Compatibility**: Fully responsive design that works on both desktop and mobile devices

## Technical Architecture

### Backend Components

- **Game Server**: FastAPI-based WebSocket server that handles game state and client connections
- **Agent System**: Modular agent architecture including:
  - Supervisor Agent: Coordinates other agents
  - Intent Agent: Interprets player input
  - Rule Agent: Enforces game mechanics
  - Narrative Agent: Generates story content
  - World Agent: Manages the game world
- **Town Generator**: Creates procedural towns with locations, NPCs, and quests

### Frontend Components

- **WebSocket Client**: Real-time communication with the game server
- **Responsive UI**: Adapts to different screen sizes and devices
- **Character Sheet**: Dynamic display of character information
- **Mini-Map**: Visual representation of the game world
- **Save/Load Interface**: User-friendly save management

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js (optional, for development)
- Modern web browser

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/digital-dm-game.git
cd digital-dm-game
```

2. Install Python dependencies:
```
pip install -r requirements.txt
```

3. Run the game server:
```
./run_game.sh
```
or
```
python -m uvicorn game_server:app --host 0.0.0.0 --port 8080
```

4. Open your browser and navigate to:
```
http://localhost:8080
```

## Game Mechanics

### Character Creation

1. Choose a character name
2. Select a race (Human, Elf, Dwarf, Halfling)
3. Select a class (Fighter, Wizard, Rogue, Cleric)
4. Begin your adventure in the town

### Exploration

- Move between locations using commands like "go to [location]"
- Interact with NPCs using "talk to [character]"
- Examine your surroundings with "look around"
- Use the mini-map for visual navigation

### Combat (Basic Implementation)

- Turn-based combat system
- Actions include attack, spell, item, and flee
- Combat stats based on character attributes

### Save System

- Manual saves with custom names
- Auto-save functionality
- Export/import save files
- Local storage backup

## Development

### Project Structure

```
digital_dm_game/
├── agents/             # Agent system components
├── data/               # Game data and resources
├── frontend/           # Web client files
│   ├── static/         # Static assets
│   └── index.html      # Main game interface
├── models/             # Game data models
├── tests/              # Test suite
├── utils/              # Utility functions
├── game_server.py      # Main server implementation
├── town_generator.py   # Procedural town generation
├── requirements.txt    # Python dependencies
└── run_game.sh         # Startup script
```

### Adding New Features

See the `WORK_TO_BE_DONE.md` file for planned enhancements and development guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by classic text adventures and tabletop RPGs
- Built with FastAPI, WebSockets, and modern web technologies
