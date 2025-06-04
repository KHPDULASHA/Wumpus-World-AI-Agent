import pygame
import random
import sys

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
safe_tiles = set()

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

# Main loop
running = True
while running:
    screen.fill((153, 153, 255))

     # Auto mode logic - indented correctly inside while loop
    if auto_mode and not game_over:
        auto_step_counter += 1
        if auto_step_counter >= auto_step_delay:
            possible_moves = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = agent_pos[0] + dx, agent_pos[1] + dy
                if 0 <= nx < ROWS and 0 <= ny < COLS:
                    possible_moves.append((nx, ny))
            if possible_moves:
                agent_pos = list(random.choice(possible_moves))
                steps += 1
                safe_tiles.add(tuple(agent_pos))
            auto_step_counter = 0  # reset counter

            

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
                        safe_tiles.clear()
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
                if event.key in move_keys:
                    dx, dy = move_keys[event.key]

            # Update direction based on movement
                if (dx, dy) == (-1, 0):
                    agent_dir = "UP"
                    arrow_img = pygame.transform.rotate(images["arrow"], 180)
                elif (dx, dy) == (1, 0):
                    agent_dir = "DOWN"
                    arrow_img = images["arrow"]  # No rotation needed
                elif (dx, dy) == (0, -1):
                    agent_dir = "LEFT"
                    arrow_img = pygame.transform.rotate(images["arrow"], 90)
                elif (dx, dy) == (0, 1):
                    agent_dir = "RIGHT"
                    arrow_img = pygame.transform.rotate(images["arrow"], -90)

                nx, ny = agent_pos[0] + dx, agent_pos[1] + dy
                if 0 <= nx < ROWS and 0 <= ny < COLS:
                    agent_pos = [nx, ny]
                    steps += 1
                    safe_tiles.add(tuple(agent_pos))

                elif event.key == pygame.K_a and not arrow_used:
                    arrow_used = True
                    arrow = "No"
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        tx, ty = agent_pos[0] + dx, agent_pos[1] + dy
                        if 0 <= tx < ROWS and 0 <= ty < COLS:
                            if world[tx][ty]["wumpus"]:
                                world[tx][ty]["wumpus"] = False
                                wumpus_alive = False
                                score += 50
                                break

    if not game_over:
        x, y = agent_pos

        if world[x][y]["gold"] and not has_gold:
            has_gold = True
            world[x][y]["gold"] = False
            score += 100
            gold += 1

        if world[x][y]["pit"] or (world[x][y]["wumpus"] and wumpus_alive):
            score -= 100
            game_over = True

        if has_gold and agent_pos == [0, 0]:
            score += 50
            game_over = True

    for i in range(ROWS):
        for j in range(COLS):
            rect = pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, (0, 18, 77), rect, 1)
            if (i, j) in safe_tiles:
                pygame.draw.rect(screen, (230, 236, 255), rect)
                pygame.draw.rect(screen, (0, 18, 77), rect, 1)
            cell = world[i][j]
            if cell["gold"]:
                screen.blit(images["gold"], rect.topleft)
            if cell["pit"]:
                screen.blit(images["pit"], rect.topleft)
            if cell["wumpus"] and wumpus_alive:
                screen.blit(images["wumpus"], rect.topleft)

    
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
