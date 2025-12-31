import pygame
import numpy as np
import math
import random

# --- Constants & Configuration ---
WIDTH, HEIGHT = 1000, 800
BACKGROUND_COLOR = (5, 5, 10)    # Deep space black/blue
GLOBE_COLOR = (50, 200, 250)     # Cyan/Blue wireframe
GLOBE_BACK_COLOR = (20, 60, 80)  # Darker blue for back-facing lines (optional)
PATH_COLOR = (255, 60, 60)       # Bright Red
PLANE_COLOR = (255, 220, 0)      # Gold/Yellow
TEXT_COLOR = (255, 255, 255)

RADIUS = 250         # Base Radius of the globe
ROTATION_SPEED = 0.005
FOV = 800            # Field of view
EARTH_RADIUS_KM = 6371 # For distance calc

# --- Mathematical Functions ---

def latlon_to_cartesian(lat, lon, radius):
    """
    Converts Latitude and Longitude to 3D Cartesian (x, y, z) coordinates.
    lat: -90 to 90
    lon: -180 to 180
    """
    phi = np.radians(90 - lat)
    theta = np.radians(lon)
    
    x = radius * np.sin(phi) * np.cos(theta)
    y = radius * np.cos(phi)
    z = radius * np.sin(phi) * np.sin(theta)
    return np.array([x, y, z])

def rotation_matrix_x(angle):
    """Returns 3x3 rotation matrix for X-axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[1, 0, 0],
                     [0, c, -s],
                     [0, s, c]])

def rotation_matrix_y(angle):
    """Returns 3x3 rotation matrix for Y-axis."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0, s],
                     [0, 1, 0],
                     [-s, 0, c]])

def project_point(point, width, height, fov, viewer_dist, radius):
    """
    Projects a 3D point (x, y, z) to 2D screen coordinates.
    """
    x, y, z = point
    # Camera is at (0, 0, viewer_dist * radius) looking at (0, 0, 0)
    # Z coordinate increases towards the viewer in standard OpenGL, but here typical math 
    # uses Z as up or depth. Let's assume standard right-handed system visually:
    # We push the object away so it's in front of camera.
    
    # Distance from camera to point z.
    # If viewer is at Z_cam = viewer_dist * RADIUS
    # And point is at z
    # Depth = Z_cam - z
    depth = (viewer_dist * radius) - z
    
    if depth <= 1: # Avoid division by zero or behind camera
        return width // 2, height // 2, 0

    scale = fov / depth
    
    px = x * scale + width / 2
    py = y * scale + height / 2
    return int(px), int(py), scale

def slerp(p0, p1, t):
    """
    Spherical Linear Interpolation (SLERP).
    """
    p0 = p0 / np.linalg.norm(p0)
    p1 = p1 / np.linalg.norm(p1)
    
    dot = np.dot(p0, p1)
    dot = np.clip(dot, -1.0, 1.0)
    
    omega = np.arccos(dot)
    
    if np.isclose(omega, 0):
        return p0
        
    sin_omega = np.sin(omega)
    
    term1 = np.sin((1 - t) * omega) / sin_omega
    term2 = np.sin(t * omega) / sin_omega
    
    return term1 * p0 + term2 * p1

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates distance in km between two lat/lon points.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return EARTH_RADIUS_KM * c

# --- Main Simulation Class ---

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Geodesic Flight Path Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.title_font = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Simulation State
        self.angle_x = 0.5
        self.angle_y = 0.0
        self.dragging = False
        self.prev_mouse = (0, 0)
        self.viewer_dist = 4.0 # Initial zoom level
        
        # Define Route: New York -> Tokyo
        self.start_latlon = (40.71, -74.00) # NY
        self.end_latlon = (35.67, 139.65)   # Tokyo
        
        self.p_start = latlon_to_cartesian(*self.start_latlon, RADIUS)
        self.p_end = latlon_to_cartesian(*self.end_latlon, RADIUS)
        
        # 1. Generate Geodesic Path (Shortest Curve)
        self.geodesic_points = []
        self.geodesic_dist = 0
        steps = 100
        
        # We calculate total distance along the way
        prev_ll = self.start_latlon
        
        for i in range(steps + 1):
            t = i / steps
            pt = slerp(self.p_start, self.p_end, t) * RADIUS 
            self.geodesic_points.append(pt)
            
        self.geodesic_dist = haversine_distance(*self.start_latlon, *self.end_latlon)

        # 2. Generate "Map Path" (Rhumb-like / Linear Lat-Lon)
        # This represents the "Straight line on a map"
        self.map_points = []
        self.map_dist = 0
        
        lat1, lon1 = self.start_latlon
        lat2, lon2 = self.end_latlon
        
        # Handle wrapping for shortest map visual (Crossing Pacific)
        # NY(-74) to Tokyo(139).
        # Diff going East: 213. Diff going West: 147.
        # So we should interpolate Lon from -74 down to (139 - 360) = -221.
        target_lon = lon2
        if lon2 - lon1 > 180:
            target_lon -= 360
        elif lon1 - lon2 > 180:
            target_lon += 360

        dLat = lat2 - lat1
        dLon = target_lon - lon1
        
        prev_p_ll = (lat1, lon1)
        
        for i in range(steps + 1):
            t = i / steps
            curr_lat = lat1 + dLat * t
            curr_lon = lon1 + dLon * t
            
            pt = latlon_to_cartesian(curr_lat, curr_lon, RADIUS)
            self.map_points.append(pt)
            
            # Add to total distance
            # Note: We must normalize lon for haversine
            norm_lon = curr_lon
            # Simple normalization
            while norm_lon < -180: norm_lon += 360
            while norm_lon > 180: norm_lon -= 360
            
            if i > 0:
                dist_seg = haversine_distance(prev_p_ll[0], prev_p_ll[1], curr_lat, norm_lon)
                self.map_dist += dist_seg
            prev_p_ll = (curr_lat, norm_lon)
            
        # Plane animation
        self.plane_t = 0.0
        self.plane_speed = 0.005
        
        # Generate Stars
        self.stars = []
        for _ in range(200):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, HEIGHT)
            brightness = random.randint(50, 255)
            self.stars.append((sx, sy, brightness))

        # Globe Grid
        self.globe_points = []
        # Longitude lines
        for lon in range(0, 360, 15): # More dense for better look? Or keep simple. 30 is fine.
            line = []
            for lat in range(-90, 91, 5):
                line.append(latlon_to_cartesian(lat, lon, RADIUS))
            self.globe_points.append(line)
        # Latitude lines
        for lat in range(-80, 81, 15):
            line = []
            for lon in range(0, 361, 5):
                line.append(latlon_to_cartesian(lat, lon, RADIUS))
            self.globe_points.append(line)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Zoom Logic
            elif event.type == pygame.MOUSEWHEEL:
                self.viewer_dist -= event.y * 0.1
                # Clamp zoom
                self.viewer_dist = max(2.5, min(self.viewer_dist, 10.0))
            
            # Rotation Logic
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging = True
                    self.prev_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mx, my = event.pos
                    dx = mx - self.prev_mouse[0]
                    dy = my - self.prev_mouse[1]
                    self.angle_y += dx * 0.005
                    self.angle_x += dy * 0.005
                    self.prev_mouse = (mx, my)
        return True

    def update(self):
        self.plane_t += self.plane_speed
        if self.plane_t > 1.0:
            self.plane_t = 0.0

    def draw_atmosphere(self, center_x, center_y, radius):
        # Create a glow effect
        # Simple radical gradient using alpha surfaces
        glow_radius = int(radius * 1.2)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        
        # Draw concentric varying alpha circles
        for r in range(glow_radius, int(radius * 0.9), -2):
            alpha = int(100 * (1 - (r - radius) / (glow_radius - radius))) if r > radius else 50
            alpha = max(0, min(alpha, 100))
            pygame.draw.circle(glow_surface, (50, 100, 200, alpha), (glow_radius, glow_radius), r)
            
        self.screen.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius))

    def draw_path(self, points, color, width=2):
        rot_x = rotation_matrix_x(self.angle_x)
        rot_y = rotation_matrix_y(self.angle_y)
        full_rot = np.dot(rot_x, rot_y)
        
        def process(pt):
             rotated = np.dot(full_rot, pt)
             return project_point(rotated, WIDTH, HEIGHT, FOV, self.viewer_dist, RADIUS)
             
        # Draw segments
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            rot_p1 = np.dot(full_rot, p1)
            rot_p2 = np.dot(full_rot, p2)
            
            # Visibility check: Check if EITHER point is visible to avoid culling loose segments
            if rot_p1[2] < 0 or rot_p2[2] < 0:
                px1, py1, _ = process(p1)
                px2, py2, _ = process(p2)
                pygame.draw.line(self.screen, color, (px1, py1), (px2, py2), width)
                # Draw small dot for debugging visibility
                if i % 10 == 0:
                   pygame.draw.circle(self.screen, color, (px1, py1), 2)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # 1. Draw Stars
        for s in self.stars:
            self.screen.set_at((s[0], s[1]), (s[2], s[2], s[2]))

        rot_x = rotation_matrix_x(self.angle_x)
        rot_y = rotation_matrix_y(self.angle_y)
        full_rot = np.dot(rot_x, rot_y)
        
        def process_point(point):
            rotated = np.dot(full_rot, point)
            return project_point(rotated, WIDTH, HEIGHT, FOV, self.viewer_dist, RADIUS)

        # Calculate approximate projected radius for atmosphere
        # We can project a point on the "limb" to guess scale
        center_px, center_py, center_scale = process_point(np.array([0,0,0]))
        projected_radius = RADIUS * center_scale
        
        # 2. Draw Atmosphere Glow (behind globe)
        self.draw_atmosphere(center_px, center_py, projected_radius)

        # 3. Draw Globe Wireframe
        # Separate front and back faces?
        # A simple sorting or just drawing all invisible back lines first slightly darker?
        # Let's do simple culling as before for clarity, but maybe draw back lines very faint?
        
        # To make it look "better", let's draw backlines very faintly
        back_lines = []
        front_lines = []
        
        for line in self.globe_points:
            proj_line_front = []
            proj_line_back = []
            
            # We need to segment line into front/back parts
            # This is tricky for long lines crossing the horizon.
            # Simplified approach: If midpoint or majority is back, it's back.
            # Even simpler: Just draw segment by segment.
            
            for i in range(len(line) - 1):
                p1 = line[i]
                p2 = line[i+1]
                
                pt1_rot = np.dot(full_rot, p1)
                pt2_rot = np.dot(full_rot, p2)
                
                px1, py1, s1 = process_point(p1)
                px2, py2, s2 = process_point(p2)
                
                # Check center z of the segment
                avg_z = (pt1_rot[2] + pt2_rot[2]) / 2.0
                
                if avg_z >= 0:
                    proj_line_back.append(((px1, py1), (px2, py2)))
                else:
                    proj_line_front.append(((px1, py1), (px2, py2)))
                    
            back_lines.extend(proj_line_back)
            front_lines.extend(proj_line_front)

        # Draw Back lines (faint)
        for p1, p2 in back_lines:
             pygame.draw.line(self.screen, (20, 20, 50), p1, p2, 1)

        # Draw Front lines (bright)
        for p1, p2 in front_lines:
             pygame.draw.line(self.screen, GLOBE_COLOR, p1, p2, 1)

        # Draw Paths
        # 1. Map Path (Green) - "Straight on Map" - Draw THICKER
        # Using a bright Green for high contrast
        GREEN_NEON = (0, 255, 100)
        self.draw_path(self.map_points, GREEN_NEON, 3)
        
        # 2. Geodesic Path (Red) - "Curved but Shortest"
        self.draw_path(self.geodesic_points, PATH_COLOR, 3)

        # 5. Draw Plane
        current_pos = slerp(self.p_start, self.p_end, self.plane_t) * RADIUS
        rot_plane = np.dot(full_rot, current_pos)
        
        if rot_plane[2] < 0:
            px, py, scale = process_point(current_pos)
            # Draw a nice little plane icon or just a better circle
            pygame.draw.circle(self.screen, PLANE_COLOR, (px, py), int(5 * scale))
            # Glow for plane
            s = pygame.Surface((20*scale, 20*scale), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 0, 100), (10*scale, 10*scale), 8*scale)
            self.screen.blit(s, (px - 10*scale, py - 10*scale))
            
            # Label
            label = self.font.render("Plane", True, PLANE_COLOR)
            self.screen.blit(label, (px + 10, py - 10))

        # 6. Markers
        for p, label_txt in [(self.p_start, "New York"), (self.p_end, "Tokyo")]:
            rot_p = np.dot(full_rot, p)
            if rot_p[2] < 0:
                px, py, scale = process_point(p)
                pygame.draw.circle(self.screen, (50, 255, 50), (px, py), int(4 * scale))
                lbl = self.font.render(label_txt, True, (200, 255, 200))
                self.screen.blit(lbl, (px + 8, py))

        # UI Overlay
        ui_lines = [
            ("Geodesic Flight Path", (255, 255, 255), self.title_font),
            ("", (0,0,0), self.font),
            (f"Red Path (Shortest): {int(self.geodesic_dist)} km", PATH_COLOR, self.font),
            (f"Green Path (Map Line): {int(self.map_dist)} km", GREEN_NEON, self.font),
            (f"Difference: {int(self.map_dist - self.geodesic_dist)} km", (200, 200, 200), self.font),
            ("", (0,0,0), self.font),
            ("Scroll to Zoom, Drag to Rotate", (150, 150, 150), self.font),
        ]
        
        y_off = 20
        for text, color, font_obj in ui_lines:
            if not text:
                y_off += 10
                continue
            surf = font_obj.render(text, True, color)
            self.screen.blit(surf, (20, y_off))
            y_off += 30

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()