# Wumpus World AI Agent
A graphical simulation of a Wumpus World environment and an intelligent agent that explores, infers, and survives using knowledge-based reasoning. Implemented in Python with Pygame.

## Features
- **4x4 Wumpus World Grid**
- Randomized placement of pits, the Wumpus, and gold each game
- Agent receives percepts: Breeze, Stench, Glitter
- Knowledge base (KB) tracks safe, unsafe, and visited cells
- Logical inference: deduces safe moves from percepts
- Auto-mode: agent explores automatically, solves for gold, and attempts escape
- Manual play: arrow-key movement, shoot arrow, reset world, toggle auto/sound
- Visual interface with clear cell states and agent direction

  ## Gameplay
- **Start:** Agent begins at (0,0), always safe
- **Goal:** Grab the gold and return to the start without falling into a pit or being eaten by the Wumpus
- **Percepts:**  
  - **Breeze:** Adjacent to a pit  
  - **Stench:** Adjacent to the Wumpus  
  - **Glitter:** Gold is present in the current cell
 
  ## Controls
  - **Arrow keys:** Move the agent manually
  - **A key:** Shoot arrow in current facing direction (once per game)
  - **Sidebar buttons:**
  - **Play/Step:** (if implemented) Step through agent actions
  - **Auto:** Toggle agent auto-mode
  - **Reset:** Generate a new random world
  - **Sound:** Toggle sound effects (if implemented)
 
  ## How the Agent Thinks
  - Maintains a knowledge base of cell safety, hazards, and visited status
  - Uses percepts to infer the presence/absence of pits and Wumpus in adjacent tiles
  - Marks cells as safe if no breeze/stench is detected nearby
  - Uses A* pathfinding to plan routes to safe or goal cells
  - Auto mode: systematically explores, collects gold, and escapes, shooting Wumpus if necessary
 
    ## Installation & Running
  1. **Clone this repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   ```

2. **Install dependencies:**
   ```bash
   pip install pygame
   ```

3. **Add images:**  
   Place the following images in an `Images/` folder (relative to the script):
   - `agent.png`
   - `gold.png`
   - `wumpus.png`
   - `pit.png`
   - `arrow.png`

4. **Run the game:**
   ```bash
   python wumpus_world.py
   ```

   ## Credits

Developed by KHPDULASHA
    
  
