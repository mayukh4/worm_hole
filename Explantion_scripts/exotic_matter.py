import pygame
import math

# --- Constants & Configuration ---
WIDTH, HEIGHT = 800, 600
BG_COLOR = (10, 10, 30) # Dark space blue
GRID_COLOR = (50, 50, 100)
PARTICLE_COLOR = (255, 255, 0)
CENTER = (WIDTH // 2, HEIGHT // 2)
GRID_SPACING = 40
G = 15000  # Gravitational constant for simulation scaling
DT = 0.1   # Time step

# --- Classes ---

class Particle:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.trail = []

    def update(self, mass_pos, mass_value):
        # Calculate vector from particle to mass
        dx = mass_pos[0] - self.x
        dy = mass_pos[1] - self.y
        dist_sq = dx*dx + dy*dy + 1000 # Add a softening factor to avoid division by zero

        # F = G * M / r^2.  Direction is (dx, dy) / dist.
        # Acceleration a = F (assuming unit mass for particle)
        # a_x = (G * M * dx) / (dist_sq * sqrt(dist_sq))
        
        dist = math.sqrt(dist_sq)
        ax = G * mass_value * dx / (dist_sq * dist)
        ay = G * mass_value * dy / (dist_sq * dist)

        self.vx += ax * DT
        self.vy += ay * DT
        self.x += self.vx * DT
        self.y += self.vy * DT
        
        self.trail.append((self.x, self.y))
        if len(self.trail) > 50:
            self.trail.pop(0)

    def draw(self, surface):
        if len(self.trail) > 1:
            pygame.draw.lines(surface, PARTICLE_COLOR, False, self.trail, 2)
        pygame.draw.circle(surface, PARTICLE_COLOR, (int(self.x), int(self.y)), 5)

class SpacetimeGrid:
    def __init__(self):
        self.points = []
        for x in range(0, WIDTH + GRID_SPACING, GRID_SPACING):
            for y in range(0, HEIGHT + GRID_SPACING, GRID_SPACING):
                self.points.append({'orig_x': x, 'orig_y': y, 'x': x, 'y': y})

    def update(self, mass_pos, mass_value):
        for p in self.points:
            dx = mass_pos[0] - p['orig_x']
            dy = mass_pos[1] - p['orig_y']
            dist_sq = dx*dx + dy*dy + 5000 # Larger softening for grid stability
            
            # Displacement is proportional to force
            # We want the grid to shift *towards* positive mass, *away* from negative
            factor = G * mass_value / dist_sq * 0.5
            
            p['x'] = p['orig_x'] + dx * factor
            p['y'] = p['orig_y'] + dy * factor

    def draw(self, surface):
        for p in self.points:
            # Draw horizontal lines
            if p['orig_x'] + GRID_SPACING <= WIDTH:
                next_p = next((np for np in self.points if np['orig_x'] == p['orig_x'] + GRID_SPACING and np['orig_y'] == p['orig_y']), None)
                if next_p:
                    pygame.draw.line(surface, GRID_COLOR, (p['x'], p['y']), (next_p['x'], next_p['y']), 1)
            # Draw vertical lines
            if p['orig_y'] + GRID_SPACING <= HEIGHT:
                next_p = next((np for np in self.points if np['orig_x'] == p['orig_x'] and np['orig_y'] == p['orig_y'] + GRID_SPACING), None)
                if next_p:
                    pygame.draw.line(surface, GRID_COLOR, (p['x'], p['y']), (next_p['x'], next_p['y']), 1)

# --- Main Function ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Visualizing Spacetime Curvature")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 24)

    grid = SpacetimeGrid()
    particle = None
    
    # Simulation State
    mass_value = 1.0 # Start with positive mass
    mode_text = "Normal Matter (Positive Mass): Attractive Gravity"
    mass_color = (0, 255, 0) # Green for normal

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    mass_value = 1.0
                    mode_text = "Normal Matter (Positive Mass): Attractive Gravity"
                    mass_color = (0, 255, 0)
                elif event.key == pygame.K_n:
                    mass_value = -1.0
                    mode_text = "Exotic Matter (Negative Mass): Repulsive Gravity (Wormhole Throat)"
                    mass_color = (255, 0, 0)
                elif event.key == pygame.K_SPACE:
                    # Launch a particle from the left
                    particle = Particle(50, HEIGHT // 2 - 100, 40, 5)

        # 2. Updates
        grid.update(CENTER, mass_value)
        if particle:
            particle.update(CENTER, mass_value)
            # Remove particle if it goes off screen
            if not (0 <= particle.x <= WIDTH and 0 <= particle.y <= HEIGHT):
                particle = None

        # 3. Drawing
        screen.fill(BG_COLOR)
        grid.draw(screen)
        
        # Draw Central Mass
        pygame.draw.circle(screen, mass_color, CENTER, 20)
        
        if particle:
            particle.draw(screen)

        # Draw UI Text
        text_surface = font.render(f"MODE: {mode_text}", True, (255, 255, 255))
        screen.blit(text_surface, (20, 20))
        
        controls_surface = font.render("Controls: 'P' = Normal Matter, 'N' = Exotic Matter, 'SPACE' = Launch Particle", True, (200, 200, 200))
        screen.blit(controls_surface, (20, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()