import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

def create_animation():
    # 1. Setup the figure and 3D axis
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 2. Define the start and end points of the line
    # Starting at origin (0,0,0) and going to (3, 4, 2)
    start_point = np.array([0, 0, 0])
    end_point = np.array([3, 4, 2])
    
    # Generate points along the line for the animation
    num_frames = 100
    x_line = np.linspace(start_point[0], end_point[0], num_frames)
    y_line = np.linspace(start_point[1], end_point[1], num_frames)
    z_line = np.linspace(start_point[2], end_point[2], num_frames)

    # 3. Setup the plot aesthetics
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_zlim(0, 5)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    # Add the equation from your storyboard as the title
    ax.set_title(r"Euclidean Metric: $ds^2 = dx^2 + dy^2 + dz^2$", fontsize=14, pad=20)

    # Initialize the line object (empty at first)
    line, = ax.plot([], [], [], color='blue', linewidth=2, marker='o', markevery=[-1])
    
    # Optional: Draw the static "shadow" lines (components) to show Pythagoras context
    # This draws dashed lines showing dx, dy, dz logic immediately
    ax.plot([3, 3], [0, 4], [0, 0], 'k--', alpha=0.3) # y-component
    ax.plot([0, 3], [0, 0], [0, 0], 'k--', alpha=0.3) # x-component
    ax.plot([3, 3], [4, 4], [0, 2], 'k--', alpha=0.3) # z-component

    # 4. Animation initialization function
    def init():
        line.set_data([], [])
        line.set_3d_properties([])
        return line,

    # 5. Animation update function
    def update(frame):
        # Update the line to draw up to the current frame
        line.set_data(x_line[:frame], y_line[:frame])
        line.set_3d_properties(z_line[:frame])
        
        # Optional: Slowly rotate the camera for better 3D depth perception
        ax.view_init(elev=20, azim=45 + frame/10)
        
        return line,

    # 6. Create and save the animation
    print("Generating animation...")
    anim = FuncAnimation(fig, update, frames=num_frames, init_func=init, blit=False, interval=50)
    
    # Save as MP4
    output_file = 'euclidean_line.mp4'
    anim.save(output_file, writer='ffmpeg', fps=30)
    print(f"Animation saved as {output_file}")

if __name__ == "__main__":
    create_animation()