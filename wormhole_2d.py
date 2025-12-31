import pygame
import numpy as np
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1000, 800
FPS = 60
BG_COLOR = (10, 10, 20)
RAY_COLOR_OURS = (100, 200, 255)  # Cyan for our universe
RAY_COLOR_THEIRS = (255, 50, 50)  # Red for the other universe
THROAT_COLOR = (255, 255, 255)
GRID_COLOR = (40, 45, 80)
TEXT_COLOR = (200, 200, 200)

# --- PHYSICS CONSTANTS ---
C = 1.0  # Speed of light (normalized)
# B is the throat size, we will make this adjustable

class GeodesicIntegrator:
    def __init__(self, b_throat):
        self.b = b_throat

    def derivatives(self, state):
        """
        Calculates derivatives [dr/dt, dphi/dt, dvr/dt, dvphi/dt]
        Based on Morris-Thorne Metric Geodesics (Page 11 of PDF)
        Assumes theta = pi/2 (Equatorial plane)
        """
        r, phi, vr, vphi = state
        
        # Equation 1: dr/dtau = vr
        dr = vr
        
        # Equation 2: dphi/dtau = vphi
        dp = vphi
        
        # Equation 3: Acceleration in r
        # d^2r/dtau^2 = r * (dphi/dtau)^2
        # (This implies a centrifugal-like force pushing away from r=0)
        dvr = r * (vphi ** 2)
        
        # Equation 4: Acceleration in phi
        # d^2phi/dtau^2 = - (2r / (b^2 + r^2)) * dr/dtau * dphi/dtau
        denominator = (self.b ** 2 + r ** 2)
        dvp = - (2 * r / denominator) * vr * vphi
        
        return np.array([dr, dp, dvr, dvp])

    def rk4_step(self, state, dt):
        """Runge-Kutta 4 Integration Step"""
        k1 = self.derivatives(state)
        k2 = self.derivatives(state + 0.5 * dt * k1)
        k3 = self.derivatives(state + 0.5 * dt * k2)
        k4 = self.derivatives(state + dt * k3)
        return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wormhole Geodesic Lab (2D)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    # Simulation State
    b_radius = 60.0  # Initial throat size
    integrator = GeodesicIntegrator(b_radius)
    
    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                b_radius += event.y * 5
                b_radius = max(10, min(b_radius, 200))
                integrator.b = b_radius

        # 2. Update Physics based on Mouse
        mx, my = pygame.mouse.get_pos()
        
        # Calculate ray start position relative to center
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        start_x, start_y = mx - center_x, my - center_y
        
        # Convert Cartesian (x,y) to Polar (r, phi)
        r0 = math.sqrt(start_x**2 + start_y**2)
        phi0 = math.atan2(start_y, start_x)
        
        # Initial Velocity: Shoot TOWARDS the center
        # We want speed c. Velocity vector points opposite to position vector.
        # Let's add a slight offset so we can "miss" the center if we want
        speed = 5.0 # Simulation speed factor
        vr0 = -speed # Moving inwards
        vphi0 = 0.5 / r0 # Small angular velocity (impact parameter)
        
        # To make it interactive like a flashlight, let's shoot a FAN of rays
        rays = []
        num_rays = 15
        spread = 0.3 # Radians spread
        
        base_angle = math.atan2(-start_y, -start_x) # Pointing at center
        
        for i in range(num_rays):
            angle_offset = (i - num_rays//2) * (spread/num_rays)
            shoot_angle = base_angle + angle_offset
            
            # Convert shoot direction to vr, vphi
            # Vr is projection of velocity onto radial vector
            # Vphi is projection onto tangential vector divided by r
            
            # Unit vector of ray direction
            dir_x = math.cos(shoot_angle)
            dir_y = math.sin(shoot_angle)
            
            # Unit vector of position (radial)
            pos_x = start_x / r0
            pos_y = start_y / r0
            
            # Project velocity
            vr_initial = speed * (dir_x * pos_x + dir_y * pos_y)
            vtan_initial = speed * (dir_y * pos_x - dir_x * pos_y) # Cross product 2D
            vphi_initial = vtan_initial / r0  # angular velocity = v_tan / r
            
            rays.append(np.array([r0, phi0, vr_initial, vphi_initial]))

        # 3. Drawing
        screen.fill(BG_COLOR)
        
        # Draw Coordinate Grid (Background)
        # Circular grid lines
        for r in range(50, 1500, 50):
            pygame.draw.circle(screen, GRID_COLOR, (center_x, center_y), r, 1)
        
        # Radial grid lines
        for angle_deg in range(0, 360, 15):
            angle_rad = math.radians(angle_deg)
            end_x = center_x + 1500 * math.cos(angle_rad)
            end_y = center_y + 1500 * math.sin(angle_rad)
            pygame.draw.line(screen, GRID_COLOR, (center_x, center_y), (end_x, end_y), 1)

        # Trace Rays
        for state in rays:
            points = []
            crossed_throat = False
            
            # Trace for 500 steps
            for _ in range(500):
                # Convert Polar back to Cartesian for drawing
                # Note: This is a visualization trick. 
                # If r < 0, we are in the "other" universe. 
                # We will draw r<0 as being "inside" the throat circle visually, 
                # or we can flip it. Let's just draw raw coordinates.
                
                px = center_x + state[0] * math.cos(state[1])
                py = center_y + state[0] * math.sin(state[1])
                points.append((px, py))
                
                # Check crossing
                if state[0] < 0:
                    crossed_throat = True

                # Step Physics
                state = integrator.rk4_step(state, 1.0)
                
                # Stop if too far away
                if state[0] > 1000:
                    break
            
            if len(points) > 1:
                # Color logic: If the ray ends up with r < 0, it went through.
                color = RAY_COLOR_THEIRS if crossed_throat else RAY_COLOR_OURS
                pygame.draw.lines(screen, color, False, points, 2)

        # Draw the Throat (The "Wormhole" entrance)
        pygame.draw.circle(screen, THROAT_COLOR, (center_x, center_y), int(b_radius), 2)
        
        # UI Text
        info = [
            f"Metric: Morris-Thorne Wormhole",
            f"Throat Radius (b): {int(b_radius)} (Scroll to change)",
            f"Mouse: Move light source",
            f"Cyan: Reflected (Our Universe)",
            f"Red: Transmitted (Other Universe)"
        ]
        for i, line in enumerate(info):
            text = font.render(line, True, TEXT_COLOR)
            screen.blit(text, (10, 10 + i * 20))

        # Draw User Mouse Position
        pygame.draw.circle(screen, (255, 255, 0), (mx, my), 5)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()
    