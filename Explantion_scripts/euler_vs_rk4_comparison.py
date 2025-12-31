"""
Euler vs RK4 Integration Comparison for Morris-Thorne Wormhole Geodesics
========================================================================
IMPROVED VERSION: Slower animation, more dramatic differences

This script visualizes the dramatic difference between Euler's method
and Runge-Kutta 4 when integrating geodesics near a wormhole throat.

For YouTube video: "Simulating Wormholes in Python"
"""

import pygame
import numpy as np
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1400, 700  # Wide format for side-by-side
PANEL_WIDTH = WIDTH // 2
FPS = 60

# Colors
BG_COLOR = (8, 8, 18)
GRID_COLOR = (30, 35, 60)
THROAT_COLOR = (255, 255, 255)
THROAT_GLOW = (100, 100, 150)
TEXT_COLOR = (200, 200, 200)
TITLE_COLOR = (255, 255, 255)

# Euler rays - Orange/Red to show "bad"
EULER_COLOR = (255, 120, 50)
EULER_HEAD = (255, 200, 100)

# RK4 rays - Cyan/Blue to show "good"  
RK4_COLOR = (50, 200, 255)
RK4_HEAD = (150, 255, 255)

# Divergence indicator
DIVERGE_COLOR = (255, 255, 0)


class WormholeIntegrator:
    """
    Integrates geodesics in Morris-Thorne wormhole spacetime.
    """
    
    def __init__(self, b_throat):
        self.b = b_throat
    
    def derivatives(self, state):
        """
        Morris-Thorne geodesic equations:
        d²l/dτ² = l × [(dθ/dτ)² + sin²θ(dφ/dτ)²]
        
        In 2D equatorial plane (θ = π/2):
        d²l/dτ² = l × (dφ/dτ)²
        d²φ/dτ² = -(2l)/(b² + l²) × (dl/dτ)(dφ/dτ)
        """
        l, phi, vl, vphi = state
        
        # Prevent division issues at throat
        r2 = self.b ** 2 + l ** 2
        if r2 < 1e-10:
            r2 = 1e-10
        
        # Position derivatives
        dl = vl
        dphi = vphi
        
        # Acceleration from geodesic equation
        # This is where the curvature matters!
        dvl = l * (vphi ** 2)
        dvphi = -(2.0 * l / r2) * vl * vphi
        
        return np.array([dl, dphi, dvl, dvphi])
    
    def euler_step(self, state, dt):
        """Euler's method - simple but accumulates error."""
        deriv = self.derivatives(state)
        return state + dt * deriv
    
    def rk4_step(self, state, dt):
        """RK4 - much more accurate."""
        k1 = self.derivatives(state)
        k2 = self.derivatives(state + 0.5 * dt * k1)
        k3 = self.derivatives(state + 0.5 * dt * k2)
        k4 = self.derivatives(state + dt * k3)
        return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)


class RayPair:
    """
    A pair of rays - one integrated with Euler, one with RK4.
    Both start from identical initial conditions.
    """
    
    def __init__(self, l0, phi0, vl0, vphi0, color_euler, color_rk4):
        # Euler ray state
        self.euler_state = np.array([l0, phi0, vl0, vphi0], dtype=np.float64)
        self.euler_trail = [(l0, phi0)]
        
        # RK4 ray state (identical start)
        self.rk4_state = np.array([l0, phi0, vl0, vphi0], dtype=np.float64)
        self.rk4_trail = [(l0, phi0)]
        
        self.color_euler = color_euler
        self.color_rk4 = color_rk4
        self.active = True
        self.step_count = 0
        
        # Track maximum divergence for visualization
        self.max_divergence = 0
    
    def step(self, integrator, dt):
        """Perform one integration step for both methods."""
        if not self.active:
            return
        
        # Euler step
        self.euler_state = integrator.euler_step(self.euler_state, dt)
        self.euler_trail.append((self.euler_state[0], self.euler_state[1]))
        
        # RK4 step  
        self.rk4_state = integrator.rk4_step(self.rk4_state, dt)
        self.rk4_trail.append((self.rk4_state[0], self.rk4_state[1]))
        
        self.step_count += 1
        
        # Calculate divergence (difference in position)
        el, ephi = self.euler_state[0], self.euler_state[1]
        rl, rphi = self.rk4_state[0], self.rk4_state[1]
        
        # Convert to cartesian for distance
        ex, ey = el * math.cos(ephi), el * math.sin(ephi)
        rx, ry = rl * math.cos(rphi), rl * math.sin(rphi)
        divergence = math.sqrt((ex - rx)**2 + (ey - ry)**2)
        self.max_divergence = max(self.max_divergence, divergence)
        
        # Deactivate if too far from center
        if abs(self.euler_state[0]) > 350 and abs(self.rk4_state[0]) > 350:
            self.active = False
    
    def draw_euler(self, screen, center_x, center_y):
        """Draw the Euler ray trail AND the accurate RK4 ghost for comparison."""
        if len(self.rk4_trail) < 2:
            pass # We need RK4 trail for ghost
        else:
            # Draw RK4 Ghost (The "Correct" Path)
            ghost_points = []
            for l, phi in self.rk4_trail:
                x = center_x + l * math.cos(phi)
                y = center_y + l * math.sin(phi)
                ghost_points.append((x, y))
            
            if len(ghost_points) > 1:
                # Faint line for ground truth
                pygame.draw.lines(screen, (40, 60, 80), False, ghost_points, 1)

        if len(self.euler_trail) < 2:
            return
        
        points = []
        for l, phi in self.euler_trail:
            x = center_x + l * math.cos(phi)
            y = center_y + l * math.sin(phi)
            points.append((x, y))
        
        # Draw trail with gradient (fade toward tail)
        for i in range(len(points) - 1):
            # Fade from dark to bright
            t = i / max(len(points) - 1, 1)
            color = (
                int(self.color_euler[0] * (0.3 + 0.7 * t)),
                int(self.color_euler[1] * (0.3 + 0.7 * t)),
                int(self.color_euler[2] * (0.3 + 0.7 * t))
            )
            pygame.draw.line(screen, color, points[i], points[i+1], 3)
        
        # Draw head
        if self.active and len(points) > 0:
            pygame.draw.circle(screen, EULER_HEAD, 
                             (int(points[-1][0]), int(points[-1][1])), 6)
            
            # Draw ERROR CONNECTOR if we have ghost points
            if len(self.rk4_trail) > 0:
                rx = center_x + self.rk4_trail[-1][0] * math.cos(self.rk4_trail[-1][1])
                ry = center_y + self.rk4_trail[-1][0] * math.sin(self.rk4_trail[-1][1])
                
                # Draw line from Euler head to RK4 phantom head
                pygame.draw.line(screen, (100, 100, 50), (points[-1][0], points[-1][1]), (rx, ry), 1)
                
                # Draw small x on the target
                pygame.draw.line(screen, (100, 100, 50), (rx-3, ry-3), (rx+3, ry+3), 1)
                pygame.draw.line(screen, (100, 100, 50), (rx-3, ry+3), (rx+3, ry-3), 1)
    
    def draw_rk4(self, screen, center_x, center_y):
        """Draw the RK4 ray trail."""
        if len(self.rk4_trail) < 2:
            return
        
        points = []
        for l, phi in self.rk4_trail:
            x = center_x + l * math.cos(phi)
            y = center_y + l * math.sin(phi)
            points.append((x, y))
        
        # Draw trail with gradient
        for i in range(len(points) - 1):
            t = i / max(len(points) - 1, 1)
            color = (
                int(self.color_rk4[0] * (0.3 + 0.7 * t)),
                int(self.color_rk4[1] * (0.3 + 0.7 * t)),
                int(self.color_rk4[2] * (0.3 + 0.7 * t))
            )
            pygame.draw.line(screen, color, points[i], points[i+1], 3)
        
        # Draw head
        if self.active and len(points) > 0:
            pygame.draw.circle(screen, RK4_HEAD,
                             (int(points[-1][0]), int(points[-1][1])), 6)


def create_grazing_rays(throat_radius, num_rays=5):
    """
    Create rays that graze close to the throat.
    This is where the differences become most apparent!
    """
    rays = []
    
    # Start position - not too far, not too close
    start_l = throat_radius * 2.5  # Start at 2.5x throat radius
    
    # Create rays at different impact parameters
    for i in range(num_rays):
        # Vary the "aim" - some will graze closer to throat
        # Impact parameter controls how close ray passes to center
        impact_param = throat_radius * (0.8 + i * 0.4)  # Range from 0.8b to 2.4b
        
        # Starting angle
        start_phi = math.pi * 0.75  # Upper left quadrant
        
        # Calculate initial velocities to achieve desired impact parameter
        # Ray shoots roughly toward center but offset
        speed = 1.5  # Slower for better visualization
        
        # Angle offset based on impact parameter
        # Larger impact param = less direct hit
        offset_angle = math.asin(min(0.95, impact_param / start_l))
        shoot_angle = start_phi + math.pi + offset_angle * (0.5 - i * 0.15)
        
        # Convert to polar velocities
        dir_x = math.cos(shoot_angle)
        dir_y = math.sin(shoot_angle)
        pos_x = math.cos(start_phi)
        pos_y = math.sin(start_phi)
        
        vl = speed * (dir_x * pos_x + dir_y * pos_y)
        vtan = speed * (dir_y * pos_x - dir_x * pos_y)
        vphi = vtan / start_l
        
        # Color variation for each ray
        hue_shift = i * 30
        euler_color = (
            min(255, EULER_COLOR[0]),
            min(255, max(0, EULER_COLOR[1] - hue_shift)),
            min(255, EULER_COLOR[2] + hue_shift // 2)
        )
        rk4_color = (
            min(255, RK4_COLOR[0] + hue_shift // 3),
            min(255, RK4_COLOR[1]),
            min(255, max(0, RK4_COLOR[2] - hue_shift // 2))
        )
        
        ray = RayPair(start_l, start_phi, vl, vphi, euler_color, rk4_color)
        rays.append(ray)
    
    return rays


def draw_wormhole(screen, center_x, center_y, throat_radius):
    """Draw the wormhole throat with glow effect."""
    # Glow rings
    for i in range(5, 0, -1):
        alpha = 30 + i * 15
        glow_color = (THROAT_GLOW[0], THROAT_GLOW[1], THROAT_GLOW[2])
        pygame.draw.circle(screen, glow_color, 
                          (center_x, center_y), int(throat_radius + i * 4), 2)
    
    # Main throat circle
    pygame.draw.circle(screen, THROAT_COLOR, 
                      (center_x, center_y), int(throat_radius), 3)
    
    # Center dot
    pygame.draw.circle(screen, (150, 150, 200), (center_x, center_y), 3)


def draw_grid(screen, center_x, center_y):
    """Draw coordinate grid."""
    # Radial circles
    for r in range(50, 400, 50):
        pygame.draw.circle(screen, GRID_COLOR, (center_x, center_y), r, 1)
    
    # Angular lines
    for angle_deg in range(0, 360, 45):
        angle_rad = math.radians(angle_deg)
        end_x = center_x + 350 * math.cos(angle_rad)
        end_y = center_y + 350 * math.sin(angle_rad)
        pygame.draw.line(screen, GRID_COLOR, (center_x, center_y), (end_x, end_y), 1)


def draw_divergence_lines(screen, rays, euler_cx, euler_cy, rk4_cx, rk4_cy):
    """Draw lines connecting corresponding points to show divergence."""
    for ray in rays:
        if len(ray.euler_trail) > 0 and len(ray.rk4_trail) > 0:
            # Get current positions
            el, ephi = ray.euler_trail[-1]
            rl, rphi = ray.rk4_trail[-1]
            
            # Convert to screen coords (normalized to center of screen)
            # This is tricky since they're on different panels...
            # Instead, show divergence value as text
            pass


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Euler vs RK4: Wormhole Geodesic Integration Comparison")
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 32, bold=True)
    font_subtitle = pygame.font.SysFont("Arial", 18)
    font_info = pygame.font.SysFont("monospace", 14)
    font_diverge = pygame.font.SysFont("Arial", 20, bold=True)
    
    # Wormhole parameters
    throat_radius = 50.0
    integrator = WormholeIntegrator(throat_radius)
    
    # CRITICAL: Large timestep to show Euler errors
    # This is the key parameter that makes the difference visible!
    dt = 4.0  # Larger timestep = Euler fails even more visibly
    
    # Create rays that graze the throat
    rays = create_grazing_rays(throat_radius, num_rays=6)
    
    # Panel centers
    euler_cx = PANEL_WIDTH // 2
    euler_cy = HEIGHT // 2
    rk4_cx = PANEL_WIDTH + PANEL_WIDTH // 2
    rk4_cy = HEIGHT // 2
    
    # Animation control
    running = True
    paused = False
    
    # SLOW animation: only integrate every N frames
    frames_per_step = 8  # Integration happens every 8 frames
    frame_counter = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Reset
                    rays = create_grazing_rays(throat_radius, num_rays=6)
                elif event.key == pygame.K_UP:
                    dt = min(dt + 0.5, 8.0)
                elif event.key == pygame.K_DOWN:
                    dt = max(dt - 0.5, 0.5)
                elif event.key == pygame.K_LEFT:
                    frames_per_step = min(frames_per_step + 2, 30)
                elif event.key == pygame.K_RIGHT:
                    frames_per_step = max(frames_per_step - 2, 1)
            elif event.type == pygame.MOUSEWHEEL:
                throat_radius = max(20, min(120, throat_radius + event.y * 5))
                integrator.b = throat_radius
        
        # Clear screen
        screen.fill(BG_COLOR)
        
        # Update physics (slowly!)
        if not paused:
            frame_counter += 1
            if frame_counter >= frames_per_step:
                frame_counter = 0
                for ray in rays:
                    if ray.active:
                        ray.step(integrator, dt)
        
        # --- DRAW LEFT PANEL (EULER) ---
        draw_grid(screen, euler_cx, euler_cy)
        draw_wormhole(screen, euler_cx, euler_cy, throat_radius)
        
        for ray in rays:
            ray.draw_euler(screen, euler_cx, euler_cy)
        
        # Euler title
        title_euler = font_title.render("EULER METHOD", True, EULER_HEAD)
        title_euler_rect = title_euler.get_rect(center=(euler_cx, 35))
        screen.blit(title_euler, title_euler_rect)
        
        # Euler formula
        formula_euler = font_subtitle.render("x(t+Δt) = x(t) + f(x)·Δt", True, TEXT_COLOR)
        formula_euler_rect = formula_euler.get_rect(center=(euler_cx, 65))
        screen.blit(formula_euler, formula_euler_rect)
        
        bad_text = font_subtitle.render("❌ Accumulates error (Ghost line = Correct Path)", True, (255, 100, 100))
        bad_rect = bad_text.get_rect(center=(euler_cx, HEIGHT - 35))
        screen.blit(bad_text, bad_rect)
        
        # --- DRAW RIGHT PANEL (RK4) ---
        draw_grid(screen, rk4_cx, rk4_cy)
        draw_wormhole(screen, rk4_cx, rk4_cy, throat_radius)
        
        for ray in rays:
            ray.draw_rk4(screen, rk4_cx, rk4_cy)
        
        # RK4 title
        title_rk4 = font_title.render("RUNGE-KUTTA 4", True, RK4_HEAD)
        title_rk4_rect = title_rk4.get_rect(center=(rk4_cx, 35))
        screen.blit(title_rk4, title_rk4_rect)
        
        # RK4 formula
        formula_rk4 = font_subtitle.render("x(t+Δt) = x(t) + (k₁+2k₂+2k₃+k₄)/6", True, TEXT_COLOR)
        formula_rk4_rect = formula_rk4.get_rect(center=(rk4_cx, 65))
        screen.blit(formula_rk4, formula_rk4_rect)
        
        good_text = font_subtitle.render("✓ Accurate even near the throat", True, (100, 255, 150))
        good_rect = good_text.get_rect(center=(rk4_cx, HEIGHT - 35))
        screen.blit(good_text, good_rect)
        
        # --- DIVIDER ---
        pygame.draw.line(screen, (80, 80, 100), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)
        
        # --- DIVERGENCE DISPLAY ---
        max_div = max((ray.max_divergence for ray in rays), default=0)
        if max_div > 5:
            div_text = f"MAX DIVERGENCE: {max_div:.1f} px"
            div_color = (255, 255, 0) if max_div > 50 else (200, 200, 100)
            div_surf = font_diverge.render(div_text, True, div_color)
            div_rect = div_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
            
            # Background box
            pygame.draw.rect(screen, (20, 20, 40), 
                           (div_rect.x - 10, div_rect.y - 5, 
                            div_rect.width + 20, div_rect.height + 10))
            pygame.draw.rect(screen, div_color,
                           (div_rect.x - 10, div_rect.y - 5,
                            div_rect.width + 20, div_rect.height + 10), 2)
            screen.blit(div_surf, div_rect)
        
        # --- CONTROLS ---
        controls = [
            f"Δt = {dt:.1f}  (↑/↓ to change)",
            f"Speed: {frames_per_step} frames/step (←/→)",
            f"Throat: {throat_radius:.0f} (scroll)",
            "SPACE: pause | R: reset"
        ]
        for i, text in enumerate(controls):
            surf = font_info.render(text, True, (120, 120, 150))
            screen.blit(surf, (10, HEIGHT - 80 + i * 16))
        
        # Step counter
        if rays:
            steps = rays[0].step_count
            step_text = font_info.render(f"Integration steps: {steps}", True, TEXT_COLOR)
            step_rect = step_text.get_rect(center=(WIDTH//2, 95))
            screen.blit(step_text, step_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()


if __name__ == "__main__":
    main()