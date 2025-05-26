"""
Chronicle Weave - Main Entry Point

This module serves as the entry point for the Digital DM game.
"""
import os
import uvicorn
from game_server import app

if __name__ == "__main__":
    print("Starting Chronicle Weave Digital DM Game Server...")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
