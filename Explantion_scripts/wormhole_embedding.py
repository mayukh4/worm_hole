"""
Wormhole Embedding Diagram Visualization
========================================

Visualizes the spatial geometry of a Morris-Thorne wormhole.
The embedding diagram shows the 2D equatorial plane (t=const, theta=pi/2)
embedded in 3D Euclidean space.

Math:
Proper radial distance l ranges from -inf to +inf.
Embedding functions in cylindrical coords (r, phi, z):
r = sqrt(b^2 + l^2)
z = b * asinh(l/b)
"""

import pygame
import numpy as np
import math

# --- Constants ---
WIDTH, HEIGHT = 900, 700
BG_COLOR = (10, 10, 20)
GRID_COLOR_1 = (50, 200, 255)  # Cyan for "upper" universe
GRID_COLOR_2 = (255, 100, 50)  # Orange for "lower" universe
THROAT_COLOR = (255, 255, 255)

# Camera/View parameters
FOV = 500
VIEW_DIST = 4.0

class Camera:
    def __init__(self):
        self.pos = np.array([0.0, -20.0, 0.0]) # Look from side/top
        self.rot = np.array([0.0, 0.0]) # Pitch, Yaw (no roll)
        self.zoom = 1.0

def project_point(point, width, height, scale, rot_x, rot_y):
    """
    Project 3D point (x, y, z) to 2D screen (sx, sy).
    Simple rotation + perspective projection.
    """
    x, y, z = point
    
    # Rotation around Y axis (Yaw)
    rx = x * math.cos(rot_y) - z * math.sin(rot_y)
    rz = x * math.sin(rot_y) + z * math.cos(rot_y)
    x, z = rx, rz
    
    # Rotation around X axis (Pitch)
    ry = y * math.cos(rot_x) - z * math.sin(rot_x)
    rz = y * math.sin(rot_x) + z * math.cos(rot_x)
    y, z = ry, rz
    
    # Perspective
    factor = FOV / (FOV + z * scale + 400) # Simple perspective fudge
    
    sx = width // 2 + int(x * scale * factor)
    sy = height // 2 + int(y * scale * factor)
    
    return (sx, sy), scale * factor

def generate_wormhole_mesh(b, l_max, l_steps, phi_steps):
    """
    Generate vertices for the embedding diagram.
    l: proper radial distance (-l_max to +l_max)
    phi: azimuthal angle (0 to 2pi)
    """
    vertices = []
    connections = [] # List of ((i1, j1), (i2, j2)) to draw lines
    
    l_vals = np.linspace(-l_max, l_max, l_steps)
    phi_vals = np.linspace(0, 2*math.pi, phi_steps)
    
    grid = []
    
    for i, l in enumerate(l_vals):
        row = []
        # Embedding formulas
        # r = sqrt(b^2 + l^2)
        # z = b * asinh(l/b)
        
        r = math.sqrt(b**2 + l**2)
        z = b * math.asinh(l/b)
        
        for j, phi in enumerate(phi_vals):
            # Convert cylindrical (r, phi, z) to Cartesian (x, y, z)
            # Note: We swap axes to make it look upright.
            # Usually z is up. Let's make y up in screen coords.
            
            x = r * math.cos(phi)
            z_coord = r * math.sin(phi) # Depth
            y = -z # Vertical axis of the wormhole (embedding dimension)
            
            row.append((x, y, z_coord, l)) # Store l to know which universe
        grid.append(row)
        
    return grid

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Morris-Thorne Wormhole Embedding Diagram")
    clock = pygame.time.Clock()
    
    # Wormhole params
    b = 1.0  # Throat radius (normalized)
    l_max = 3.0
    l_steps = 25
    phi_steps = 24
    
    # View params
    rot_x = 0.3 # Tilt down slightly
    rot_y = 0.0
    scale = 100.0
    
    # Auto rotate
    auto_rotate = True
    
    font = pygame.font.SysFont("monospace", 14)
    
    while True:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    auto_rotate = not auto_rotate
                elif event.key == pygame.K_r:
                    rot_x, rot_y = 0.3, 0.0
            elif event.type == pygame.MOUSEWHEEL:
                scale = max(20, min(300, scale + event.y * 5))
        
        # Mouse control
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_rel()
            rot_y += mx * 0.01
            rot_x += my * 0.01
            auto_rotate = False
        else:
            pygame.mouse.get_rel() # flush
        
        if auto_rotate:
            rot_y += 0.5 * dt
        
        # Clear
        screen.fill(BG_COLOR)
        
        # Generate mesh (cheap enough to do basically every frame or just once)
        # We recalculate projection every frame
        grid = generate_wormhole_mesh(b, l_max, l_steps, phi_steps)
        
        # Draw Mesh
        # We draw longitudinal lines (lines of constant phi)
        # and latitudinal lines (circles, lines of constant l)
        
        # Draw Radial Lines (along l)
        for j in range(phi_steps):
            points = []
            for i in range(l_steps):
                p_3d = grid[i][j][:3]
                l_val = grid[i][j][3]
                pt_2d, _ = project_point(p_3d, WIDTH, HEIGHT, scale, rot_x, rot_y)
                points.append((pt_2d, l_val))
            
            # Draw strips
            for k in range(len(points) - 1):
                p1, l1 = points[k]
                p2, l2 = points[k+1]
                
                # Color based on universe (-l vs +l)
                if l1 < -0.1: color = GRID_COLOR_2 # Lower
                elif l1 > 0.1: color = GRID_COLOR_1 # Upper
                else: color = THROAT_COLOR # Throat
                
                pygame.draw.line(screen, color, p1, p2, 1)
        
        # Draw Circles (along phi)
        for i in range(l_steps):
            points = []
            l_val = grid[i][0][3]
            for j in range(phi_steps):
                p_3d = grid[i][j][:3]
                pt_2d, _ = project_point(p_3d, WIDTH, HEIGHT, scale, rot_x, rot_y)
                points.append(pt_2d)
            
            # Close the circle
            p_3d_start = grid[i][0][:3]
            pt_2d_start, _ = project_point(p_3d_start, WIDTH, HEIGHT, scale, rot_x, rot_y)
            points.append(pt_2d_start)
            
            # Color
            if l_val < -0.1: color = GRID_COLOR_2
            elif l_val > 0.1: color = GRID_COLOR_1
            else: color = THROAT_COLOR
            
            # Draw circle
            pygame.draw.lines(screen, color, False, points, 1)

        # UI
        text1 = font.render(f"Throat Radius: {b}", True, (150, 150, 150))
        text2 = font.render("Drag to Rotate | Scroll to Zoom | Space: Pause", True, (150, 150, 150))
        screen.blit(text1, (10, 10))
        screen.blit(text2, (10, 30))
        
        pygame.display.flip()

if __name__ == "__main__":
    main()
