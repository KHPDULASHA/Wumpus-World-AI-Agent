import pygame
import random
import sys
import heapq

# Initialize pygame
pygame.init()
clock = pygame.time.Clock()

# Screen config
WIDTH, HEIGHT = 500, 400
ROWS, COLS = 4, 4
SIDEBAR_WIDTH = 200
TILE_SIZE = (WIDTH - SIDEBAR_WIDTH) // COLS
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wumpus World")

# Load and resize images
images = {
    "agent": pygame.image.load("Images/agent.png"),
    "gold": pygame.image.load("Images/gold.png"),
    "wumpus": pygame.image.load("Images/wumpus.png"),
    "pit": pygame.image.load("Images/pit.png"),
    "arrow": pygame.image.load("Images/arrow.png"),
}
for key in images:
    images[key] = pygame.transform.scale(images[key], (int(TILE_SIZE * 0.8), int(TILE_SIZE * 0.8)))
images["arrow"] = pygame.transform.scale(images["arrow"], (int(TILE_SIZE * 0.4), int(TILE_SIZE * 0.4)))

# Fonts
font = pygame.font.SysFont(None, 24)

# Environment setup
world = [[{"pit": False, "wumpus": False, "gold": False} for _ in range(COLS)] for _ in range(ROWS)]
agent_pos = [0, 0]
agent_dir = "RIGHT"  # initial facing direction
has_gold = False
game_over = False
arrow_used = False
wumpus_alive = True

# Knowledge base for agent
# Each cell: {"safe": bool/None, "visited": bool, "pit?": bool/None, "wumpus?": bool/None}
kb = [[{"safe": None, "visited": False, "pit?": None, "wumpus?": None} for _ in range(COLS)] for _ in range(ROWS)]

# Functions for percepts
def adjacent_tiles(x, y):
    return [(i, j) for i, j in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)] if 0 <= i < ROWS and 0 <= j < COLS]

def get_percepts(pos):
    x, y = pos
    percepts = []
    if world[x][y]["gold"]:
        percepts.append("Glitter")
    if any(world[i][j]["wumpus"] for i, j in adjacent_tiles(x, y)):
        percepts.append("Stench")
    if any(world[i][j]["pit"] for i, j in adjacent_tiles(x, y)):
        percepts.append("Breeze")
    return percepts

# Place game elements
def place_random():
    global wumpus_alive, arrow_used
    wumpus_alive = True
    arrow_used = False
    for i in range(ROWS):
        for j in range(COLS):
            world[i][j] = {"pit": False, "wumpus": False, "gold": False}
            kb[i][j] = {"safe": None, "visited": False, "pit?": None, "wumpus?": None}

    positions = [(i, j) for i in range(ROWS) for j in range(COLS) if (i, j) != (0, 0)]
    random.shuffle(positions)

    gold_pos = positions.pop()
    wumpus_pos = positions.pop()
    pit1_pos = positions.pop()
    pit2_pos = positions.pop()

    world[gold_pos[0]][gold_pos[1]]["gold"] = True
    world[wumpus_pos[0]][wumpus_pos[1]]["wumpus"] = True
    world[pit1_pos[0]][pit1_pos[1]]["pit"] = True
    world[pit2_pos[0]][pit2_pos[1]]["pit"] = True

place_random()

# UI setup
sidebar_rect = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
bottom_rect = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)
button_height = 40
padding = 10
buttons = {
    "Play": pygame.Rect(WIDTH - SIDEBAR_WIDTH + padding, padding, SIDEBAR_WIDTH - 2*padding, button_height),
    "Step": pygame.Rect(WIDTH - SIDEBAR_WIDTH + padding, padding*2 + button_height, SIDEBAR_WIDTH - 2*padding, button_height),
    "Reset": pygame.Rect(WIDTH - SIDEBAR_WIDTH + padding, padding*3 + 2*button_height, SIDEBAR_WIDTH - 2*padding, button_height),
    "Auto": pygame.Rect(WIDTH - SIDEBAR_WIDTH + padding, padding*4 + 3*button_height, SIDEBAR_WIDTH - 2*padding, button_height),
    "Sound": pygame.Rect(WIDTH - SIDEBAR_WIDTH + padding, padding*5 + 4*button_height, SIDEBAR_WIDTH - 2*padding, button_height),
}

# Stats
score = 0
steps = 0
gold = 0
arrow = "Yes"
auto_mode = False
sound_on = True

auto_step_delay = 10  # number of frames to wait between auto moves
auto_step_counter = 0

# --- AGENT LOGIC ---

def infer_safe_and_danger(pos):
    """Performs logical inference to update knowledge base about adjacent tiles."""
    x, y = pos
    percepts = get_percepts(pos)
    kb[x][y]["visited"] = True
    kb[x][y]["safe"] = True

    adjs = adjacent_tiles(x, y)
    stench = "Stench" in percepts
    breeze = "Breeze" in percepts

    for (i, j) in adjs:
        # If no stench, then no wumpus in adj
        if not stench:
            kb[i][j]["wumpus?"] = False
        # If no breeze, then no pit in adj
        if not breeze:
            kb[i][j]["pit?"] = False
        # If both stench and breeze are absent, mark safe
        if not stench and not breeze:
            kb[i][j]["safe"] = True
    # If visited, mark safe
    kb[x][y]["safe"] = True

def unexplored_safe_tiles():
    """Returns list of unvisited but inferred safe tiles."""
    tiles = []
    for i in range(ROWS):
        for j in range(COLS):
            if kb[i][j]["safe"] and not kb[i][j]["visited"]:
                tiles.append((i, j))
    return tiles

def unexplored_unknown_tiles():
    """Returns list of unvisited tiles that are not definitely unsafe."""
    tiles = []
    for i in range(ROWS):
        for j in range(COLS):
            if not kb[i][j]["visited"]:
                # Not marked as pit/wumpus with certainty
                if kb[i][j]["pit?"] is not True and kb[i][j]["wumpus?"] is not True:
                    tiles.append((i, j))
    return tiles

def is_safe(i, j):
    """Returns True if tile is known to be safe."""
    return kb[i][j]["safe"] is True

def pathfind(start, goal, allow_unknown=False):
    """A* pathfinding from start to goal. Only through safe (or optionally unknown) tiles."""
    # Tiles are (x, y)
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: abs(goal[0]-start[0]) + abs(goal[1]-start[1])}

    def neighbors(x, y):
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < ROWS and 0 <= ny < COLS:
                if is_safe(nx, ny) or (allow_unknown and kb[nx][ny]["safe"] is not False):
                    yield (nx, ny)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            # reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1][1:]  # Exclude start
        for neighbor in neighbors(*current):
            tentative = g_score[current] + 1
            if neighbor not in g_score or tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score[neighbor] = tentative + abs(goal[0]-neighbor[0]) + abs(goal[1]-neighbor[1])
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []  # No path found

def agent_auto_move():
    """Smart agent: strategic exploration, danger avoidance, knowledge-based pathfinding, and Wumpus shooting."""
    global agent_pos, has_gold, game_over, score, arrow_used, wumpus_alive, arrow

    infer_safe_and_danger(tuple(agent_pos))

    # --- SHOOT WUMPUS IF INFERRED WITH CERTAINTY AND IN ADJACENT TILE ---
    if not arrow_used and wumpus_alive:
        x, y = agent_pos
        percepts = get_percepts((x, y))
        if "Stench" in percepts:
            adjs = adjacent_tiles(x, y)
            wumpus_candidates = []
            for i, j in adjs:
                # If this adjacent tile could be the wumpus (not marked safe or visited, not ruled out as wumpus)
                if kb[i][j]["wumpus?"] is not False and not kb[i][j]["visited"]:
                    wumpus_candidates.append((i, j))
            # If exactly one candidate, shoot at it!
            if len(wumpus_candidates) == 1:
                wx, wy = wumpus_candidates[0]
                # Mark arrow used
                arrow_used = True
                arrow = "No"
                # Kill the wumpus if actually there
                if world[wx][wy]["wumpus"]:
                    world[wx][wy]["wumpus"] = False
                    wumpus_alive = False
                    score += 50
                    # Update KB: no more wumpus in world
                    for i in range(ROWS):
                        for j in range(COLS):
                            kb[i][j]["wumpus?"] = False
                # Mark that tile as safe for future
                kb[wx][wy]["safe"] = True

    if has_gold:
        # Try to pathfind home through safe tiles. If not possible, allow unknown (risky) tiles.
        path = pathfind(tuple(agent_pos), (0,0), allow_unknown=False)
        if not path:
            path = pathfind(tuple(agent_pos), (0,0), allow_unknown=True)
        if path:
            agent_pos[:] = path[0]
            kb[agent_pos[0]][agent_pos[1]]["visited"] = True
            return
        else:
            # No path home. Game over (trapped).
            game_over = True
            return

    # If gold is in current tile, pick it up
    if world[agent_pos[0]][agent_pos[1]]["gold"]:
        has_gold = True
        world[agent_pos[0]][agent_pos[1]]["gold"] = False
        score += 100
        return

    # Explore unvisited safe tiles, closest first
    safe_unvisited = unexplored_safe_tiles()
    if safe_unvisited:
        safe_unvisited.sort(key=lambda t: abs(t[0]-agent_pos[0]) + abs(t[1]-agent_pos[1]))
        for target in safe_unvisited:
            path = pathfind(tuple(agent_pos), target)
            if path:
                agent_pos[:] = path[0]
                kb[agent_pos[0]][agent_pos[1]]["visited"] = True
                return

    # No known safe tiles left. Take a risk (unexplored and not definitely unsafe)
    unknowns = unexplored_unknown_tiles()
    if unknowns:
        unknowns.sort(key=lambda t: abs(t[0]-agent_pos[0]) + abs(t[1]-agent_pos[1]))
        for target in unknowns:
            path = pathfind(tuple(agent_pos), target, allow_unknown=True)
            if path:
                agent_pos[:] = path[0]
                kb[agent_pos[0]][agent_pos[1]]["visited"] = True
                return

    # Nowhere to go, stop.
    game_over = True

# Main loop
running = True
while running:
    screen.fill((153, 153, 255))

    # Auto mode logic
    if auto_mode and not game_over:
        auto_step_counter += 1
        if auto_step_counter >= auto_step_delay:
            agent_auto_move()
            steps += 1
            auto_step_counter = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            for label, rect in buttons.items():
                if rect.collidepoint(mouse_pos):
                    if label == "Reset":
                        place_random()
                        agent_pos = [0, 0]
                        has_gold = False
                        score = 0
                        steps = 0
                        gold = 0
                        arrow = "Yes"
                        game_over = False
                    elif label == "Auto":
                        auto_mode = not auto_mode
                    elif label == "Sound":
                        sound_on = not sound_on

        elif event.type == pygame.KEYDOWN:
            if not game_over:
                move_keys = {
                    pygame.K_UP: (-1, 0),
                    pygame.K_DOWN: (1, 0),
                    pygame.K_LEFT: (0, -1),
                    pygame.K_RIGHT: (0, 1)
                }

                # --------- Movement Code ---------
                if event.key in move_keys:
                    dx, dy = move_keys[event.key]

                    # Update direction based on movement key
                    if (dx, dy) == (-1, 0):
                        agent_dir = "UP"
                        arrow_img = pygame.transform.rotate(images["arrow"], 180)
                    elif (dx, dy) == (1, 0):
                        agent_dir = "DOWN"
                        arrow_img = images["arrow"]
                    elif (dx, dy) == (0, -1):
                        agent_dir = "LEFT"
                        arrow_img = pygame.transform.rotate(images["arrow"], 90)
                    elif (dx, dy) == (0, 1):
                        agent_dir = "RIGHT"
                        arrow_img = pygame.transform.rotate(images["arrow"], -90)

                    # Move agent if within bounds and safe/unknown
                    nx, ny = agent_pos[0] + dx, agent_pos[1] + dy
                    if 0 <= nx < ROWS and 0 <= ny < COLS:
                        if kb[nx][ny]["safe"] is not False:
                            agent_pos = [nx, ny]
                            kb[nx][ny]["visited"] = True
                            steps += 1

                # --------- Shooting Code (Press 'A') ---------
                elif event.key == pygame.K_a and not arrow_used:
                    arrow_used = True
                    arrow = "No"

                    # Set direction to shoot based on agent_dir
                    dx, dy = {
                        "UP": (-1, 0),
                        "DOWN": (1, 0),
                        "LEFT": (0, -1),
                        "RIGHT": (0, 1)
                    }[agent_dir]

                    # Shoot in that direction
                    for step in range(1, ROWS):
                        tx = agent_pos[0] + dx * step
                        ty = agent_pos[1] + dy * step

                        if 0 <= tx < ROWS and 0 <= ty < COLS:
                            if world[tx][ty]["wumpus"]:
                                world[tx][ty]["wumpus"] = False
                                wumpus_alive = False
                                score += 50
                                # Update KB: no more wumpus in world
                                for i in range(ROWS):
                                    for j in range(COLS):
                                        kb[i][j]["wumpus?"] = False
                                break  # arrow stops after killing wumpus
                        else:
                            break  # arrow goes out of bounds

    # AGENT INTERACTION
    if not game_over:
        x, y = agent_pos

        if not kb[x][y]["visited"]:
            steps += 1
        kb[x][y]["visited"] = True

        if world[x][y]["gold"] and not has_gold:
            has_gold = True
            world[x][y]["gold"] = False
            score += 100
            gold += 1

        if world[x][y]["pit"] or (world[x][y]["wumpus"] and wumpus_alive):
            score -= 100
            kb[x][y]["safe"] = False
            game_over = True

        # If agent brought gold home
        if has_gold and agent_pos == [0, 0]:
            score += 50
            game_over = True

        infer_safe_and_danger((x, y))

    # Draw world
    for i in range(ROWS):
        for j in range(COLS):
            rect = pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, (0, 18, 77), rect, 1)
            # Knowledge-based coloring
            if kb[i][j]["visited"]:
                pygame.draw.rect(screen, (230, 236, 255), rect)
            elif kb[i][j]["safe"] is True:
                pygame.draw.rect(screen, (200, 255, 200), rect)
            elif kb[i][j]["safe"] is False:
                pygame.draw.rect(screen, (255, 200, 200), rect)
            # Draw elements
            cell = world[i][j]
            if cell["gold"]:
                screen.blit(images["gold"], rect.topleft)
            if cell["pit"]:
                screen.blit(images["pit"], rect.topleft)
            if cell["wumpus"] and wumpus_alive:
                screen.blit(images["wumpus"], rect.topleft)
            # Visited mark
            if kb[i][j]["visited"]:
                pygame.draw.circle(screen, (0, 0, 0), rect.center, 5)

    # Center the agent image in its tile
    tile_x = agent_pos[1] * TILE_SIZE
    tile_y = agent_pos[0] * TILE_SIZE

    agent_img = images["agent"]
    arrow_img = images["arrow"]

    # Calculate positions to center agent and arrow vertically inside the tile
    agent_x = tile_x + (TILE_SIZE - agent_img.get_width()) // 2
    agent_y = tile_y + (TILE_SIZE - agent_img.get_height()) // 2 - 5  # move slightly up
    arrow_x = tile_x + (TILE_SIZE - arrow_img.get_width()) // 2
    arrow_y = agent_y + agent_img.get_height() - 10  # place just below agent

    # Blit agent and arrow
    screen.blit(agent_img, (agent_x, agent_y))
    screen.blit(arrow_img, (arrow_x, arrow_y))

    if game_over:
        message = "You Win!" if has_gold and agent_pos == [0, 0] else "Game Over!"
        msg_surf = font.render(message, True, (255, 0, 0))
        padding = 10
        msg_rect = msg_surf.get_rect(center=(WIDTH // 2 - SIDEBAR_WIDTH // 2, HEIGHT // 2))
        box_rect = pygame.Rect(
            msg_rect.left - padding,
            msg_rect.top - padding,
            msg_rect.width + 2 * padding,
            msg_rect.height + 2 * padding
        )
        pygame.draw.rect(screen, (255, 179, 179), box_rect)
        pygame.draw.rect(screen, (255, 26, 26), box_rect, 2)
        screen.blit(msg_surf, msg_rect)

    pygame.draw.rect(screen, (0, 0, 128), sidebar_rect)
    for label, rect in buttons.items():
        pygame.draw.rect(screen, (117, 117, 163), rect)
        text = label
        if label == "Auto":
            text = "Auto: ON" if auto_mode else "Auto: OFF"
        elif label == "Sound":
            text = "Sound: ON" if sound_on else "Sound: OFF"
        text_surf = font.render(text, True, (0,0,0))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    pygame.draw.rect(screen, (0, 0, 128), bottom_rect)
    info_texts = [
        f"Score: {score}",
        f"Steps: {steps}",
        f"Gold: {gold}",
        f"Arrow: {arrow}"
    ]
    for idx, text in enumerate(info_texts):
        text_surf = font.render(text, True, (255,255,255))
        text_x = 10 + idx * (WIDTH // 4)
        text_y = HEIGHT - 40
        screen.blit(text_surf, (text_x, text_y))

    # Percept display
    percepts = get_percepts(agent_pos)
    percept_text = "Percepts: " + ", ".join(percepts) if percepts else "Percepts: None"
    percept_surf = font.render(percept_text, True, (255,255,255))
    screen.blit(percept_surf, (10, HEIGHT - 17))

    pygame.display.flip()
    clock.tick(10)