# Save Functionality Design for Digital DM Game

## Overview
The save functionality will allow players to save their game progress and resume later, enhancing the game experience by preserving character development, exploration progress, and game state across sessions.

## Data Structure

### Save Data Format
The save data will include:

```json
{
  "save_id": "unique_save_id",
  "timestamp": "2025-05-26T01:05:00Z",
  "player_data": {
    "user_id": "user_123",
    "character": {
      "name": "Aragorn",
      "race": "Human",
      "class_name": "Fighter",
      "level": 1,
      "strength": 16,
      "dexterity": 12,
      "constitution": 14,
      "intelligence": 8,
      "wisdom": 10,
      "charisma": 10,
      "hp": 12,
      "max_hp": 12,
      "ac": 16,
      "inventory": [],
      "known_spells": [],
      "spell_slots": {}
    }
  },
  "game_state": {
    "current_location_id": "town_square",
    "in_combat": false,
    "combat_data": null,
    "town_map": {
      "name": "Eigengrau",
      "player_visited": ["town_square", "inn", "market"]
    },
    "quests": [],
    "game_flags": {}
  }
}
```

### Storage Methods
1. **Backend Storage**: Save data stored in server-side JSON files
2. **Local Storage**: Browser localStorage for client-side backup
3. **Export/Import**: Allow players to download/upload save files

## Implementation Approach

### Backend Implementation
1. Create save/load endpoints in the FastAPI server
2. Implement save file management (create, list, load, delete)
3. Add auto-save functionality at key game points
4. Implement save versioning for backward compatibility

### Frontend Implementation
1. Add save/load UI elements to the game interface
2. Create save management modal dialog
3. Implement localStorage backup mechanism
4. Add export/import functionality for save files

## User Interface

### Save Button
- Add a save button to the game interface (top-right corner)
- Show save confirmation with save name/slot selection
- Display timestamp of last save

### Load Menu
- Create a load game menu accessible from the main screen
- Show available saves with character info and timestamps
- Allow deletion of saves

### Auto-Save Indicator
- Show a subtle indicator when auto-save occurs
- Include last auto-save time in the save menu

## Technical Details

### Save File Management
- Save files stored in `/saves/{user_id}/` directory
- Filename format: `{save_id}_{timestamp}.json`
- Maintain a `save_index.json` file listing all saves

### Save/Load Process
1. **Saving**:
   - Collect current game state and player data
   - Generate unique save ID if new save
   - Write to file with timestamp
   - Update save index
   - Store backup in localStorage

2. **Loading**:
   - Read save file from server
   - Validate data structure
   - Restore game state and player character
   - Update UI to reflect loaded state

### Error Handling
- Implement save corruption detection
- Provide backup recovery options
- Handle version compatibility issues

## Security Considerations
- Validate save data to prevent injection attacks
- Implement user authentication for save access
- Sanitize imported save files

## Future Expansion
- Cloud save synchronization
- Multiple save slots per user
- Save file sharing between players
- Save file conversion between versions
