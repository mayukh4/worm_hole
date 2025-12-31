"""
CPU-Only Wormhole Raytracer - INTENTIONALLY SLOW
=================================================
This demonstrates why GPU acceleration is necessary.
Watch the FPS counter in the terminal cry.

This is the SAME math as the GPU shader version, 
but running on CPU one pixel at a time.

For YouTube video: "Simulating Wormholes in Python"
"""

import pygame
import numpy as np
import math
import time

# --- CONFIGURATION ---
# Using a MUCH smaller resolution to even be runnable
WIDTH, HEIGHT = 320, 180  # 1/4 of 1280x720 in each dimension = 1/16 pixels
# Even at this tiny size: 320 × 180 = 57,600 pixels

FPS_UPDATE_INTERVAL = 0.5  # Update FPS display every 0.5 seconds

# Wormhole parameters
THROAT_SIZE = 1.5
MAX_STEPS = 200  # Reduced from 600 for sanity
MAX_DIST = 50.0

# Camera
CAM_L = -15.0  # Starting position (in "blue" universe)
CAM_THETA = math.pi / 2
CAM_PHI = 0.0


def derivatives(l, th, ph, vl, vth, vph, b):
    """
    Morris-Thorne geodesic equations.
    Identical to the GPU shader version.
    """
    r2 = l*l + b*b
    sin_th = math.sin(th)
    if abs(sin_th) < 0.001:
        sin_th = 0.001 * (1 if sin_th >= 0 else -1)
    cos_th = math.cos(th)
    
    # Position derivatives
    dl = vl
    dth = vth
    dph = vph
    
    # Velocity derivatives (geodesic equation)
    dvl = l * (vth*vth + sin_th*sin_th * vph*vph)
    dvth = -(2.0*l/r2)*vl*vth + sin_th*cos_th*vph*vph
    dvph = -(2.0*l/r2)*vl*vph - 2.0*(cos_th/sin_th)*vth*vph
    
    return dl, dth, dph, dvl, dvth, dvph


def rk4_step(l, th, ph, vl, vth, vph, b, h):
    """
    Runge-Kutta 4 integration step.
    Identical to the GPU shader version.
    """
    # k1
    k1 = derivatives(l, th, ph, vl, vth, vph, b)
    
    # k2
    k2 = derivatives(
        l + k1[0]*h*0.5, th + k1[1]*h*0.5, ph + k1[2]*h*0.5,
        vl + k1[3]*h*0.5, vth + k1[4]*h*0.5, vph + k1[5]*h*0.5, b
    )
    
    # k3
    k3 = derivatives(
        l + k2[0]*h*0.5, th + k2[1]*h*0.5, ph + k2[2]*h*0.5,
        vl + k2[3]*h*0.5, vth + k2[4]*h*0.5, vph + k2[5]*h*0.5, b
    )
    
    # k4
    k4 = derivatives(
        l + k3[0]*h, th + k3[1]*h, ph + k3[2]*h,
        vl + k3[3]*h, vth + k3[4]*h, vph + k3[5]*h, b
    )
    
    # Combine
    new_l = l + (h/6.0) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
    new_th = th + (h/6.0) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
    new_ph = ph + (h/6.0) * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
    new_vl = vl + (h/6.0) * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])
    new_vth = vth + (h/6.0) * (k1[4] + 2*k2[4] + 2*k3[4] + k4[4])
    new_vph = vph + (h/6.0) * (k1[5] + 2*k2[5] + 2*k3[5] + k4[5])
    
    return new_l, new_th, new_ph, new_vl, new_vth, new_vph


def hash3(x, y, z):
    """Simple hash for procedural noise."""
    p = np.array([x, y, z]) * 0.1031
    p = p - np.floor(p)
    p = p + np.dot(p, p + 33.33)
    return (p[0] + p[1]) * p[2] - math.floor((p[0] + p[1]) * p[2])


def get_sky_color(dx, dy, dz, universe_sign):
    """
    Generate procedural sky color.
    Simplified version of shader's get_sky function.
    """
    # Base star field
    stars = hash3(dx * 150, dy * 150, dz * 150) ** 100 * 2.0
    r, g, b = stars, stars, stars
    
    if universe_sign > 0:
        # Blue universe
        r += 0.02 + abs(dx) * 0.1
        g += 0.05 + abs(dy) * 0.2
        b += 0.3 + abs(dz) * 0.3
    else:
        # Red universe
        r += 0.4 + abs(dx) * 0.3
        g += 0.08 + abs(dy) * 0.1
        b += 0.05
    
    # Clamp
    r = min(1.0, max(0.0, r))
    g = min(1.0, max(0.0, g))
    b = min(1.0, max(0.0, b))
    
    # Gamma correction
    r = r ** 0.4545
    g = g ** 0.4545
    b = b ** 0.4545
    
    return int(r * 255), int(g * 255), int(b * 255)


def trace_ray(px, py, cam_forward, cam_right, cam_up, b):
    """
    Trace a single ray through the wormhole.
    This is where all the computation happens.
    """
    # Calculate ray direction from pixel position
    uv_x = (px - WIDTH * 0.5) / HEIGHT
    uv_y = (py - HEIGHT * 0.5) / HEIGHT
    
    # Ray direction in world space
    rd = np.array([
        cam_forward[0] + uv_x * cam_right[0] + uv_y * cam_up[0],
        cam_forward[1] + uv_x * cam_right[1] + uv_y * cam_up[1],
        cam_forward[2] + uv_x * cam_right[2] + uv_y * cam_up[2]
    ])
    rd = rd / np.linalg.norm(rd)
    
    # Initial state in wormhole coordinates
    l = CAM_L
    th = CAM_THETA
    ph = CAM_PHI
    
    # Calculate r(l) = sqrt(b² + l²)
    rl = math.sqrt(b*b + l*l)
    
    # Basis vectors at camera position
    er = np.array([
        math.sin(th) * math.cos(ph),
        math.sin(th) * math.sin(ph),
        math.cos(th)
    ])
    eth = np.array([
        math.cos(th) * math.cos(ph),
        math.cos(th) * math.sin(ph),
        -math.sin(th)
    ])
    eph = np.array([
        -math.sin(ph),
        math.cos(ph),
        0.0
    ])
    
    # Initial velocities
    vl = np.dot(rd, er)
    vth = np.dot(rd, eth) / rl
    sin_th = math.sin(th)
    if abs(sin_th) < 0.001:
        sin_th = 0.001
    vph = np.dot(rd, eph) / (rl * sin_th)
    
    # Raymarch!
    for _ in range(MAX_STEPS):
        # Adaptive step size
        dist = abs(l)
        if dist < 3.0:
            h = 0.02
        elif dist < 6.0:
            h = 0.06
        else:
            h = 0.15
        
        # RK4 step
        l, th, ph, vl, vth, vph = rk4_step(l, th, ph, vl, vth, vph, b, h)
        
        # Check if escaped
        if abs(l) > MAX_DIST:
            break
    
    # Determine final direction and universe
    universe_sign = 1.0 if l > 0 else -1.0
    final_dir = np.array([
        math.sin(th) * math.cos(ph),
        math.sin(th) * math.sin(ph),
        math.cos(th)
    ])
    
    return get_sky_color(final_dir[0], final_dir[1], final_dir[2], universe_sign)


def main():
    pygame.init()
    
    # Create window at 4x size for visibility, but render at low res
    display_scale = 4
    screen = pygame.display.set_mode((WIDTH * display_scale, HEIGHT * display_scale))
    pygame.display.set_caption("CPU Wormhole Raytracer - SLOW VERSION")
    
    # Create a surface at actual render resolution
    render_surface = pygame.Surface((WIDTH, HEIGHT))
    
    # Camera setup (looking toward wormhole)
    cam_yaw = math.pi / 2
    cam_pitch = 0.0
    
    cam_forward = np.array([
        math.cos(cam_pitch) * math.sin(cam_yaw),
        math.sin(cam_pitch),
        math.cos(cam_pitch) * math.cos(cam_yaw)
    ], dtype=np.float64)
    
    cam_right = np.cross(cam_forward, np.array([0, 1, 0]))
    cam_right = cam_right / np.linalg.norm(cam_right)
    cam_up = np.cross(cam_right, cam_forward)
    
    # FPS tracking
    frame_count = 0
    fps_timer = time.time()
    current_fps = 0.0
    
    # Stats
    total_pixels = WIDTH * HEIGHT
    total_rays_traced = 0
    
    print("=" * 60)
    print("CPU WORMHOLE RAYTRACER - PERFORMANCE DEMONSTRATION")
    print("=" * 60)
    print(f"Resolution: {WIDTH} x {HEIGHT} = {total_pixels:,} pixels")
    print(f"Max steps per ray: {MAX_STEPS}")
    print(f"RK4 evaluations per step: 4")
    print(f"Operations per frame: ~{total_pixels * MAX_STEPS * 4 * 20:,}")
    print("=" * 60)
    print("Watch the FPS counter below...")
    print("=" * 60)
    
    running = True
    
    while running:
        frame_start = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # RENDER FRAME - This is the slow part!
        pixels = pygame.PixelArray(render_surface)
        
        for py in range(HEIGHT):
            for px in range(WIDTH):
                color = trace_ray(px, py, cam_forward, cam_right, cam_up, THROAT_SIZE)
                pixels[px, py] = color
                total_rays_traced += 1
        
        del pixels  # Release pixel array
        
        # Scale up and display
        scaled = pygame.transform.scale(render_surface, 
                                        (WIDTH * display_scale, HEIGHT * display_scale))
        screen.blit(scaled, (0, 0))
        
        # Draw FPS overlay
        font = pygame.font.SysFont("monospace", 20)
        fps_text = font.render(f"FPS: {current_fps:.2f}", True, (255, 255, 0))
        screen.blit(fps_text, (10, 10))
        
        res_text = font.render(f"Resolution: {WIDTH}x{HEIGHT} (scaled 4x)", True, (255, 255, 255))
        screen.blit(res_text, (10, 35))
        
        note_text = font.render("This is 1/16th of 1280x720!", True, (255, 100, 100))
        screen.blit(note_text, (10, 60))
        
        pygame.display.flip()
        
        # Update FPS counter
        frame_count += 1
        frame_time = time.time() - frame_start
        
        if time.time() - fps_timer >= FPS_UPDATE_INTERVAL:
            current_fps = frame_count / (time.time() - fps_timer)
            
            # Print to terminal
            print(f"FPS: {current_fps:.3f} | "
                  f"Frame time: {frame_time*1000:.1f}ms | "
                  f"Rays traced: {total_rays_traced:,}")
            
            frame_count = 0
            fps_timer = time.time()
    
    # Final stats
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    print(f"Total rays traced: {total_rays_traced:,}")
    print(f"Average FPS: {current_fps:.3f}")
    print(f"\nAt full 1280x720 resolution, this would be {16:.0f}x slower!")
    print(f"Estimated full-res FPS: {current_fps/16:.4f}")
    print("=" * 60)
    
    pygame.quit()


if __name__ == "__main__":
    main()