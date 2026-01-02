import pygame
import moderngl
import numpy as np
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1280, 720
THROAT_SIZE = 1.5
MOUSE_SENSITIVITY = 0.002
MOVE_SPEED = 12.0

FRAGMENT_SHADER = '''
#version 330
uniform vec2 u_resolution;
uniform vec3 u_cam_pos;     // (l, theta, phi)
uniform vec3 u_cam_forward; // Camera orientation
uniform vec3 u_cam_right;
uniform vec3 u_cam_up;
uniform float u_throat;     // Throat size (b)
uniform float u_time;
uniform float u_glow_strength; // To toggle "pipe" effect (Cinematic vs Realistic)
uniform float u_fov_scale;  // Field of View scaling (Zoom)

out vec4 f_color;

#define MAX_STEPS 600
#define MAX_DIST 100.0
#define PI 3.14159265359

// --- NOISE FUNCTIONS ---
// Hash function (Dave_Hoskins Hash13)
float hash(vec3 p3) {
	p3  = fract(p3 * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// Gradient noise (using Value Noise approach with Quintic Smoothing)
float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    // Quintic interpolation (C2 continuous) to prevent derivative artifacts
    f = f*f*f*(f*(f*6.0-15.0)+10.0);
    return mix(mix(mix(hash(i+vec3(0,0,0)), hash(i+vec3(1,0,0)),f.x),
                   mix(hash(i+vec3(0,1,0)), hash(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash(i+vec3(0,0,1)), hash(i+vec3(1,0,1)),f.x),
                   mix(hash(i+vec3(0,1,1)), hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}

// --- FBM (Fractal Brownian Motion) for detailed clouds ---
float fbm(vec3 x) {
    float v = 0.0;
    float a = 0.5;
    mat3 rot = mat3(0.00, 0.80, 0.60, -0.80, 0.36, -0.48, -0.60, -0.48, 0.64);
    for (int i=0; i<3; i++) {
        v += a * noise(x);
        x = rot * x * 2.0; // Rotate octaves to prevent grid alignment
        a *= 0.5;
    }
    return v;
}

// --- GALAXY RENDERER ---
// Procedural Spiral Galaxy
vec3 render_galaxy(vec3 dir, vec3 center_dir, vec3 up_vec, float scale, vec3 color) {
    // 1. Create a coordinate system for the galaxy plane
    vec3 z_axis = normalize(center_dir);
    vec3 x_axis = normalize(cross(up_vec, z_axis));
    vec3 y_axis = cross(z_axis, x_axis);
    
    // 2. Project view direction onto the galaxy plane (tangent plane approximation)
    float dist_from_center = acos(dot(dir, z_axis)); // Angle from center
    
    // Discard if too far to save perf
    if (dist_from_center > scale * 1.5) return vec3(0.0);
    
    // 3. Local 2D coordinates
    float x = dot(dir, x_axis);
    float y = dot(dir, y_axis);
    
    // Polar coordinates
    float r = sqrt(x*x + y*y) / scale; // Normalized radius
    float angle = atan(y, x);
    
    // 4. Galaxy Shape Logic
    // Central Bulge
    float core = exp(-r * 4.0);
    
    // Spiral Arms
    // Arm twist: angle increases with radius
    float twist = angle - r * 3.5;
    // Two main arms (sin varies between -1 and 1, we want peaks)
    float arms = sin(twist * 2.0); 
    // Sharpen arms
    arms = smoothstep(0.2, 1.0, arms);
    // Fade arms with radius
    float arm_brightness = arms * exp(-r * 1.5) * smoothstep(0.0, 0.2, r); // Don't draw arms in dead center
    
    // Add noise for dust/texture
    float dust = fbm(vec3(x*15.0, y*15.0, 0.0));
    
    // 5. Combine
    float total_light = core * 2.0 + arm_brightness * (0.8 + dust * 0.5);
    
    // Falloff at edge
    total_light *= smoothstep(1.5, 0.5, r);
    
    return color * total_light * 1.5;
}

// --- BACKGROUND GENERATION ---
vec3 get_sky(vec3 dir, float uni_sign) {
    // Offset and Rotate dir to avoid 0-crossing axial artifacts
    // The rotation matrix breaks the alignment with the camera axes
    mat3 base_rot = mat3(0.6, -0.8, 0.0, 0.8, 0.6, 0.0, 0.0, 0.0, 1.0);
    vec3 safe_dir = base_rot * dir + vec3(100.13, 100.47, 100.89);
    
    // 1. Base Stars (YouTube Enhancement: Increased brightness from 2.0 to 3.5)
    float stars = pow(hash(safe_dir * 150.0), 100.0) * 3.5;
    vec3 col = vec3(stars);
    
    // 2. Universe Specifics
    if (uni_sign > 0.0) {
        // --- UNIVERSE A (BLUE) ---
        // Galactic Plane (used for structure)
        float band = 1.0 - smoothstep(0.0, 0.4, abs(dir.y));
        band = pow(band, 6.0);
        
        // Moving Blue Nebula Clouds
        float clouds = fbm(safe_dir * 3.0 + vec3(u_time * 0.05, 0.0, 0.0));
        float cloud_core = smoothstep(0.25, 0.85, clouds);
        
        vec3 deep_blue = vec3(0.02, 0.05, 0.3) * clouds;
        vec3 bright_cyan = vec3(0.1, 0.6, 1.2) * pow(cloud_core, 1.5) * 1.5;
        vec3 white_haze = vec3(0.9, 0.95, 1.0) * pow(cloud_core, 2.5) * 2.0;
        
        
        col += deep_blue + bright_cyan + white_haze;
        
        // Add Galaxies (Universe A)
        // Galaxy 1: Large Spiral overhead
        col += render_galaxy(dir, normalize(vec3(0.3, 0.8, 0.2)), vec3(1.0, 0.0, 0.0), 0.35, vec3(0.6, 0.8, 1.0));
        // Galaxy 2: Small distinct one
        col += render_galaxy(dir, normalize(vec3(-0.7, -0.3, 0.5)), vec3(0.0, 1.0, 0.0), 0.2, vec3(0.8, 0.9, 1.0));
        
    } else {
        // --- UNIVERSE B (RED) ---
        // Cinematic Interstellar Look
        float clouds = fbm(safe_dir * 3.0 + vec3(0.0, u_time * 0.08, 0.0));
        float cloud_core = smoothstep(0.35, 0.8, clouds); // Sharper core
        
        vec3 red_glow = vec3(0.4, 0.08, 0.05) * clouds;
        vec3 gold_fire = vec3(1.2, 0.7, 0.3) * pow(cloud_core, 1.2) * 2.2;
        
        col += red_glow + gold_fire;
        
        // Add Galaxies (Universe B)
        // Galaxy 1: Golden spiral
        col += render_galaxy(dir, normalize(vec3(-0.5, 0.6, -0.4)), vec3(0.0, 0.0, 1.0), 0.4, vec3(1.0, 0.8, 0.4));
        // Galaxy 2: Distant red companion
        col += render_galaxy(dir, normalize(vec3(0.8, -0.2, -0.3)), vec3(0.0, 1.0, 0.0), 0.25, vec3(1.0, 0.4, 0.2));
    }
    
    return col;
}

// --- PHYSICS ENGINE ---
struct State { float l; float th; float ph; float vl; float vth; float vph; };

State derivatives(State s) {
    float r2 = s.l*s.l + u_throat*u_throat;
    float sin_th = sin(s.th);
    if (abs(sin_th) < 0.001) sin_th = 0.001 * sign(sin_th); // Pole safety
    float cos_th = cos(s.th);

    State d;
    d.l = s.vl; d.th = s.vth; d.ph = s.vph;
    d.vl  = s.l * (s.vth*s.vth + sin_th*sin_th * s.vph*s.vph);
    d.vth = -(2.0*s.l/r2)*s.vl*s.vth + sin_th*cos_th*s.vph*s.vph;
    d.vph = -(2.0*s.l/r2)*s.vl*s.vph - 2.0*(cos_th/sin_th)*s.vth*s.vph;
    return d;
}

State rk4(State s, float h) {
    State k1 = derivatives(s);
    State s2 = s; s2.l+=k1.l*h*0.5; s2.th+=k1.th*h*0.5; s2.ph+=k1.ph*h*0.5; s2.vl+=k1.vl*h*0.5; s2.vth+=k1.vth*h*0.5; s2.vph+=k1.vph*h*0.5;
    State k2 = derivatives(s2);
    State s3 = s; s3.l+=k2.l*h*0.5; s3.th+=k2.th*h*0.5; s3.ph+=k2.ph*h*0.5; s3.vl+=k2.vl*h*0.5; s3.vth+=k2.vth*h*0.5; s3.vph+=k2.vph*h*0.5;
    State k3 = derivatives(s3);
    State s4 = s; s4.l+=k3.l*h; s4.th+=k3.th*h; s4.ph+=k3.ph*h; s4.vl+=k3.vl*h; s4.vth+=k3.vth*h; s4.vph+=k3.vph*h;
    State k4 = derivatives(s4);
    
    State f = s;
    f.l += (h/6.0)*(k1.l + 2.0*k2.l + 2.0*k3.l + k4.l);
    f.th += (h/6.0)*(k1.th + 2.0*k2.th + 2.0*k3.th + k4.th);
    f.ph += (h/6.0)*(k1.ph + 2.0*k2.ph + 2.0*k3.ph + k4.ph);
    f.vl += (h/6.0)*(k1.vl + 2.0*k2.vl + 2.0*k3.vl + k4.vl);
    f.vth += (h/6.0)*(k1.vth + 2.0*k2.vth + 2.0*k3.vth + k4.vth);
    f.vph += (h/6.0)*(k1.vph + 2.0*k2.vph + 2.0*k3.vph + k4.vph);
    return f;
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / u_resolution.y;
    
    // Apply FOV Zoom (Scaling the sensor plane)
    vec3 cam_right = u_cam_right * u_fov_scale;
    vec3 cam_up = u_cam_up * u_fov_scale;

    // Camera ray direction
    vec3 rd = normalize(u_cam_forward + uv.x * cam_right + uv.y * cam_up);
    
    // Initial State
    float cl = u_cam_pos.x;
    float rl = sqrt(cl*cl + u_throat*u_throat);
    
    vec3 er  = vec3(sin(u_cam_pos.y)*cos(u_cam_pos.z), sin(u_cam_pos.y)*sin(u_cam_pos.z), cos(u_cam_pos.y));
    vec3 eth = vec3(cos(u_cam_pos.y)*cos(u_cam_pos.z), cos(u_cam_pos.y)*sin(u_cam_pos.z), -sin(u_cam_pos.y));
    vec3 eph = vec3(-sin(u_cam_pos.z), cos(u_cam_pos.z), 0.0);
    
    State s; s.l=cl; s.th=u_cam_pos.y; s.ph=u_cam_pos.z;
    s.vl = dot(rd, er);
    s.vth = dot(rd, eth) / rl;
    s.vph = dot(rd, eph) / (rl * sin(u_cam_pos.y));
    
    // Raymarch
    float min_dist_to_throat = abs(s.l);
    float throat_glow_acc = 0.0;
    
    for(int i=0; i<600; i++) {
        // Adaptive Step Size
        float dist = abs(s.l);
        float h = 0.15;
        if (dist < 3.0) h = 0.02;
        else if (dist < 6.0) h = 0.06;
        
        s = rk4(s, h);
        
        // Volumetric Glow
        float density = exp(-s.l*s.l * 0.5);
        throat_glow_acc += density * h * 0.015;
        
        if (abs(s.l) < min_dist_to_throat) min_dist_to_throat = abs(s.l);
        if (abs(s.l) > MAX_DIST) break;
    }
    
    // Resolve
    float final_uni = (s.l > 0.0) ? 1.0 : -1.0;
    vec3 final_dir = vec3(sin(s.th)*cos(s.ph), sin(s.th)*sin(s.ph), cos(s.th));
    
    vec3 col = get_sky(final_dir, final_uni);
    
    // Photon Ring
    float glow = smoothstep(0.4, 0.0, min_dist_to_throat);
    float sharp_ring = smoothstep(0.05, 0.0, abs(min_dist_to_throat - 0.1));
    
    vec3 ring_color = vec3(1.0, 0.8, 0.6);
    col += ring_color * glow * 0.5;
    col += vec3(1.0) * sharp_ring * 0.8;

    // Accretion Disk Hint
    float disk_mask = 1.0 - smoothstep(0.0, 0.15, abs(s.th - 1.57));
    float disk_intensity = smoothstep(4.0, 1.6, min_dist_to_throat); 
    col += vec3(0.9, 0.7, 0.5) * disk_mask * disk_intensity * 0.4;
    
    // Volumetric Throat Glow
    col += vec3(0.4, 0.8, 1.0) * throat_glow_acc * u_glow_strength;

    // Gamma
    col = pow(col, vec3(0.4545));
    f_color = vec4(col, 1.0);
}
'''

def main():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    ctx = moderngl.create_context()

    prog = ctx.program(
        vertex_shader="#version 330\nin vec2 in_vert; void main() { gl_Position = vec4(in_vert, 0.0, 1.0); }",
        fragment_shader=FRAGMENT_SHADER,
    )
    vbo = ctx.buffer(np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4'))
    vao = ctx.simple_vertex_array(prog, vbo, 'in_vert')
    
    # Init Stats
    cam_l, cam_th, cam_ph = -15.0, math.pi/2, 0.0 
    cam_yaw, cam_pitch = math.pi/2, 0.0001
    vel_l = 0.0
    
    # Visualization State
    show_glow = True
    show_hud = True
    mouse_smoothing = False # Toggle with 'M'
    
    # Cinematic Mode State
    cinematic_mode = False
    cinematic_timer = 0.0
    
    # Smooth inputs
    target_yaw, target_pitch = cam_yaw, cam_pitch
    
    # Field of View (Zoom)
    fov_scale = 1.0 # 1.0 = Normal, <1.0 = Zoom In (Telephoto), >1.0 = Zoom Out (Wide)
    target_fov = 1.0
    
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    start_time = pygame.time.get_ticks()
    
    running = True
    while running:
        raw_dt = clock.tick(60) / 1000.0
        dt = min(raw_dt, 0.05)
        time_sec = (pygame.time.get_ticks() - start_time) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_z: show_glow = not show_glow
                if event.key == pygame.K_h: show_hud = not show_hud # Toggle HUD
                if event.key == pygame.K_m: mouse_smoothing = not mouse_smoothing # Toggle Smoothing
                if event.key == pygame.K_c: # Cinematic Trigger
                    cinematic_mode = True
                    cinematic_timer = 0.0
                    mouse_smoothing = True # Enforce smoothing for cinematic feel
                    # Teleport to start
                    cam_l = -20.0
                    vel_l = 0.0
                    cam_th = math.pi/2
                    cam_ph = 0.0
                    cam_yaw = math.pi/2
                    cam_pitch = 0.0
                    target_yaw = cam_yaw
                    target_pitch = cam_pitch
                    target_fov = 1.0

                if event.key == pygame.K_r: # Reset
                    cinematic_mode = False
                    cam_l, cam_th, cam_ph = -15.0, math.pi/2, 0.0
                    cam_yaw, cam_pitch = math.pi/2, 0.0001
                    target_yaw, target_pitch = cam_yaw, cam_pitch
                    vel_l = 0.0
                    target_fov = 1.0
                    fov_scale = 1.0
                    
            if event.type == pygame.MOUSEMOTION:
                dx, dy = event.rel
                # Accumulate into target
                target_yaw -= dx * MOUSE_SENSITIVITY
                target_pitch -= dy * MOUSE_SENSITIVITY
                target_pitch = max(-1.5, min(1.5, target_pitch))
                
                # If smoothing is off, snap directly
                if not mouse_smoothing:
                    cam_yaw = target_yaw
                    cam_pitch = target_pitch
            
            if event.type == pygame.MOUSEWHEEL:
                # Zoom in/out
                target_fov -= event.y * 0.1
                target_fov = max(0.2, min(2.0, target_fov)) # Clamp zoom
                
        # Camera Smoothing Logic
        if mouse_smoothing:
            # Exponential decay for cinematic 'heavy' feel
            smooth_factor = 10.0 * dt
            cam_yaw += (target_yaw - cam_yaw) * smooth_factor
            cam_pitch += (target_pitch - cam_pitch) * smooth_factor
        
        # Cinematic Sequence Logic
        if cinematic_mode:
            cinematic_timer += dt
            
            # Phase 1: Travel through wormhole (0s - 7s)
            if cinematic_timer <= 7.0:
                # Smooth interpolation from -20 to 5
                t = cinematic_timer / 7.0
                # Smoothstep for velocity ramp up/down
                t_smooth = t * t * (3.0 - 2.0 * t) 
                cam_l = -20.0 + (5.0 - (-20.0)) * t_smooth
                
                # Force look forward
                target_yaw = math.pi/2
                target_pitch = 0.0
                
            # Phase 2: Rotate to look back (7s - 12s)
            elif cinematic_timer <= 12.0:
                # Drift forward slowly
                cam_l += 0.5 * dt
                
                # Rotate 180 degrees
                local_t = (cinematic_timer - 7.0) / 5.0
                # Smooth rotation
                rot_t = local_t * local_t * (3.0 - 2.0 * local_t)
                target_yaw = math.pi/2 + (math.pi * rot_t)
                
            else:
                # End cinematic mode
                cinematic_mode = False
        
        # FOV Smoothing (Always smooth intentionally)
        fov_scale += (target_fov - fov_scale) * 5.0 * dt

        keys = pygame.key.get_pressed()
        throttle = 0.0
        if keys[pygame.K_w]: throttle += 1.0
        if keys[pygame.K_s]: throttle -= 1.0
        
        # Physics with drag
        vel_l += throttle * MOVE_SPEED * dt
        vel_l *= 0.92 
        cam_l += vel_l * dt
        
        # Orbit
        rl = math.sqrt(THROAT_SIZE**2 + cam_l**2)
        if keys[pygame.K_d]: cam_ph -= (10.0 * dt) / rl
        if keys[pygame.K_a]: cam_ph += (10.0 * dt) / rl

        # --- MATH ---
        forward = np.array([
            math.cos(cam_pitch) * math.sin(cam_yaw),
            math.sin(cam_pitch),
            math.cos(cam_pitch) * math.cos(cam_yaw)
        ], dtype='f4')
        
        right = np.cross(forward, np.array([0,1,0], dtype='f4'))
        if np.linalg.norm(right) < 0.001: right = np.array([1,0,0], dtype='f4')
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)

        # --- HUD LOGIC ---
        if show_hud:
            uni_code = "UNIVERSE A (BLUE)" if cam_l > 0 else "UNIVERSE B (RED)"
            heading = int(math.degrees(cam_yaw) % 360)
            pitch_deg = int(math.degrees(cam_pitch))
            
            mode_text = "AUTO-CINEMA" if cinematic_mode else ("CINEMATIC" if mouse_smoothing else "RESPONSIVE")
            vis_mode = "GLOW" if show_glow else "CLEAR"
            
            hud_text = f"[{uni_code}] [CAM: {mode_text}] [VIS: {vis_mode}]  HDG: {heading:03d}  ZOOM: {1.0/fov_scale:.1f}x  ||  DIST: {abs(cam_l):.2f} ly"
            pygame.display.set_caption(hud_text)
        else:
            pygame.display.set_caption("Wormhole Cinematic Recorder")

        # --- RENDER ---
        # Get Dynamic Resolution
        current_w, current_h = pygame.display.get_surface().get_size()
        
        try:
            if 'u_resolution' in prog: prog['u_resolution'].value = (current_w, current_h)
            if 'u_cam_pos' in prog: prog['u_cam_pos'].value = (cam_l, cam_th, cam_ph)
            if 'u_cam_forward' in prog: prog['u_cam_forward'].value = tuple(forward)
            if 'u_cam_right' in prog: prog['u_cam_right'].value = tuple(right)
            if 'u_cam_up' in prog: prog['u_cam_up'].value = tuple(up)
            if 'u_throat' in prog: prog['u_throat'].value = THROAT_SIZE
            if 'u_time' in prog: prog['u_time'].value = time_sec
            if 'u_glow_strength' in prog: prog['u_glow_strength'].value = 1.0 if show_glow else 0.0
            if 'u_fov_scale' in prog: prog['u_fov_scale'].value = fov_scale
        except Exception: pass
        
        # Viewport update for resizing
        ctx.viewport = (0, 0, current_w, current_h)

        vao.render(moderngl.TRIANGLE_STRIP)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()