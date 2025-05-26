#!/bin/bash
# Run Digital DM Game with proper WebSocket support

# Kill any existing processes on port 8080
fuser -k 8080/tcp 2>/dev/null

# Start the game server with FastAPI/Uvicorn
cd /home/ubuntu/digital_dm_game
python -m uvicorn game_server:app --host 0.0.0.0 --port 8080
