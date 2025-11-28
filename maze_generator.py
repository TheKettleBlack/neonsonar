import random

# Tile legend
# 0 = floor
# 1 = wall
# 2 = key
# 3 = exit
# 4 = player start

def generate_maze(cols, rows, room_chance=0.2, max_room_size=6):
    # Ensure odd numbers so maze walls work properly
    if cols % 2 == 0: cols += 1
    if rows % 2 == 0: rows += 1

    # Create grid full of walls
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    # Directions for carving: (dx, dy)
    directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]

    def carve(x, y):
        maze[y][x] = 0  # carve floor

        # Possibly create a room at this location
        if random.random() < room_chance:
            create_room(x, y)

        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx < cols-1 and 1 <= ny < rows-1:
                if maze[ny][nx] == 1:  # still a wall → carve it
                    # carve the tile between current and next cell
                    maze[y + dy//2][x + dx//2] = 0
                    carve(nx, ny)

    def create_room(cx, cy):
        # Random odd dimensions for the room
        w = random.randrange(3, max_room_size, 2)
        h = random.randrange(3, max_room_size, 2)
        start_x = max(1, cx - w // 2)
        start_y = max(1, cy - h // 2)
        end_x = min(cols-2, start_x + w)
        end_y = min(rows-2, start_y + h)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                maze[y][x] = 0

    # Start carving from a random odd tile
    start_x = random.randrange(1, cols, 2)
    start_y = random.randrange(1, rows, 2)
    carve(start_x, start_y)

    # Collect all floor tiles
    floor_tiles = [(x, y) for y in range(rows) for x in range(cols) if maze[y][x] == 0]

    # Random player start
    player_start = random.choice(floor_tiles)

    # Place key as the FARTHEREST tile from player start
    key_pos = max(floor_tiles, key=lambda t: (t[0]-player_start[0])**2 + (t[1]-player_start[1])**2)

    # Exit is farthest from the key
    exit_pos = max(floor_tiles, key=lambda t: (t[0]-key_pos[0])**2 + (t[1]-key_pos[1])**2)

    # Enemies: evenly spread
    enemy_positions = []
    min_enemies = 8
    max_enemies = 12
    num_enemies = random.randint(min_enemies, max_enemies)

    floor_tiles_shuffled = floor_tiles.copy()
    random.shuffle(floor_tiles_shuffled)

    placed = 0
    for fx, fy in floor_tiles_shuffled:
        if (fx, fy) in [player_start, key_pos, exit_pos]:
            continue
        enemy_positions.append((fx, fy))
        placed += 1
        if placed >= num_enemies:
            break

    # Mark special tiles
    px, py = player_start
    kx, ky = key_pos
    ex, ey = exit_pos

    maze[py][px] = 4  # player start
    maze[ky][kx] = 2  # key
    maze[ey][ex] = 3  # exit

    return maze, player_start, key_pos, exit_pos, enemy_positions