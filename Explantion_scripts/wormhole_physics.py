"""
Exotic Matter & Wormhole Tension Visualization
===============================================
FIXED VERSION - No overlapping elements

Demonstrates why wormholes require exotic matter:
- Normal matter: positive pressure (pushes inward)
- Exotic matter: negative pressure/tension (pulls outward)
- Required tension: ~10^34 Pascals (like a neutron star, but REVERSED)

For YouTube video: "Simulating Wormholes in Python"
"""

import pygame
import math
import time

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1600, 900  # Larger window to fit everything
FPS = 60

# Colors
BG_COLOR = (5, 5, 15)
TEXT_COLOR = (200, 200, 200)
TITLE_COLOR = (255, 255, 255)

# Wormhole colors
THROAT_COLOR = (100, 150, 255)
THROAT_GLOW = (50, 100, 200)
SPACETIME_COLOR = (30, 40, 60)

# Force arrows
INWARD_COLOR = (255, 80, 80)      # Red - collapse force
OUTWARD_COLOR = (80, 255, 150)    # Green - exotic matter tension

# Pressure scale colors
SCALE_COLORS = [
    (80, 200, 80),     # Low pressure - green
    (150, 200, 80),    
    (200, 200, 80),    # Medium - yellow
    (255, 180, 50),    # High - orange
    (255, 100, 50),    # Very high - red-orange
    (255, 50, 200),    # Extreme - magenta
]


class WormholeThroat:
    """Animated wormhole throat that can collapse or stay open."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_radius = 100
        self.current_radius = self.base_radius
        self.target_radius = self.base_radius
        
        # State
        self.has_exotic_matter = True
        self.collapsed = False
        
        # Animation
        self.pulse_phase = 0
        self.collapse_speed = 0
        self.arrow_pulse = 0
        
        # Force arrows
        self.num_arrows = 12
        self.arrow_length = 70
    
    def set_exotic_matter(self, has_it):
        self.has_exotic_matter = has_it
        if has_it:
            self.target_radius = self.base_radius
            self.collapsed = False
            self.collapse_speed = 0
        else:
            self.target_radius = 8
    
    def reset(self):
        self.current_radius = self.base_radius
        self.target_radius = self.base_radius
        self.has_exotic_matter = True
        self.collapsed = False
        self.collapse_speed = 0
    
    def update(self, dt):
        self.pulse_phase += dt * 2
        self.arrow_pulse += dt * 3
        
        if self.has_exotic_matter:
            pulse = math.sin(self.pulse_phase) * 4
            self.current_radius = self.base_radius + pulse
        else:
            if self.current_radius > self.target_radius:
                self.collapse_speed += dt * 80
                self.current_radius -= self.collapse_speed * dt
                if self.current_radius <= self.target_radius:
                    self.current_radius = self.target_radius
                    self.collapsed = True
    
    def draw(self, screen):
        # Draw spacetime fabric
        self._draw_spacetime_fabric(screen)
        
        # Draw throat glow
        for i in range(5, 0, -1):
            glow_radius = self.current_radius + i * 10
            pygame.draw.circle(screen, THROAT_GLOW, (int(self.x), int(self.y)), 
                             int(glow_radius), 2)
        
        # Draw throat
        pygame.draw.circle(screen, THROAT_COLOR, (int(self.x), int(self.y)), 
                          int(self.current_radius), 4)
        
        # Draw center (the passage)
        inner_color = (15, 25, 45) if not self.collapsed else (5, 5, 15)
        pygame.draw.circle(screen, inner_color, (int(self.x), int(self.y)), 
                          int(max(5, self.current_radius * 0.7)))
        
        # Draw force arrows
        self._draw_force_arrows(screen)
    
    def _draw_spacetime_fabric(self, screen):
        """Draw curved spacetime lines around the throat."""
        num_lines = 8
        for i in range(num_lines):
            angle = (i / num_lines) * math.pi * 2
            
            points = []
            for t in range(-12, 13):
                perp_dist = t * 15
                base_dist = 220 + abs(perp_dist) * 0.3
                bend = 40 / (1 + abs(perp_dist) * 0.04)
                actual_dist = base_dist - bend
                
                px = self.x + math.cos(angle) * actual_dist + math.cos(angle + math.pi/2) * perp_dist
                py = self.y + math.sin(angle) * actual_dist + math.sin(angle + math.pi/2) * perp_dist
                points.append((px, py))
            
            if len(points) > 1:
                pygame.draw.lines(screen, SPACETIME_COLOR, False, points, 1)
    
    def _draw_force_arrows(self, screen):
        """Draw arrows showing forces on the throat."""
        arrow_base_dist = self.current_radius + 25
        
        for i in range(self.num_arrows):
            angle = (i / self.num_arrows) * math.pi * 2 + self.arrow_pulse * 0.1
            
            start_x = self.x + math.cos(angle) * (arrow_base_dist + self.arrow_length)
            start_y = self.y + math.sin(angle) * (arrow_base_dist + self.arrow_length)
            end_x = self.x + math.cos(angle) * arrow_base_dist
            end_y = self.y + math.sin(angle) * arrow_base_dist
            
            if self.has_exotic_matter:
                # OUTWARD arrows
                start_x, end_x = end_x, start_x
                start_y, end_y = end_y, start_y
                color = OUTWARD_COLOR
                pulse = (math.sin(self.arrow_pulse + i * 0.5) + 1) * 0.3 + 0.5
            else:
                # INWARD arrows
                color = INWARD_COLOR
                speed = 1 + (self.base_radius - self.current_radius) * 0.15
                pulse = (math.sin(self.arrow_pulse * speed + i * 0.5) + 1) * 0.3 + 0.5
            
            final_color = (
                min(255, max(0, int(color[0] * pulse))),
                min(255, max(0, int(color[1] * pulse))),
                min(255, max(0, int(color[2] * pulse)))
            )
            
            pygame.draw.line(screen, final_color, (start_x, start_y), (end_x, end_y), 3)
            self._draw_arrowhead(screen, start_x, start_y, end_x, end_y, final_color)
    
    def _draw_arrowhead(self, screen, x1, y1, x2, y2, color):
        angle = math.atan2(y2 - y1, x2 - x1)
        head_length = 14
        head_angle = 0.5
        
        left_x = x2 - head_length * math.cos(angle - head_angle)
        left_y = y2 - head_length * math.sin(angle - head_angle)
        right_x = x2 - head_length * math.cos(angle + head_angle)
        right_y = y2 - head_length * math.sin(angle + head_angle)
        
        pygame.draw.polygon(screen, color, [(x2, y2), (left_x, left_y), (right_x, right_y)])


class PressureScale:
    """Visual scale comparing different pressures."""
    
    def __init__(self, x, y, height):
        self.x = x
        self.y = y
        self.height = height
        self.animation_progress = 0
        
        # Pressure data: (name, log10(pressure), description)
        self.pressures = [
            ("Atmospheric Pressure", 5, "What you feel right now"),
            ("Mariana Trench", 8, "Deepest ocean point"),
            ("Center of Earth", 11.5, "3.6 million atmospheres"),
            ("Center of the Sun", 16.4, "250 billion atmospheres"),
            ("Neutron Star Core", 34, "Densest known matter"),
            ("WORMHOLE THROAT", 34, "Same pressure, OPPOSITE direction!"),
        ]
    
    def update(self, dt):
        self.animation_progress += dt
    
    def draw(self, screen):
        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font = pygame.font.SysFont("Arial", 15)
        font_small = pygame.font.SysFont("Arial", 12)
        
        # Title
        title = font_title.render("PRESSURE COMPARISON", True, TITLE_COLOR)
        screen.blit(title, (self.x, self.y))
        
        # Scale parameters
        scale_top = self.y + 40
        scale_height = self.height - 60
        bar_width = 35
        
        # Draw scale bar with gradient
        pygame.draw.rect(screen, (30, 30, 45), 
                        (self.x, scale_top, bar_width, scale_height))
        
        for i in range(scale_height):
            t = i / scale_height
            idx = min(int(t * (len(SCALE_COLORS) - 1)), len(SCALE_COLORS) - 2)
            local_t = (t * (len(SCALE_COLORS) - 1)) - idx
            
            c1 = SCALE_COLORS[idx]
            c2 = SCALE_COLORS[min(idx + 1, len(SCALE_COLORS) - 1)]
            
            color = (
                int(c1[0] + (c2[0] - c1[0]) * local_t),
                int(c1[1] + (c2[1] - c1[1]) * local_t),
                int(c1[2] + (c2[2] - c1[2]) * local_t),
            )
            pygame.draw.line(screen, color, 
                           (self.x + 2, scale_top + i), 
                           (self.x + bar_width - 2, scale_top + i))
        
        # Draw border
        pygame.draw.rect(screen, (80, 80, 100), 
                        (self.x, scale_top, bar_width, scale_height), 2)
        
        # Draw pressure markers
        min_log, max_log = 4, 36
        
        for i, (name, log_val, desc) in enumerate(self.pressures):
            t = (log_val - min_log) / (max_log - min_log)
            marker_y = scale_top + t * scale_height
            
            is_exotic = "WORMHOLE" in name
            is_neutron = "Neutron" in name
            
            # Marker line and dot
            line_color = OUTWARD_COLOR if is_exotic else INWARD_COLOR
            pygame.draw.line(screen, line_color,
                           (self.x + bar_width, marker_y),
                           (self.x + bar_width + 15, marker_y), 2)
            pygame.draw.circle(screen, line_color,
                             (self.x + bar_width + 20, int(marker_y)), 5)
            
            # Text position
            text_x = self.x + bar_width + 30
            
            # Name
            name_color = OUTWARD_COLOR if is_exotic else (INWARD_COLOR if is_neutron else TEXT_COLOR)
            name_surf = font.render(name, True, name_color)
            screen.blit(name_surf, (text_x, marker_y - 10))
            
            # Pressure value
            pressure_str = f"10^{int(log_val)} Pa"
            pressure_surf = font_small.render(pressure_str, True, (120, 120, 140))
            screen.blit(pressure_surf, (text_x, marker_y + 8))
            
            # Direction
            if is_exotic:
                dir_text = "↑ PULLING OUTWARD ↑"
                dir_color = OUTWARD_COLOR
            else:
                dir_text = "↓ pushing inward"
                dir_color = (180, 80, 80)
            
            dir_surf = font_small.render(dir_text, True, dir_color)
            screen.blit(dir_surf, (text_x, marker_y + 22))
            
            # Description
            desc_surf = font_small.render(desc, True, (90, 90, 110))
            screen.blit(desc_surf, (text_x, marker_y + 36))
            
            # Highlight box for exotic matter
            if is_exotic:
                pulse = (math.sin(self.animation_progress * 3) + 1) * 0.3 + 0.2
                box_color = (int(30 * pulse), int(60 * pulse), int(40 * pulse))
                pygame.draw.rect(screen, box_color,
                               (text_x - 5, marker_y - 15, 280, 70))
                pygame.draw.rect(screen, OUTWARD_COLOR,
                               (text_x - 5, marker_y - 15, 280, 70), 2)
                
                # Redraw text on top of box
                name_surf = font.render(name, True, OUTWARD_COLOR)
                screen.blit(name_surf, (text_x, marker_y - 10))
                screen.blit(pressure_surf, (text_x, marker_y + 8))
                screen.blit(dir_surf, (text_x, marker_y + 22))
                screen.blit(desc_surf, (text_x, marker_y + 36))
        
        # Scale labels on left
        scale_labels = ["10⁵", "10¹⁰", "10¹⁵", "10²⁰", "10²⁵", "10³⁰", "10³⁵"]
        for i, label in enumerate(scale_labels):
            t = i / (len(scale_labels) - 1)
            label_y = scale_top + t * scale_height
            label_surf = font_small.render(label, True, (70, 70, 90))
            screen.blit(label_surf, (self.x - 40, label_y - 6))


def draw_comparison_boxes(screen, x, y):
    """Draw normal matter vs exotic matter comparison."""
    font_title = pygame.font.SysFont("Arial", 18, bold=True)
    font = pygame.font.SysFont("Arial", 14)
    
    box_width = 220
    box_height = 130
    gap = 30
    
    # Normal matter box
    pygame.draw.rect(screen, (25, 15, 15), (x, y, box_width, box_height))
    pygame.draw.rect(screen, INWARD_COLOR, (x, y, box_width, box_height), 2)
    
    title1 = font_title.render("NORMAL MATTER", True, INWARD_COLOR)
    screen.blit(title1, (x + 10, y + 10))
    
    props1 = [
        "• Positive energy density",
        "• Positive pressure",
        "• Pulls things together",
        "• Everything we've observed"
    ]
    for i, prop in enumerate(props1):
        surf = font.render(prop, True, TEXT_COLOR)
        screen.blit(surf, (x + 10, y + 40 + i * 20))
    
    # VS label
    vs_font = pygame.font.SysFont("Arial", 24, bold=True)
    vs_surf = vs_font.render("vs", True, (80, 80, 100))
    screen.blit(vs_surf, (x + box_width + 5, y + box_height // 2 - 12))
    
    # Exotic matter box
    ex_x = x + box_width + gap
    pygame.draw.rect(screen, (15, 25, 15), (ex_x, y, box_width, box_height))
    pygame.draw.rect(screen, OUTWARD_COLOR, (ex_x, y, box_width, box_height), 2)
    
    title2 = font_title.render("EXOTIC MATTER", True, OUTWARD_COLOR)
    screen.blit(title2, (ex_x + 10, y + 10))
    
    props2 = [
        "• Negative energy density",
        "• Negative pressure (tension)",
        "• Pushes things apart",
        "• NEVER OBSERVED!"
    ]
    for i, prop in enumerate(props2):
        color = (255, 100, 100) if "NEVER" in prop else TEXT_COLOR
        surf = font.render(prop, True, color)
        screen.blit(surf, (ex_x + 10, y + 40 + i * 20))


def draw_key_insight(screen, x, y, width):
    """Draw the key insight box."""
    font = pygame.font.SysFont("Arial", 15)
    
    box_height = 75
    pygame.draw.rect(screen, (15, 15, 30), (x, y, width, box_height))
    pygame.draw.rect(screen, (100, 100, 150), (x, y, width, box_height), 2)
    
    lines = [
        ("KEY INSIGHT:", TITLE_COLOR),
        ("To hold open a human-traversable wormhole, you need tension of ~10³⁴ Pa", TEXT_COLOR),
        ("(same as a neutron star core) but PULLING OUTWARD. Nothing can do this.", OUTWARD_COLOR),
    ]
    
    for i, (text, color) in enumerate(lines):
        surf = font.render(text, True, color)
        screen.blit(surf, (x + 15, y + 12 + i * 20))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wormhole Exotic Matter Requirements")
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 36, bold=True)
    font_subtitle = pygame.font.SysFont("Arial", 18)
    font_status = pygame.font.SysFont("Arial", 22, bold=True)
    font_controls = pygame.font.SysFont("Arial", 14)
    
    # Layout positions
    throat_x = 320
    throat_y = 380
    
    scale_x = 900
    scale_y = 80
    scale_height = 550
    
    comparison_x = 60
    comparison_y = 680
    
    insight_x = 60
    insight_y = 815
    insight_width = 520
    
    # Create objects
    throat = WormholeThroat(throat_x, throat_y)
    pressure_scale = PressureScale(scale_x, scale_y, scale_height)
    
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    throat.set_exotic_matter(not throat.has_exotic_matter)
                elif event.key == pygame.K_r:
                    throat.reset()
        
        # Update
        throat.update(dt)
        pressure_scale.update(dt)
        
        # Draw
        screen.fill(BG_COLOR)
        
        # Main title
        title = font_title.render("WHY WORMHOLES NEED EXOTIC MATTER", True, TITLE_COLOR)
        title_rect = title.get_rect(center=(WIDTH // 2, 35))
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = font_subtitle.render(
            "The throat naturally wants to collapse. Only exotic matter can hold it open.",
            True, (150, 150, 170)
        )
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, 65))
        screen.blit(subtitle, subtitle_rect)
        
        # Throat section label
        throat_label_font = pygame.font.SysFont("Arial", 20, bold=True)
        if throat.has_exotic_matter:
            label_text = "EXOTIC MATTER TENSION"
            label_sub = "(pulling outward - holding throat open)"
            label_color = OUTWARD_COLOR
        else:
            label_text = "GRAVITATIONAL COLLAPSE"
            label_sub = "(pushing inward - closing throat)"
            label_color = INWARD_COLOR
        
        label_surf = throat_label_font.render(label_text, True, label_color)
        label_rect = label_surf.get_rect(center=(throat_x, 120))
        screen.blit(label_surf, label_rect)
        
        sub_font = pygame.font.SysFont("Arial", 14)
        sub_surf = sub_font.render(label_sub, True, label_color)
        sub_rect = sub_surf.get_rect(center=(throat_x, 145))
        screen.blit(sub_surf, sub_rect)
        
        # Draw throat
        throat.draw(screen)
        
        # Status below throat
        if throat.has_exotic_matter:
            status = "✓ STABLE"
            status_color = OUTWARD_COLOR
        elif throat.collapsed:
            status = "✗ COLLAPSED"
            status_color = INWARD_COLOR
        else:
            status = "⚠ COLLAPSING..."
            status_color = (255, 200, 50)
        
        status_surf = font_status.render(status, True, status_color)
        status_rect = status_surf.get_rect(center=(throat_x, 620))
        screen.blit(status_surf, status_rect)
        
        # Draw pressure scale
        pressure_scale.draw(screen)
        
        # Draw comparison boxes
        draw_comparison_boxes(screen, comparison_x, comparison_y)
        
        # Draw key insight
        draw_key_insight(screen, insight_x, insight_y, insight_width)
        
        # Controls
        controls = "SPACE: Toggle exotic matter  |  R: Reset  |  ESC: Quit"
        controls_surf = font_controls.render(controls, True, (80, 80, 100))
        screen.blit(controls_surf, (WIDTH - 420, HEIGHT - 25))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()