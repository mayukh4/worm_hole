"""
CPU vs GPU Parallel Processing Visualization
=============================================
Demonstrates why fragment shaders are so powerful:
- CPU: Processes pixels ONE BY ONE (sequential)
- GPU: Processes ALL PIXELS AT ONCE (parallel)

For YouTube video: "Simulating Wormholes in Python"
"""

import pygame
import math
import time
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1400, 700
PANEL_WIDTH = WIDTH // 2
RENDER_WIDTH, RENDER_HEIGHT = 160, 90  # Small grid for visualization
PIXEL_SIZE = 4  # Each "pixel" drawn as 4x4 square for visibility

FPS = 60

# Colors
BG_COLOR = (8, 8, 18)
TEXT_COLOR = (200, 200, 200)
TITLE_COLOR = (255, 255, 255)
GRID_COLOR = (30, 30, 40)

# CPU colors (warm - to show it's "working hard")
CPU_COMPUTING_COLOR = (255, 200, 50)
CPU_DONE_COLOR = (255, 100, 50)

# GPU colors (cool - efficient)
GPU_COMPUTING_COLOR = (50, 200, 255)
GPU_DONE_COLOR = (50, 255, 150)


def generate_wormhole_color(x, y, width, height):
    """
    Generate a color that looks like wormhole output.
    Simplified version - creates a radial pattern.
    """
    # Normalize coordinates to [-1, 1]
    nx = (x / width) * 2 - 1
    ny = (y / height) * 2 - 1
    
    # Distance from center
    dist = math.sqrt(nx*nx + ny*ny)
    
    # Angle
    angle = math.atan2(ny, nx)
    
    # Create wormhole-like pattern
    # Central dark region (the throat)
    throat_radius = 0.3
    
    if dist < throat_radius:
        # Inside throat - show "other universe" (reddish)
        intensity = 1 - dist / throat_radius
        r = int(150 + 100 * intensity)
        g = int(50 + 50 * intensity)
        b = int(30)
    else:
        # Outside throat - show "our universe" (bluish) with ring
        ring_intensity = math.exp(-(dist - throat_radius) * 3)
        
        # Background stars/nebula
        noise = (math.sin(angle * 10 + dist * 20) + 1) * 0.2
        
        r = int(30 + ring_intensity * 200 + noise * 50)
        g = int(50 + ring_intensity * 150 + noise * 100)
        b = int(150 + ring_intensity * 100 + noise * 50)
    
    return (min(255, r), min(255, g), min(255, b))


class CPUSimulator:
    """Simulates CPU processing pixels one by one."""
    
    def __init__(self, x_offset, y_offset):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.pixels = {}  # (x, y) -> color
        self.current_pixel = 0
        self.total_pixels = RENDER_WIDTH * RENDER_HEIGHT
        self.computing = False
        self.done = False
        self.pixels_per_frame = 8  # How many pixels to compute per frame
        
        # For timing display
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.computing = True
        self.done = False
        self.current_pixel = 0
        self.pixels = {}
        self.start_time = time.time()
        self.end_time = None
    
    def reset(self):
        self.computing = False
        self.done = False
        self.current_pixel = 0
        self.pixels = {}
        self.start_time = None
        self.end_time = None
    
    def update(self):
        if not self.computing or self.done:
            return
        
        # Process a few pixels this frame
        for _ in range(self.pixels_per_frame):
            if self.current_pixel >= self.total_pixels:
                self.done = True
                self.computing = False
                self.end_time = time.time()
                return
            
            # Calculate x, y from linear index
            x = self.current_pixel % RENDER_WIDTH
            y = self.current_pixel // RENDER_WIDTH
            
            # "Compute" the pixel color
            color = generate_wormhole_color(x, y, RENDER_WIDTH, RENDER_HEIGHT)
            self.pixels[(x, y)] = color
            
            self.current_pixel += 1
    
    def draw(self, screen):
        # Draw grid background
        grid_width = RENDER_WIDTH * PIXEL_SIZE
        grid_height = RENDER_HEIGHT * PIXEL_SIZE
        grid_x = self.x_offset + (PANEL_WIDTH - grid_width) // 2
        grid_y = self.y_offset + 80
        
        # Background
        pygame.draw.rect(screen, (15, 15, 25), 
                        (grid_x - 2, grid_y - 2, grid_width + 4, grid_height + 4))
        
        # Draw computed pixels
        for (x, y), color in self.pixels.items():
            px = grid_x + x * PIXEL_SIZE
            py = grid_y + y * PIXEL_SIZE
            pygame.draw.rect(screen, color, (px, py, PIXEL_SIZE - 1, PIXEL_SIZE - 1))
        
        # Draw current pixel being computed (highlighted)
        if self.computing and not self.done:
            curr_x = self.current_pixel % RENDER_WIDTH
            curr_y = self.current_pixel // RENDER_WIDTH
            px = grid_x + curr_x * PIXEL_SIZE
            py = grid_y + curr_y * PIXEL_SIZE
            
            # Scanning line effect
            scan_y = grid_y + curr_y * PIXEL_SIZE
            pygame.draw.rect(screen, CPU_COMPUTING_COLOR, 
                           (grid_x, scan_y, grid_width, PIXEL_SIZE), 1)
            
            # Current pixel highlight
            pygame.draw.rect(screen, (255, 255, 255), 
                           (px - 1, py - 1, PIXEL_SIZE + 2, PIXEL_SIZE + 2), 2)
        
        # Draw border
        border_color = CPU_DONE_COLOR if self.done else (CPU_COMPUTING_COLOR if self.computing else GRID_COLOR)
        pygame.draw.rect(screen, border_color,
                        (grid_x - 2, grid_y - 2, grid_width + 4, grid_height + 4), 2)
        
        return grid_x, grid_y, grid_width, grid_height


class GPUSimulator:
    """Simulates GPU processing all pixels in parallel."""
    
    def __init__(self, x_offset, y_offset):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.pixels = {}
        self.computing = False
        self.done = False
        
        # GPU "computes" in one burst after a short delay
        self.compute_delay = 0.3  # seconds to show "computing" state
        self.compute_start_time = None
        
        # For timing display
        self.start_time = None
        self.end_time = None
        
        # Animation: pixels appearing in parallel waves
        self.reveal_progress = 0.0
        self.revealing = False
    
    def start(self):
        self.computing = True
        self.done = False
        self.pixels = {}
        self.start_time = time.time()
        self.compute_start_time = time.time()
        self.end_time = None
        self.reveal_progress = 0.0
        self.revealing = False
        
        # Pre-compute all pixels (simulating parallel computation)
        for y in range(RENDER_HEIGHT):
            for x in range(RENDER_WIDTH):
                color = generate_wormhole_color(x, y, RENDER_WIDTH, RENDER_HEIGHT)
                self.pixels[(x, y)] = color
    
    def reset(self):
        self.computing = False
        self.done = False
        self.pixels = {}
        self.start_time = None
        self.end_time = None
        self.reveal_progress = 0.0
        self.revealing = False
    
    def update(self):
        if not self.computing:
            return
        
        if self.done:
            return
        
        elapsed = time.time() - self.compute_start_time
        
        if not self.revealing and elapsed >= self.compute_delay:
            # Start revealing all pixels at once!
            self.revealing = True
            self.reveal_progress = 0.0
        
        if self.revealing:
            # Quick reveal animation (all pixels fade in together)
            self.reveal_progress += 0.15
            if self.reveal_progress >= 1.0:
                self.reveal_progress = 1.0
                self.done = True
                self.computing = False
                self.end_time = time.time()
    
    def draw(self, screen):
        grid_width = RENDER_WIDTH * PIXEL_SIZE
        grid_height = RENDER_HEIGHT * PIXEL_SIZE
        grid_x = self.x_offset + (PANEL_WIDTH - grid_width) // 2
        grid_y = self.y_offset + 80
        
        # Background
        pygame.draw.rect(screen, (15, 15, 25),
                        (grid_x - 2, grid_y - 2, grid_width + 4, grid_height + 4))
        
        if self.revealing or self.done:
            # Draw ALL pixels with fade-in effect
            alpha = self.reveal_progress if not self.done else 1.0
            
            for (x, y), color in self.pixels.items():
                px = grid_x + x * PIXEL_SIZE
                py = grid_y + y * PIXEL_SIZE
                
                # Apply alpha
                final_color = (
                    int(color[0] * alpha),
                    int(color[1] * alpha),
                    int(color[2] * alpha)
                )
                pygame.draw.rect(screen, final_color, 
                               (px, py, PIXEL_SIZE - 1, PIXEL_SIZE - 1))
        
        elif self.computing:
            # Show "computing" state - all pixels pulsing
            pulse = (math.sin(time.time() * 10) + 1) * 0.5
            computing_color = (
                int(30 + 50 * pulse),
                int(50 + 100 * pulse),
                int(100 + 100 * pulse)
            )
            
            # Draw grid of computing pixels
            for y in range(RENDER_HEIGHT):
                for x in range(RENDER_WIDTH):
                    px = grid_x + x * PIXEL_SIZE
                    py = grid_y + y * PIXEL_SIZE
                    pygame.draw.rect(screen, computing_color,
                                   (px, py, PIXEL_SIZE - 1, PIXEL_SIZE - 1))
        
        # Draw border
        border_color = GPU_DONE_COLOR if self.done else (GPU_COMPUTING_COLOR if self.computing else GRID_COLOR)
        pygame.draw.rect(screen, border_color,
                        (grid_x - 2, grid_y - 2, grid_width + 4, grid_height + 4), 2)
        
        return grid_x, grid_y, grid_width, grid_height


def draw_processor_diagram(screen, x, y, is_gpu=False):
    """Draw a simple diagram of CPU vs GPU architecture."""
    
    if is_gpu:
        # GPU: Many small cores
        core_size = 8
        cores_x, cores_y = 12, 6
        
        for cy in range(cores_y):
            for cx in range(cores_x):
                px = x + cx * (core_size + 2)
                py = y + cy * (core_size + 2)
                color = GPU_COMPUTING_COLOR if (cx + cy) % 2 == 0 else (30, 150, 200)
                pygame.draw.rect(screen, color, (px, py, core_size, core_size))
    else:
        # CPU: Few large cores
        core_size = 25
        cores_x, cores_y = 4, 2
        
        for cy in range(cores_y):
            for cx in range(cores_x):
                px = x + cx * (core_size + 5)
                py = y + cy * (core_size + 5)
                color = CPU_COMPUTING_COLOR if cx == 0 and cy == 0 else (100, 60, 30)
                pygame.draw.rect(screen, color, (px, py, core_size, core_size))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CPU vs GPU: Sequential vs Parallel Processing")
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 36, bold=True)
    font_subtitle = pygame.font.SysFont("Arial", 20)
    font_info = pygame.font.SysFont("monospace", 16)
    font_big = pygame.font.SysFont("Arial", 48, bold=True)
    
    # Create simulators
    cpu = CPUSimulator(0, 0)
    gpu = GPUSimulator(PANEL_WIDTH, 0)
    
    running = True
    simulation_started = False
    show_comparison = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Start/restart simulation
                    cpu.start()
                    gpu.start()
                    simulation_started = True
                    show_comparison = False
                elif event.key == pygame.K_r:
                    cpu.reset()
                    gpu.reset()
                    simulation_started = False
                    show_comparison = False
                elif event.key == pygame.K_UP:
                    cpu.pixels_per_frame = min(cpu.pixels_per_frame + 4, 64)
                elif event.key == pygame.K_DOWN:
                    cpu.pixels_per_frame = max(cpu.pixels_per_frame - 4, 1)
        
        # Update
        cpu.update()
        gpu.update()
        
        # Check if both done
        if cpu.done and gpu.done and not show_comparison:
            show_comparison = True
        
        # Draw
        screen.fill(BG_COLOR)
        
        # === LEFT PANEL: CPU ===
        # Title
        cpu_title = font_title.render("CPU", True, CPU_COMPUTING_COLOR)
        cpu_title_rect = cpu_title.get_rect(center=(PANEL_WIDTH // 2, 30))
        screen.blit(cpu_title, cpu_title_rect)
        
        # Subtitle
        cpu_sub = font_subtitle.render("Sequential Processing", True, TEXT_COLOR)
        cpu_sub_rect = cpu_sub.get_rect(center=(PANEL_WIDTH // 2, 60))
        screen.blit(cpu_sub, cpu_sub_rect)
        
        # Draw pixel grid
        cpu_grid = cpu.draw(screen)
        
        # Progress
        progress_pct = (cpu.current_pixel / cpu.total_pixels) * 100
        progress_text = f"Progress: {progress_pct:.1f}% ({cpu.current_pixel:,} / {cpu.total_pixels:,} pixels)"
        progress_surf = font_info.render(progress_text, True, TEXT_COLOR)
        screen.blit(progress_surf, (20, cpu_grid[1] + cpu_grid[3] + 20))
        
        # Time
        if cpu.start_time:
            elapsed = (cpu.end_time or time.time()) - cpu.start_time
            time_text = f"Time: {elapsed:.2f}s"
            time_color = GPU_DONE_COLOR if cpu.done else TEXT_COLOR
            time_surf = font_info.render(time_text, True, time_color)
            screen.blit(time_surf, (20, cpu_grid[1] + cpu_grid[3] + 45))
        
        # Code representation
        code_y = cpu_grid[1] + cpu_grid[3] + 80
        code_lines = [
            "for y in range(HEIGHT):",
            "    for x in range(WIDTH):",
            "        color = trace_ray(x, y)",
            "        pixels[x,y] = color",
            "",
            "# One pixel at a time...",
        ]
        for i, line in enumerate(code_lines):
            color = CPU_COMPUTING_COLOR if i == 2 and cpu.computing else (100, 100, 120)
            code_surf = font_info.render(line, True, color)
            screen.blit(code_surf, (30, code_y + i * 20))
        
        # Draw CPU diagram
        draw_processor_diagram(screen, 30, code_y + 140, is_gpu=False)
        cpu_label = font_info.render("4-8 cores (only 1 active)", True, (150, 100, 50))
        screen.blit(cpu_label, (30, code_y + 200))
        
        # === RIGHT PANEL: GPU ===
        # Title
        gpu_title = font_title.render("GPU (Fragment Shader)", True, GPU_COMPUTING_COLOR)
        gpu_title_rect = gpu_title.get_rect(center=(PANEL_WIDTH + PANEL_WIDTH // 2, 30))
        screen.blit(gpu_title, gpu_title_rect)
        
        # Subtitle
        gpu_sub = font_subtitle.render("Parallel Processing", True, TEXT_COLOR)
        gpu_sub_rect = gpu_sub.get_rect(center=(PANEL_WIDTH + PANEL_WIDTH // 2, 60))
        screen.blit(gpu_sub, gpu_sub_rect)
        
        # Draw pixel grid
        gpu_grid = gpu.draw(screen)
        
        # Status
        if gpu.done:
            status_text = f"ALL {RENDER_WIDTH * RENDER_HEIGHT:,} pixels computed in parallel!"
        elif gpu.revealing:
            status_text = "Rendering output..."
        elif gpu.computing:
            status_text = f"Computing ALL {RENDER_WIDTH * RENDER_HEIGHT:,} pixels simultaneously..."
        else:
            status_text = "Ready"
        
        status_surf = font_info.render(status_text, True, GPU_COMPUTING_COLOR if gpu.computing else TEXT_COLOR)
        screen.blit(status_surf, (PANEL_WIDTH + 20, gpu_grid[1] + gpu_grid[3] + 20))
        
        # Time
        if gpu.start_time:
            elapsed = (gpu.end_time or time.time()) - gpu.start_time
            time_text = f"Time: {elapsed:.2f}s"
            time_color = GPU_DONE_COLOR if gpu.done else TEXT_COLOR
            time_surf = font_info.render(time_text, True, time_color)
            screen.blit(time_surf, (PANEL_WIDTH + 20, gpu_grid[1] + gpu_grid[3] + 45))
        
        # Code representation
        code_y = gpu_grid[1] + gpu_grid[3] + 80
        code_lines = [
            "void main() {",
            "    vec2 pixel = gl_FragCoord.xy;",
            "    vec3 color = trace_ray(pixel);",
            "    fragColor = vec4(color, 1.0);",
            "}",
            "// ALL pixels at once!",
        ]
        for i, line in enumerate(code_lines):
            color = GPU_COMPUTING_COLOR if i == 2 and gpu.computing else (100, 100, 120)
            code_surf = font_info.render(line, True, color)
            screen.blit(code_surf, (PANEL_WIDTH + 30, code_y + i * 20))
        
        # Draw GPU diagram
        draw_processor_diagram(screen, PANEL_WIDTH + 30, code_y + 140, is_gpu=True)
        gpu_label = font_info.render("1000s of cores (ALL active)", True, (50, 200, 150))
        screen.blit(gpu_label, (PANEL_WIDTH + 30, code_y + 200))
        
        # === DIVIDER ===
        pygame.draw.line(screen, (60, 60, 80), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 3)
        
        # === COMPARISON RESULT ===
        if show_comparison and cpu.end_time and gpu.end_time:
            cpu_time = cpu.end_time - cpu.start_time
            gpu_time = gpu.end_time - gpu.start_time
            speedup = cpu_time / max(gpu_time, 0.001)
            
            # Draw comparison box
            box_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 60, 400, 120)
            pygame.draw.rect(screen, (20, 20, 40), box_rect)
            pygame.draw.rect(screen, GPU_DONE_COLOR, box_rect, 3)
            
            result_text = f"GPU is ~{speedup:.0f}x faster!"
            result_surf = font_big.render(result_text, True, GPU_DONE_COLOR)
            result_rect = result_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            screen.blit(result_surf, result_rect)
            
            detail_text = f"CPU: {cpu_time:.2f}s | GPU: {gpu_time:.2f}s"
            detail_surf = font_subtitle.render(detail_text, True, TEXT_COLOR)
            detail_rect = detail_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25))
            screen.blit(detail_surf, detail_rect)
        
        # === INSTRUCTIONS ===
        if not simulation_started:
            instruction = font_subtitle.render("Press SPACE to start simulation", True, (150, 150, 200))
            instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT - 30))
            screen.blit(instruction, instruction_rect)
        else:
            controls = "SPACE: Restart | R: Reset | ↑/↓: CPU speed"
            controls_surf = font_info.render(controls, True, (100, 100, 120))
            screen.blit(controls_surf, (10, HEIGHT - 25))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()


if __name__ == "__main__":
    main()