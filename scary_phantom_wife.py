import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60
TILE_SIZE = 40

# Colors (Aesthetic: Dark background, neon purple/cyan accents)
BLACK = (15, 10, 20)
NEON_PURPLE = (176, 38, 255)
NEON_CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
DARK_PURPLE = (60, 10, 90)
WALL_COLOR = (25, 20, 50)
TEXT_COLOR = (200, 200, 255)

# Maze Layout (1 for wall, 0 for path)
MAZE = [
    "11111111111111111111",
    "10000000000000000001",
    "10111011111111011101",
    "10100000011000000101",
    "10101111011011110101",
    "10001000000000010001",
    "11101011100111010111",
    "10000010000001000001",
    "10111110111101111101",
    "10000000000000000001",
    "10111011111111011101",
    "10001000011000010001",
    "11101111011011110111",
    "10000000000000000001",
    "11111111111111111111"
]

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 14
        self.speed = 4
        self.color = NEON_PURPLE
        self.phasing = False
        self.phase_meter = 100.0
        self.phase_max = 100.0
        self.phase_drain_rate = 1.0
        self.phase_recharge_rate = 0.3
        
    def update(self, keys, walls):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            
        # Phasing logic
        if keys[pygame.K_SPACE] and self.phase_meter > 0:
            self.phasing = True
            self.phase_meter -= self.phase_drain_rate
        else:
            self.phasing = False
            if self.phase_meter < self.phase_max:
                self.phase_meter += self.phase_recharge_rate
                
        if self.phase_meter < 0:
            self.phase_meter = 0
            self.phasing = False

        # Proposed move
        new_rect = pygame.Rect(self.x + dx - self.radius, self.y + dy - self.radius, self.radius*2, self.radius*2)
        
        # Collision detection with walls
        collision = False
        if not self.phasing:  # Core Mechanic: Bypass wall collision while phasing
            for wall in walls:
                if new_rect.colliderect(wall):
                    collision = True
                    break
                    
        # Boundary collision is absolute and cannot be phased through
        if new_rect.left < 0 or new_rect.right > WIDTH or new_rect.top < 0 or new_rect.bottom > HEIGHT:
            collision = True
            
        if not collision:
            self.x += dx
            self.y += dy

    def draw(self, surface):
        draw_color = DARK_PURPLE if self.phasing else NEON_PURPLE
        pygame.draw.circle(surface, draw_color, (int(self.x), int(self.y)), self.radius)
        if self.phasing:
            # Aura effect while passing through walls
            pygame.draw.circle(surface, NEON_PURPLE, (int(self.x), int(self.y)), self.radius + 4, 3)

class Enemy:
    def __init__(self, x, y, ai_type="random"):
        self.x = x
        self.y = y
        self.radius = 16
        self.speed = 2.5
        self.color = YELLOW
        self.ai_type = ai_type
        self.original_ai = ai_type
        self.direction = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
        
    def check_wall_collision(self, dx, dy, walls):
        new_rect = pygame.Rect(self.x + dx - self.radius + 2, self.y + dy - self.radius + 2, self.radius*2 - 4, self.radius*2 - 4)
        for wall in walls:
            if new_rect.colliderect(wall):
                return True
        if new_rect.left < 0 or new_rect.right > WIDTH or new_rect.top < 0 or new_rect.bottom > HEIGHT:
            return True
        return False
        
    def update(self, player, walls):
        if self.ai_type == "follow":
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx, dy = dx / dist, dy / dist
                move_x = dx * self.speed
                move_y = dy * self.speed
                
                # Pathfinding - priority: compound -> x-axis only -> y-axis only -> random fallback
                if not self.check_wall_collision(move_x, move_y, walls):
                    self.x += move_x
                    self.y += move_y
                elif not self.check_wall_collision(move_x, 0, walls):
                    self.x += move_x
                elif not self.check_wall_collision(0, move_y, walls):
                    self.y += move_y
                else:
                    self.ai_type = "random" 
        
        elif self.ai_type == "random":
            move_x = self.direction[0] * self.speed
            move_y = self.direction[1] * self.speed
            
            if self.check_wall_collision(move_x, move_y, walls):
                valid_dirs = []
                for d in [(1,0), (-1,0), (0,1), (0,-1)]:
                    if not self.check_wall_collision(d[0]*self.speed, d[1]*self.speed, walls):
                        valid_dirs.append(d)
                if valid_dirs:
                    self.direction = random.choice(valid_dirs)
                else:
                    self.direction = (0,0)
                    
            self.x += self.direction[0] * self.speed
            self.y += self.direction[1] * self.speed
            
            if self.original_ai == "follow" and random.random() < 0.02:
                 self.ai_type = "follow" # Blinky regains senses occasionally when stuck

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Pac-Hunters mouth abstraction
        mouth = [(int(self.x), int(self.y)), 
                 (int(self.x + self.radius), int(self.y - self.radius/2)), 
                 (int(self.x + self.radius), int(self.y + self.radius/2))]
        pygame.draw.polygon(surface, BLACK, mouth)

def main():
    walls = []
    ectoplasms = []
    
    for r, row in enumerate(MAZE):
        for c, col in enumerate(row):
            rx = c * TILE_SIZE
            ry = r * TILE_SIZE
            if col == '1':
                walls.append(pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE))
            elif col == '0':
                ectoplasm = pygame.Rect(rx + TILE_SIZE//2 - 4, ry + TILE_SIZE//2 - 4, 8, 8)
                ectoplasms.append(ectoplasm)
                
    player = Player(TILE_SIZE * 1.5, TILE_SIZE * 1.5)
    
    enemies = [
        Enemy(WIDTH - TILE_SIZE * 1.5, HEIGHT - TILE_SIZE * 1.5, "follow"),  # Blinky
        Enemy(WIDTH - TILE_SIZE * 1.5, TILE_SIZE * 1.5, "random")            # Inky
    ]
    
    state = "PLAYING"
    font_large = pygame.font.SysFont("Arial", 48, bold=True)
    font_small = pygame.font.SysFont("Arial", 24)
    font_tiny  = pygame.font.SysFont("Arial", 14, bold=True)
    
    running = True
    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and state in ["WIN", "LOSS"]:
                    main()
                    return
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        if state == "PLAYING":
            player.update(keys, walls)
            
            for enemy in enemies:
                enemy.update(player, walls)
                
            # Collect Ectoplasm
            player_rect = pygame.Rect(player.x - player.radius, player.y - player.radius, player.radius*2, player.radius*2)
            
            # Identify collected ectoplasms
            for e_rect in ectoplasms[:]:
                if player_rect.colliderect(e_rect):
                    ectoplasms.remove(e_rect)
                    print('\a', end='', flush=True) # System beep!
                    
            if not ectoplasms:
                state = "WIN"
                
            # Enemy tracking/collision
            for enemy in enemies:
                dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
                # Distance threshold slightly smaller than combined radii to be fair
                if dist < (player.radius + enemy.radius - 6):
                    state = "LOSS"
            
        # --- DRAWING ---
        screen.fill(BLACK)
        
        # Walls
        for wall in walls:
            pygame.draw.rect(screen, WALL_COLOR, wall)
            pygame.draw.rect(screen, NEON_PURPLE, wall, 1) # Neon grid effect
            
        # Collectibles
        for e in ectoplasms:
            pygame.draw.rect(screen, NEON_CYAN, e)
            
        # Entities
        player.draw(screen)
        
        for enemy in enemies:
            enemy.draw(screen)
            
        # UI Rendering - Phase Meter
        meter_w = 200
        pygame.draw.rect(screen, WALL_COLOR, (10, 10, meter_w, 20))
        fill_w = max(0, (player.phase_meter / player.phase_max) * meter_w)
        pygame.draw.rect(screen, NEON_PURPLE if not player.phasing else DARK_PURPLE, (10, 10, fill_w, 20))
        pygame.draw.rect(screen, TEXT_COLOR, (10, 10, meter_w, 20), 2)
        
        phase_text = font_tiny.render("PHASE METER (SPACE)", True, TEXT_COLOR)
        screen.blit(phase_text, (10 + meter_w/2 - phase_text.get_width()/2, 12))
        
        # Score Tracking
        score_text = font_small.render(f"Ectoplasms: {len(ectoplasms)}", True, TEXT_COLOR)
        screen.blit(score_text, (WIDTH - 180, 10))
        
        # Win / Loss Overlays
        if state == "WIN":
            win_surf = font_large.render("YOU SURVIVED!", True, NEON_CYAN)
            sub_surf = font_small.render("Press R to Restart | ESC to Quit", True, TEXT_COLOR)
            screen.blit(win_surf, (WIDTH//2 - win_surf.get_width()//2, HEIGHT//2 - 30))
            screen.blit(sub_surf, (WIDTH//2 - sub_surf.get_width()//2, HEIGHT//2 + 30))
            
        elif state == "LOSS":
            loss_surf = font_large.render("BUSTED BY THE HUNTERS!", True, NEON_PURPLE)
            sub_surf = font_small.render("Press R to Restart | ESC to Quit", True, TEXT_COLOR)
            screen.blit(loss_surf, (WIDTH//2 - loss_surf.get_width()//2, HEIGHT//2 - 30))
            screen.blit(sub_surf, (WIDTH//2 - sub_surf.get_width()//2, HEIGHT//2 + 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
