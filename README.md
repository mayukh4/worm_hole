# Wormhole Metric and Geodesic Visualization

A high-performance physics simulation and ray tracing engine for Morris-Thorne wormholes. This project visualizes the spacetime geometry and light-ray trajectories (geodesics) in the vicinity of a traversable wormhole.

## Table of Contents
- [Physics and Mathematics](#physics-and-mathematics)
- [Project Architecture](#project-architecture)
- [Ray Tracing Engine](#ray-tracing-engine)
- [Installation](#installation)
- [Usage](#usage)

## Physics and Mathematics

### The Morris-Thorne Metric
The simulations are based on the Morris-Thorne metric, which describes a traversable wormhole. The spacetime metric in Schwarzschild-like coordinates $(t, r, \theta, \phi)$ is given by:

$$ds^2 = -c^2 dt^2 + \frac{dr^2}{1 - \frac{b(r)}{r}} + r^2(d\theta^2 + \sin^2\theta d\phi^2)$$

For a simple wormhole with a constant throat radius $b$, we use the substitution $b(r) = b$. In many of our visualizations, we use the proper radial distance $l$ instead of $r$, where:
$l = \pm \int_{b}^{r} \frac{dr}{\sqrt{1 - b/r}}$
This maps the two universes to $l > 0$ and $l < 0$, meeting at the throat ($l=0$).

### Geodesic Equations
Geodesics describe the paths of light rays. By extremizing the Lagrangian:
$$\mathcal{L} = \frac{1}{2} g_{\mu\nu} \dot{x}^\mu \dot{x}^\nu$$
For the equatorial plane ($\theta = \pi/2$), we derive the coupled second-order differential equations:

1. $\frac{d^2l}{d\tau^2} = r(l) (\dot{\theta}^2 + \sin^2\theta \dot{\phi}^2)$
2. $\frac{d^2\phi}{d\tau^2} = -\frac{2}{r} \frac{dr}{dl} \dot{l} \dot{\phi}$

In the code, these are reduced to a system of first-order ODEs and integrated using the **4th-order Runge-Kutta (RK4)** method for high stability and precision near the high-curvature throat region.

## Project Architecture

- **`wormhole_2d.py`**: A top-down 2D visualization of light rays being deflected or transmitted through the wormhole. It uses PyGame for rendering and RK4 for physics integration.
- **`wormhole_cinema_final.py`**: The flagship 3D cinematic visualizer. It implements a GPU-accelerated ray tracer using OpenGL shaders to render the wormhole in real-time.
- **`Explantion_scripts/`**:
    - `wormhole_embedding.py`: Visualizes the "flamm's paraboloid" style embedding diagram in 3D.
    - `wormhole_physics.py`: Demonstrates the exotic matter and tension requirements ($10^{34}$ Pa) to keep the throat open.
    - `shaders.py`: A pedagogical tool comparing CPU vs GPU parallel processing performance.

## Ray Tracing Engine

The engine uses **Relativistic Ray Tracing**. Unlike standard Euclidean ray tracers:
1. Every pixel on the screen spawns a ray.
2. The initial state is defined by the camera's position and orientation in the curved spacetime.
3. The ray position is integrated step-by-step using the geodesic equations.
4. If the ray reaches $l < 0$, it is sampling the "Other" universe (Universe B).
5. Background stars and nebulae are generated using **Fractal Brownian Motion (FBM)** noise directly in the fragment shader.

### OpenGL Integration
We utilize **ModernGL** to interface with OpenGL 3.3+. The heavy lifting is done in the `FRAGMENT_SHADER`, where each thread calculates a single geodesic integration for its corresponding pixel. This allows for real-time interaction at 60 FPS, which would be impossible on a sequential CPU-based integrator.

## Installation

### Prerequisites
- Python 3.8+
- OpenGL 3.3 compatible hardware

### Setup
1. Clone the repository.
2. Install dependencies using the provided `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Usage

### 3D Cinematic Visualizer
```bash
python wormhole_cinema_final.py
```
- **W/S**: Move Forward/Backward
- **A/D**: Orbit Left/Right
- **Mouse**: Look around
- **Scroll**: Zoom In/Out (FOV)
- **C**: Start Cinematic Fly-through
- **R**: Reset Camera
- **Z**: Toggle Volumetric Glow
- **H**: Toggle HUD

### 2D Geodesic Lab
```bash
python wormhole_2d.py
```
- **Mouse**: Move the light source.
- **Scroll**: Adjust the throat radius $(b)$ in real-time.
