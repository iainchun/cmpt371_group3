# Multiplayer Grid Holding Game (CMPT 371 Project)

This project is a multiplayer game server-client system written in Python. Players connect to a central server and attempt to hold boxes on an 8x8 grid to gain control. Holding a box for a specific amount of time colors it and awards the player points.

---

## Game Description

- Players join the server and are assigned a unique player ID and color.
- The game begins when **at least 3 players** connect.
- A **10-second countdown** starts before the game begins.
- Each player can "hold" a box on the grid.
- If a player holds the same box for **3 seconds**, the box is marked with that player's color.
- Only one player can hold a box at a time.
- The game ends after a set time or condition (as defined in the game logic).
- The player(s) with the highest score win.

---

## Files

- `server.py`: The main game server script. Accepts clients and manages the game logic.
- `client.py`: The client script. Sends player actions and receives updates from the server.

---

## How to Run
Make sure pygame is intalled.

### 1. Start the Server

```bash
python server.py
```
### 1. Start Clients (each in a new terminal)

```bash
python client.py
```

## Requirements
Python 3.x

No external dependencies (uses socket, threading, and time)

