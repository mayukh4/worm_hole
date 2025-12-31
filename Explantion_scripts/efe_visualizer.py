"""
Einstein Field Equations - 3D Visualizer
========================================
"Matter tells Spacetime how to curve."

A 3D interactive "rubber sheet" visualization.
- Move the RED BALL (Mass) with your mouse.
- Press 'W' to increase Mass (make it bigger/heavier).
- Press 'S' to decrease Mass.
- Observe how the grid curves (Equation: G_uv ~ T_uv).
"""

import pygame
import numpy as np
import math

# --- Constants ---
WIDTH, HEIGHT = 1200, 800
BG_COLOR = (10, 10, 15)
GRID_COLOR = (40, 60, 100)
GRID_WARPED_COLOR = (60, 100, 200)
MASS_COLOR = (255, 50, 50) # Red ball
TEXT_COLOR = (220, 220, 220)

# Camera / Projection
FOV = 600
VIEW_DIST = 500
CAM_HEIGHT = -300 # Looking down from above
CAM_PITCH = 0.5   # Tilted down

class Spacetime3D:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("General Relativity: Spacetime Curvature")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20)
        self.font_big = pygame.font.SysFont("Times New Roman", 32, italic=True)

        # Grid params
        self.grid_size = 20 # 20x20 grid
        self.spacing = 40
        self.grid_width = self.grid_size * self.spacing
        self.grid_depth = self.grid_size * self.spacing
        
        # Mass params
        self.mass_pos = np.array([0.0, 0.0]) # x, z (y is up/down)
        self.mass_val = 50.0 # Controls curvature and size radius
        
        # Precompute base grid (x, z)
        self.base_points = []
        for i in range(self.grid_size + 1):
            for j in range(self.grid_size + 1):
                x = (i - self.grid_size/2) * self.spacing
                z = (j - self.grid_size/2) * self.spacing
                self.base_points.append((x, z))

    def project(self, point_3d):
        """Project 3D world point to 2D screen."""
        x, y, z = point_3d
        
        # Simple camera translation
        # Camera is at (0, CAM_HEIGHT, -VIEW_DIST) looking at (0, 0, 0)
        # But let's keep it simple: rotate world then project
        
        # Rotate around X axis (Pitch)
        # y' = y*cos - z*sin
        # z' = y*sin + z*cos
        
        # Shift relative to camera
        z_cam = z + VIEW_DIST
        y_cam = y - CAM_HEIGHT
        
        # Rotate (pitch down)
        rx = x
        ry = y_cam * math.cos(CAM_PITCH) - z_cam * math.sin(CAM_PITCH)
        rz = y_cam * math.sin(CAM_PITCH) + z_cam * math.cos(CAM_PITCH)
        
        if rz <= 10: return None # Behind camera
        
        scale = FOV / rz
        screen_x = WIDTH//2 + int(rx * scale)
        screen_y = HEIGHT//2 + int(ry * scale)
        
        return (screen_x, screen_y)

    def get_curvature_depth(self, x, z):
        """Calculate y-displacement based on mass position."""
        dx = x - self.mass_pos[0]
        dz = z - self.mass_pos[1]
        dist_sq = dx*dx + dz*dz
        dist = math.sqrt(dist_sq)
        
        # Lorentzian-like dip: M / (1 + r^2/a^2)
        # We want positive depth to go DOWN on screen (since Y+ is down-ish in our view)
        width_param = 60.0 + self.mass_val 
        depth = (self.mass_val * 8.0) / (1.0 + dist_sq / (width_param**2))
        
        return depth

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Input
            mx, my = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.mass_val = min(self.mass_val + 5, 200)
                    elif event.key == pygame.K_s:
                        self.mass_val = max(self.mass_val - 5, 10)
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                 self.mass_val = min(self.mass_val + 2, 200)
            if keys[pygame.K_s]:
                 self.mass_val = max(self.mass_val - 2, 10)

            # Map Mouse to Ground Plane (Raycasting approx)
            # Center of screen is (0, 0, 0)
            # Simple approximation: map screen X to world X, screen Y to world Z
            # This is not perfect due to perspective but good enough for controls
            
            # Better approach: 
            # We want to move mass on the X-Z plane.
            # Screen center = (0,0,0).
            rel_x = (mx - WIDTH//2) 
            rel_y = (my - HEIGHT//2)
            
            # Sensitive tuning for "feeling" right
            self.mass_pos[0] = rel_x * 1.5
            self.mass_pos[1] = rel_y * 1.5 + 100 # Offset z slightly
            
            # --- RENDER ---
            self.screen.fill(BG_COLOR)
            
            # Calculate grid vertices
            warped_points = []
            for x, z in self.base_points:
                y = self.get_curvature_depth(x, z)
                warped_points.append((x, y, z))
                
            # Draw Grid Lines
            # Row-wise
            for i in range(self.grid_size + 1):
                row_pts_2d = []
                for j in range(self.grid_size + 1):
                    idx = i * (self.grid_size + 1) + j
                    p3 = warped_points[idx]
                    p2 = self.project(p3)
                    if p2: row_pts_2d.append(p2)
                if len(row_pts_2d) > 1:
                     pygame.draw.lines(self.screen, GRID_WARPED_COLOR, False, row_pts_2d, 1)

            # Col-wise
            for j in range(self.grid_size + 1):
                col_pts_2d = []
                for i in range(self.grid_size + 1):
                    idx = i * (self.grid_size + 1) + j
                    p3 = warped_points[idx]
                    p2 = self.project(p3)
                    if p2: col_pts_2d.append(p2)
                if len(col_pts_2d) > 1:
                     pygame.draw.lines(self.screen, GRID_WARPED_COLOR, False, col_pts_2d, 1)

            # Draw Mass (Red Ball)
            # Position at the BOTTOM of the well
            ball_y = self.get_curvature_depth(self.mass_pos[0], self.mass_pos[1])
            ball_pos_3d = (self.mass_pos[0], ball_y, self.mass_pos[1])
            ball_center = self.project(ball_pos_3d)
            
            if ball_center:
                # Radius scales with perspective AND mass
                # Base size roughly proportional to mass
                base_radius = self.mass_val * 0.4
                # Perspective scaling
                z_depth = ball_pos_3d[2] + VIEW_DIST
                if z_depth < 1.0: z_depth = 1.0 # Prevent div by zero
                scale_factor = FOV / z_depth
                draw_radius = int(base_radius * scale_factor)
                if draw_radius < 5: draw_radius = 5
                if draw_radius > 1000: draw_radius = 1000 # Clamp to prevent segfault on Surface alloc
                
                # Draw Glow
                glow_surf = pygame.Surface((draw_radius*4, draw_radius*4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 50, 50, 50), (draw_radius*2, draw_radius*2), draw_radius*1.5)
                self.screen.blit(glow_surf, (ball_center[0] - draw_radius*2, ball_center[1] - draw_radius*2))
                
                # Draw Sphere
                pygame.draw.circle(self.screen, MASS_COLOR, ball_center, draw_radius)
                
                # Highlight
                pygame.draw.circle(self.screen, (255, 150, 150), (ball_center[0] - draw_radius//3, ball_center[1] - draw_radius//3), draw_radius//4)

            # UI / Text
            title = self.font_big.render("G_uv = 8πT_uv", True, TEXT_COLOR)
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
            
            sub = self.font.render("Mass tells Spacetime how to curve.", True, (150, 150, 200))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 70))
            
            ctrls = self.font.render(f"Mass: {self.mass_val:.0f} (W/S to Resize) | Mouse to Move", True, (100, 200, 100))
            self.screen.blit(ctrls, (10, HEIGHT - 30))

            pygame.display.flip()
            
        pygame.quit()

if __name__ == "__main__":
    app = Spacetime3D()
    app.run()
