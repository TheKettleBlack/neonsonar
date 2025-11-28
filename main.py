import pygame
from sys import exit
import math
import random
import maze_generator
from particles import Particle

# Spin up pygame
pygame.init()
pygame.display.set_caption("ping!")

# Static variables
FPS = 60
WIDTH = 800
HEIGHT = 600
BLACK = (0,0,0)
BLUE = (0,170,255)
PURPLE = (170,0,255)
PINK = (255,0,170)
ORANGE = (255,170,0)
GREEN = (170,255,0)
WHITE = (255,255,255)
MAZE_COLS = 40
MAZE_ROWS = 30
TILE_SIZE = 50
CAMERA_MARGIN = 200
SONAR_MAX_RADIUS = 300
SONAR_SPEED = 5
SONAR_COLOR = GREEN
ANIM_SPEED = 8
MAX_ENERGY = 100
ENERGY_DRAIN = 20
ENERGY_DRAIN_FROM_ENEMY = 240
ENERGY_RECHARGE = 0.05
ENERGY_DRAIN_PER_SECOND = 20
ENERGY_RECHARGE_PER_SECOND = 5
font = pygame.font.SysFont('Arial', 32)
screen = pygame.display.set_mode((WIDTH,HEIGHT))
clock = pygame.time.Clock()

# Images
player_up = [
    pygame.image.load("img/up1.png").convert_alpha(),
    pygame.image.load("img/up2.png").convert_alpha(),
    pygame.image.load("img/up3.png").convert_alpha(),
    pygame.image.load("img/up4.png").convert_alpha()
]
player_down = [
    pygame.image.load("img/down1.png").convert_alpha(),
    pygame.image.load("img/down2.png").convert_alpha(),
    pygame.image.load("img/down3.png").convert_alpha(),
    pygame.image.load("img/down4.png").convert_alpha()
]
player_left = [
    pygame.image.load("img/left1.png").convert_alpha(),
    pygame.image.load("img/left2.png").convert_alpha()
]
player_right = [
    pygame.image.load("img/right1.png").convert_alpha(),
    pygame.image.load("img/right2.png").convert_alpha()
]
wallImg = pygame.image.load("img/1.png").convert_alpha()
keyImg = pygame.image.load("img/2.png").convert_alpha()
exitImg = pygame.image.load("img/3.png").convert_alpha()
enemy_up_img = pygame.image.load("img/eu.png").convert_alpha()
enemy_down_img = pygame.image.load("img/ed.png").convert_alpha()
enemy_left_img = pygame.image.load("img/el.png").convert_alpha()
enemy_right_img = pygame.image.load("img/er.png").convert_alpha()
got_key_img = pygame.image.load("img/got_key.png").convert_alpha()

# Sprite groups
playerGroup = pygame.sprite.GroupSingle()
keyGroup = pygame.sprite.GroupSingle()
exitGroup = pygame.sprite.GroupSingle()
doorGroup = pygame.sprite.Group()
terrainGroup = pygame.sprite.Group()
enemyGroup = pygame.sprite.Group()
particleGroup = pygame.sprite.Group()

# Game variables
camera_x = 0
camera_y = 0
player_speed = 2
run_speed = 4
fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
fog.fill((0,0,0))
fog.set_alpha(255)
sonar_active = False
sonar_radius = 0
exit_visible = False
key_visible = False
arrow_radius = 30
revealed_walls = set()
revealed_enemies = set()
energy = MAX_ENERGY
has_key = False
level_complete = False
enemy_positions = []
player_dead = False
game_state = "playing"
player = None
mouse_was_down = False
pending_level_reset = False
game_running = True

# def drawText(text,font,text_col,x,y):
#     img = font.render(text,True,text_col)
#     screen.blit(img,(x,y))

# Tile legend
# 0 = floor
# 1 = wall
# 2 = key
# 3 = exit
# 4 = player start

# Initiate a new level
def getLevel():
    global revealed_walls, key_visible, exit_visible
    global energy, has_key, level_complete
    global sonar_active, sonar_radius
    global game_state, player

    # Reset state
    game_state = "playing"
    sonar_active = False
    sonar_radius = 0
    key_visible = False
    exit_visible = False
    revealed_walls = set()
    has_key = False
    level_complete = False
    energy = MAX_ENERGY

    # Clear all sprite groups
    playerGroup.empty()
    keyGroup.empty()
    exitGroup.empty()
    doorGroup.empty()
    terrainGroup.empty()
    particleGroup.empty()
    enemyGroup.empty()

    # Generate the maze and positions
    maze, player_start, key_pos, exit_pos, enemy_positions = maze_generator.generate_maze(MAZE_COLS, MAZE_ROWS)
    print("Player:", player_start)
    print("Key:", key_pos)
    print("Exit:", exit_pos)
    print("Enemies:", enemy_positions)

    # Spawn tiles, key, exit, player
    for y, row in enumerate(maze):
        for x, tile in enumerate(row):
            if tile == 1:
                terrainGroup.add(Tile(x, y, tile))
            elif tile == 2:
                keyGroup.add(Key(x * TILE_SIZE, y * TILE_SIZE))
            elif tile == 3:
                exitGroup.add(Exit(x * TILE_SIZE, y * TILE_SIZE))
            elif tile == 4:
                player = Player(x, y, player_up, player_down, player_left, player_right)
                playerGroup.add(player)

    # Spawn enemies with their directional images
    for ex, ey in enemy_positions:
        enemyGroup.add(
            Enemy(
                ex * TILE_SIZE,
                ey * TILE_SIZE,
                enemy_up_img,     # provide your loaded up image
                enemy_down_img,   # provide your loaded down image
                enemy_left_img,   # provide your loaded left image
                enemy_right_img   # provide your loaded right image
            )
        )

    # Center camera on player
    center_camera()

# Center the camera
def center_camera():
    global camera_x, camera_y
    camera_x = player.rect.centerx - WIDTH // 2
    camera_y = player.rect.centery - HEIGHT // 2

# Update the camera
def update_camera():
    global camera_x, camera_y
    screen_x = player.rect.centerx - camera_x
    screen_y = player.rect.centery - camera_y
    if screen_x < CAMERA_MARGIN:
        camera_x = player.rect.centerx - CAMERA_MARGIN
    elif screen_x > WIDTH - CAMERA_MARGIN:
        camera_x = player.rect.centerx - (WIDTH - CAMERA_MARGIN)
    if screen_y < CAMERA_MARGIN:
        camera_y = player.rect.centery - CAMERA_MARGIN
    elif screen_y > HEIGHT - CAMERA_MARGIN:
        camera_y = player.rect.centery - (HEIGHT - CAMERA_MARGIN)

# Draw sprite groups
def draw_group(group):
    for sprite in group.sprites():
        screen.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y - camera_y))

# Draw glow on key and exit
def draw_glow(target_rect, color, camera_x, camera_y, size=20, alpha=100):
    glow_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
    pygame.draw.circle(glow_surface, (*color, alpha), (size, size), size)
    screen.blit(
        glow_surface,
        (target_rect.centerx - size - camera_x,
         target_rect.centery - size - camera_y)
    )

# Draw the energy bar
def draw_energy_bar(player,energy,max_energy):
    bar_width = 40
    bar_height = 6
    bar_x = player.rect.centerx - camera_x - bar_width // 2
    bar_y = player.rect.y - camera_y - 10
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
    fill_ratio = energy/max_energy
    fill_width = int(bar_width * fill_ratio)
    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_width, bar_height))
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)

# Draw buttons
def draw_button(text, x, y, w, h, bg_color):
    # Draw button rectangle
    pygame.draw.rect(screen, bg_color, (x, y, w, h))
    
    # Draw button text
    text_surf = font.render(text, True, BLACK)
    screen.blit(text_surf, (x + (w - text_surf.get_width()) // 2,
                            y + (h - text_surf.get_height()) // 2))
    
    # Return True if mouse is over this button
    mx, my = pygame.mouse.get_pos()
    return x < mx < x+w and y < my < y+h
    
# Called from buttons above, continue
def next_level():
    global pending_level_reset
    pending_level_reset = True

# Called from buttons above, quit
def quit_game():
    global game_running, mouse_was_down
    mouse_was_down = False
    game_running = False

# Called when the player hits the exit with the key. Can use level_complete for state management.
def unlocked(exit_tile):
    global level_complete, game_state
    if not level_complete:
        level_complete = True
        spawnParticles(exit_tile.rect.centerx, exit_tile.rect.centery)
        exit_x = exit_tile.rect.x
        exit_y = exit_tile.rect.y
        exitGroup.empty()
        doorGroup.add(DoorExit(exit_x, exit_y))
        # Let the door animate before displaying buttons
        game_state = "door_animating"

# Particles
def spawnParticles(x, y):
    for _ in range(50):
        color = random.choice((BLUE, PURPLE, PINK, ORANGE, GREEN))
        direction = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1))
        if direction.length() == 0:
            direction = pygame.math.Vector2(0,-1)
        else:
            direction = direction.normalize()
        particle_speed = random.uniform(3, 6)
        Particle(particleGroup, (x, y), color, direction, particle_speed)

# Check enemy line of sight to player, Bresenham-style
def has_line_of_sight(enemy, player, walls):
    ex, ey = enemy.rect.center
    px, py = player.rect.center
    ex_tile = ex // TILE_SIZE
    ey_tile = ey // TILE_SIZE
    px_tile = px // TILE_SIZE
    py_tile = py // TILE_SIZE
    dx = px_tile - ex_tile
    dy = py_tile - ey_tile
    n = max(abs(dx), abs(dy))
    if n == 0:
        return True
    for step in range(n + 1):
        tx = int(ex_tile + dx * step / n)
        ty = int(ey_tile + dy * step / n)
        # Check if this tile is a wall
        for w in walls:
            wx, wy = w.rect.x // TILE_SIZE, w.rect.y // TILE_SIZE
            if wx == tx and wy == ty:
                return False
    return True

def player_died(player_pos):
    player_x = player_pos[0]
    player_y = player_pos[1]
    global player_dead
    player_dead = True
    spawnParticles(player_x, player_y)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, up, down, left, right):
        super().__init__()
        self.sprites = {
            "up": up,
            "down": down,
            "left": left,
            "right": right
        }
        self.direction = "down"
        self.current_sprite = 0
        self.image = self.sprites[self.direction][self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.x = (x * TILE_SIZE) + 12
        self.rect.y = (y * TILE_SIZE) + 12
        self.anim_timer = 0

    def update(self, keys_pressed):
        global energy
        old_x = self.rect.x
        old_y = self.rect.y
        moved_this_frame = False

        # Can they run?
        running = keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT]
        if running and energy <= 0:
            running = False
        speed = run_speed if running else player_speed

        # Movement
        if keys_pressed[97]:  # A = left
            self.rect.x -= speed
            self.direction = "left"
        if keys_pressed[100]:  # D = right
            self.rect.x += speed
            self.direction = "right"
        for tile in terrainGroup:
            if self.rect.colliderect(tile.rect):
                self.rect.x = old_x
                break
        old_y = self.rect.y
        if keys_pressed[119]:  # W = up
            self.rect.y -= speed
            self.direction = "up"
        if keys_pressed[115]:  # S = down
            self.rect.y += speed
            self.direction = "down"
        for tile in terrainGroup:
            if self.rect.colliderect(tile.rect):
                self.rect.y = old_y
                break
        if self.rect.x != old_x or self.rect.y != old_y:
            moved_this_frame = True

        update_camera()

        # Animate movement
        frames = self.sprites[self.direction]
        if moved_this_frame:
            self.anim_timer += 1
            if self.anim_timer >= ANIM_SPEED:
                self.current_sprite = (self.current_sprite + 1) % len(frames)
                self.image = frames[self.current_sprite]
                self.anim_timer = 0
        else:
            self.current_sprite = 0
            self.image = frames[0]

        # Drain energy if running and moving
        if running and moved_this_frame > 0:
            energy -= ENERGY_DRAIN_PER_SECOND / FPS
            if energy < 0:
                energy = 0

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, img_up, img_down, img_left, img_right):
        super().__init__()
        # Directional images
        self.images = {
            "up": img_up,
            "down": img_down,
            "left": img_left,
            "right": img_right
        }
        self.direction = "down"
        self.image = self.images[self.direction]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 1.5
        self.revealed = False
        self.chase_player = False

    def reveal(self):
        self.revealed = True

    def hide(self):
        self.revealed = False

    def update(self):
        global energy
        # Only chase if revealed and player is in line of sight
        self.chase_player = has_line_of_sight(self, player, terrainGroup)

        if self.chase_player:
            # Move toward player
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            if distance > 0:
                dx /= distance
                dy /= distance
                new_x = self.rect.x + dx * self.speed
                new_y = self.rect.y + dy * self.speed

                # Move horizontally and check collision with walls
                self.rect.x = new_x
                for wall in terrainGroup:
                    if self.rect.colliderect(wall.rect):
                        self.rect.x -= dx * self.speed
                        break

                # Move vertically and check collision with walls
                self.rect.y = new_y
                for wall in terrainGroup:
                    if self.rect.colliderect(wall.rect):
                        self.rect.y -= dy * self.speed
                        break

                # Set facing direction
                if abs(dx) > abs(dy):
                    self.direction = "right" if dx > 0 else "left"
                else:
                    self.direction = "down" if dy > 0 else "up"
                self.image = self.images[self.direction]

        # Drain player energy if colliding, and bump back the enemy
        if self.rect.colliderect(player.rect):
            energy -= ENERGY_DRAIN_FROM_ENEMY / FPS  # adjust damage per second
            if energy <= 0:
                energy = 0
                player_died(player.rect.center)  # call your function when player runs out of energy

            # Simple bump-back: move enemy away from player
            bump_distance = 5
            dx = self.rect.centerx - player.rect.centerx
            dy = self.rect.centery - player.rect.centery
            distance = math.hypot(dx, dy)
            if distance > 0:
                dx /= distance
                dy /= distance
                self.rect.x += dx * bump_distance
                self.rect.y += dy * bump_distance

            # Prevent bumping into walls
            for wall in terrainGroup:
                if self.rect.colliderect(wall.rect):
                    # Undo bump in the offending axis
                    if abs(self.rect.centerx - wall.rect.centerx) < TILE_SIZE:
                        self.rect.x -= dx * bump_distance
                    if abs(self.rect.centery - wall.rect.centery) < TILE_SIZE:
                        self.rect.y -= dy * bump_distance

# Tile class
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        if type == 1:
            self.image = wallImg
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

# Key class
class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = keyImg
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Exit class
class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = exitImg
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class DoorExit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Load animation frames
        self.frames = [
            pygame.image.load("img/3.png").convert_alpha(),
            pygame.image.load("img/3a.png").convert_alpha(),
            pygame.image.load("img/3b.png").convert_alpha(),
            pygame.image.load("img/3c.png").convert_alpha(),
            pygame.image.load("img/3d.png").convert_alpha(),
            pygame.image.load("img/3e.png").convert_alpha(),
            pygame.image.load("img/3f.png").convert_alpha(),
            pygame.image.load("img/3g.png").convert_alpha()
        ]
        self.current_frame = 0
        self.anim_timer = 0
        self.anim_speed = 6   # lower = slower animation
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    def update(self):
        if self.current_frame < len(self.frames) - 1:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_speed:
                self.current_frame += 1
                self.image = self.frames[self.current_frame]
                self.anim_timer = 0
        else:
            global game_state, mouse_was_down
            if game_state == "door_animating":
                game_state = "level_complete"
                mouse_was_down = False

# Start the game by grabbing a level
getLevel()

# Main loop
while game_running:

    # Event check
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        keys_pressed = pygame.key.get_pressed()

    # Check mouse state for clicks
    mx, my = pygame.mouse.get_pos()
    mouse_down = pygame.mouse.get_pressed()[0]
    mouse_clicked = mouse_down and not mouse_was_down
    mouse_was_down = mouse_down

    # Reset level?
    if pending_level_reset:
        getLevel()
        pending_level_reset = False
        game_state = "playing"

    # We be playin'
    if game_state == "playing":

        # Initial fill of screen with black
        screen.fill(BLACK)

        # Keyboard presses
        if keys_pressed[pygame.K_SPACE] and not sonar_active and energy >= ENERGY_DRAIN:
            sonar_active = True
            sonar_radius = 0
            energy -= ENERGY_DRAIN

        # Update player and camera
        player.update(keys_pressed)
        update_camera()

        # Energy recharge
        if not sonar_active and energy < MAX_ENERGY and not (keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT]):
            energy = min(MAX_ENERGY, energy + ENERGY_RECHARGE_PER_SECOND / FPS)
        
        # Draw walls
        draw_group(terrainGroup)

        # Check enemy line of sight to player
        for enemy in enemyGroup:
            enemy.hide()  # default hidden
            if has_line_of_sight(enemy, player, terrainGroup):
                enemy.reveal()
                enemy.chase_player = True
            if sonar_active:
                dx = enemy.rect.centerx - player.rect.centerx
                dy = enemy.rect.centery - player.rect.centery
                distance = math.hypot(dx, dy)
                if distance <= sonar_radius:
                    enemy.reveal()
                    enemy.chase_player = True

        # Update enemy states
        enemyGroup.update()

        # Draw all enemies
        for enemy in enemyGroup:
            if enemy.revealed:   # Only draw if revealed
                screen.blit(enemy.image, (enemy.rect.x - camera_x, enemy.rect.y - camera_y))

        # Cover with fog
        fog.fill((0,0,0,255))  

        # Draw sonar
        if sonar_active:
            pygame.draw.circle(fog, (0,255,0,100),
                            (player.rect.centerx - camera_x, player.rect.centery - camera_y),
                            sonar_radius)
            sonar_radius += SONAR_SPEED
            if sonar_radius > SONAR_MAX_RADIUS:
                sonar_active = False
                for enemy in enemyGroup:
                    enemy.hide()

            # Reveal walls
            for wall in terrainGroup:
                dx = wall.rect.centerx - player.rect.centerx
                dy = wall.rect.centery - player.rect.centery
                distance = math.hypot(dx, dy)
                if distance <= sonar_radius:
                    revealed_walls.add(wall)

            # Reveal exit
            for exit_tile in exitGroup:
                exit_dx = exit_tile.rect.centerx - player.rect.centerx
                exit_dy = exit_tile.rect.centery - player.rect.centery
                exit_distance = math.hypot(exit_dx, exit_dy)
                if exit_distance <= sonar_radius:
                    exit_visible = True

            # Reveal key
            for key_tile in keyGroup:
                key_dx = key_tile.rect.centerx - player.rect.centerx
                key_dy = key_tile.rect.centery - player.rect.centery
                key_distance = math.hypot(key_dx, key_dy)
                if key_distance <= sonar_radius:
                    key_visible = True
        
        # Paint fog
        screen.blit(fog,(0,0))

        # Paint revealed walls
        for wall in revealed_walls:
            screen.blit(wall.image, (wall.rect.x - camera_x, wall.rect.y - camera_y))

        # Paint revealed enemies
        for enemy in enemyGroup:
            if enemy.revealed:   # Only draw if revealed
                screen.blit(enemy.image, (enemy.rect.x - camera_x, enemy.rect.y - camera_y))

        # Draw key if it's been pinged
        if key_visible and keyGroup.sprites():
            key_tile = keyGroup.sprites()[0]
            draw_glow(key_tile.rect, (255, 150, 0), camera_x, camera_y, size=30, alpha=120)
            screen.blit(key_tile.image, (key_tile.rect.x - camera_x, key_tile.rect.y - camera_y))
        
        # Got the key?
        if key_visible and keyGroup.sprites() and not has_key:
            key_tile = keyGroup.sprites()[0]
            if player.rect.colliderect(key_tile.rect):
                has_key = True
                spawnParticles(key_tile.rect.centerx, key_tile.rect.centery)
                keyGroup.empty()

        # Draw exit if it's been pinged
        if exit_visible and exitGroup.sprites():
            exit_tile = exitGroup.sprites()[0]
            draw_glow(exit_tile.rect, (0, 200, 0), camera_x, camera_y, size=35, alpha=120)
            screen.blit(exit_tile.image, (exit_tile.rect.x - camera_x, exit_tile.rect.y - camera_y))

        # Draw player, then energy bar
        draw_group(playerGroup)
        draw_energy_bar(player, energy, MAX_ENERGY)

        # Draw animated door if exiting
        doorGroup.update()
        draw_group(doorGroup)

        # Draw particles if exiting
        particleGroup.update()
        for particle in particleGroup:
            screen.blit(particle.image, (particle.rect.x - camera_x, particle.rect.y - camera_y))

        # Draw arrows for pinged exit and key
        if exit_visible and exitGroup.sprites():
            exit_tile = exitGroup.sprites()[0]
            exit_dx = exit_tile.rect.centerx - player.rect.centerx
            exit_dy = exit_tile.rect.centery - player.rect.centery
            exit_angle = math.atan2(exit_dy, exit_dx)
            exit_arrow_x = player.rect.centerx + math.cos(exit_angle) * arrow_radius - camera_x
            exit_arrow_y = player.rect.centery + math.sin(exit_angle) * arrow_radius - camera_y
            exit_size = 10
            exit_tip = (exit_arrow_x + math.cos(exit_angle)*exit_size, exit_arrow_y + math.sin(exit_angle)*exit_size)
            exit_left = (exit_arrow_x + math.cos(exit_angle+math.pi/2)*exit_size/2, exit_arrow_y + math.sin(exit_angle+math.pi/2)*exit_size/2)
            exit_right = (exit_arrow_x + math.cos(exit_angle-math.pi/2)*exit_size/2, exit_arrow_y + math.sin(exit_angle-math.pi/2)*exit_size/2)
            pygame.draw.polygon(screen, GREEN, [exit_tip, exit_left, exit_right])
        if key_visible and keyGroup.sprites():
            key_tile = keyGroup.sprites()[0]
            key_dx = key_tile.rect.centerx - player.rect.centerx
            key_dy = key_tile.rect.centery - player.rect.centery
            key_angle = math.atan2(key_dy, key_dx)
            key_arrow_x = player.rect.centerx + math.cos(key_angle) * arrow_radius - camera_x
            key_arrow_y = player.rect.centery + math.sin(key_angle) * arrow_radius - camera_y
            key_size = 10
            key_tip = (key_arrow_x + math.cos(key_angle)*key_size, key_arrow_y + math.sin(key_angle)*key_size)
            key_left = (key_arrow_x + math.cos(key_angle+math.pi/2)*key_size/2, key_arrow_y + math.sin(key_angle+math.pi/2)*key_size/2)
            key_right = (key_arrow_x + math.cos(key_angle-math.pi/2)*key_size/2, key_arrow_y + math.sin(key_angle-math.pi/2)*key_size/2)
            pygame.draw.polygon(screen, ORANGE, [key_tip, key_left, key_right])

        # Key reminder
        if has_key:
            screen.blit(got_key_img, (10,10))

        # Player unlocked the door?
        if has_key and exit_visible and exitGroup.sprites():
            exit_tile = exitGroup.sprites()[0]
            if player.rect.colliderect(exit_tile.rect):
                unlocked(exit_tile)

    # Door is being animated
    elif game_state == "door_animating":
        screen.fill(BLACK)

        # Draw world
        draw_group(terrainGroup)
        draw_group(playerGroup)
        enemyGroup.update()
        for enemy in enemyGroup:
            if enemy.revealed:
                screen.blit(enemy.image, (enemy.rect.x - camera_x, enemy.rect.y - camera_y))

        # Draw the animated door
        doorGroup.update()
        draw_group(doorGroup)

        # Draw particles
        particleGroup.update()
        for particle in particleGroup:
            screen.blit(particle.image, (particle.rect.x - camera_x, particle.rect.y - camera_y))

    # Escaped
    elif game_state == "level_complete":
        screen.fill(BLACK)
        
        # Draw buttons and check hover
        next_hover = draw_button("Next Level", WIDTH//2 - 100, HEIGHT//2 - 40, 200, 60, GREEN)
        quit_hover = draw_button("Quit", WIDTH//2 - 100, HEIGHT//2 + 40, 200, 60, PINK)

        # Handle click
        if mouse_clicked:
            if next_hover:
                next_level()  # now just sets the flag
            elif quit_hover:
                quit_game()

    # Frame refresh
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
exit()
