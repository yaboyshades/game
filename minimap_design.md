# Mini-Map Design for Digital DM Game

## Overview
The mini-map feature will provide players with a visual representation of the game world, showing their current location, visited locations, and unexplored areas. It will update dynamically as the player explores the town and will be integrated into the existing sidebar UI.

## UI Design

### Placement
The mini-map will be placed in the sidebar, below the character sheet and above the location info section. This provides a logical flow of information:
1. Character information (top)
2. World map (middle)
3. Current location details (bottom)

### Visual Style
- **Map Container**: A rounded rectangle with a slightly darker background than the sidebar
- **Map Border**: Styled to look like an aged parchment or fantasy map
- **Location Markers**: Distinct icons for different location types (inn, shop, temple, etc.)
- **Player Marker**: A distinctive marker (e.g., a pulsing dot or arrow) showing the player's current position
- **Visited vs. Unexplored**: Visited locations will be fully visible, while unexplored areas will be partially transparent or shown as outlines

### Responsive Design
- On desktop: Full detailed map with all markers visible
- On mobile portrait: Compact version focusing on nearby locations
- On mobile landscape: Similar to desktop but with adjusted proportions

## Technical Implementation

### Data Structure
The backend will need to track:
1. All locations in the town
2. Which locations the player has visited
3. Connections between locations (paths, roads)
4. The player's current location

```json
{
  "town_map": {
    "name": "Eigengrau",
    "locations": [
      {
        "id": "town_square",
        "name": "Town Square",
        "type": "square",
        "x": 50,
        "y": 50,
        "connections": ["inn", "blacksmith", "temple"]
      },
      {
        "id": "inn",
        "name": "The Prancing Pony Inn",
        "type": "inn",
        "x": 30,
        "y": 70,
        "connections": ["town_square", "market"]
      },
      // More locations...
    ],
    "player_visited": ["town_square", "inn"],
    "current_location": "inn"
  }
}
```

### Frontend Rendering
The mini-map will be rendered using HTML5 Canvas for performance and flexibility:

1. Draw the base map background
2. Draw connection paths between locations
3. Draw location markers with appropriate icons
4. Highlight the player's current location
5. Apply visual effects for visited vs. unexplored areas

### Dynamic Updates
The mini-map will update in response to:
1. Player movement between locations
2. Discovery of new locations
3. Changes in the game world (e.g., new quests, events)

## Integration with Game State

### Backend Changes
1. Enhance the `GameState` class to include map data
2. Update location tracking to include coordinates and connections
3. Add methods to update the map when players discover new areas
4. Include map data in the game state sent to the frontend

### Frontend Changes
1. Add a new mini-map component to the sidebar
2. Create rendering logic for the map using Canvas
3. Update the map when new game state is received
4. Add interactive elements (hover tooltips, click to view details)

## User Interaction
- **Hover**: Show location name and brief description
- **Click**: Center the map on that location and show more details
- **Zoom**: Allow zooming in/out on larger maps (optional)
- **Pan**: Allow panning the map for larger worlds (optional)

## Animation and Effects
- Smooth transitions when moving between locations
- Subtle pulsing effect for the player marker
- Reveal animation when discovering new locations
- Path highlighting when traveling

## Future Expansion
The mini-map system will be designed to accommodate future enhancements:
- Multiple towns/regions
- Dungeon maps with different visualization
- Quest markers and points of interest
- Fog of war for unexplored areas
