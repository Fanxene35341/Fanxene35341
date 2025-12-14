import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Initialize Pygame and OpenGL
pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Exploration Game")

# Set up perspective
gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
glTranslatef(0.0, -1.5, -5)

# Enable depth testing
glEnable(GL_DEPTH_TEST)

# Camera position and rotation
camera_pos = [0, 0, 0]
camera_rot = [0, 0]  # [pitch, yaw]

# Mouse settings
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

def draw_cube(x, y, z, size=1):
    """Draw a cube at given position"""
    vertices = [
        [x-size, y-size, z-size], [x+size, y-size, z-size],
        [x+size, y+size, z-size], [x-size, y+size, z-size],
        [x-size, y-size, z+size], [x+size, y-size, z+size],
        [x+size, y+size, z+size], [x-size, y+size, z+size]
    ]
    
    edges = [
        (0,1), (1,2), (2,3), (3,0),
        (4,5), (5,6), (6,7), (7,4),
        (0,4), (1,5), (2,6), (3,7)
    ]
    
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_ground():
    """Draw a grid ground"""
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-20, 21, 2):
        glVertex3f(i, -2, -20)
        glVertex3f(i, -2, 20)
        glVertex3f(-20, -2, i)
        glVertex3f(20, -2, i)
    glEnd()

def draw_scene():
    """Draw the 3D scene"""
    # Draw ground
    draw_ground()
    
    # Draw cubes
    glColor3f(1, 0, 0)
    draw_cube(0, 0, 0, 0.5)
    
    glColor3f(0, 1, 0)
    draw_cube(3, 0, 2, 0.5)
    
    glColor3f(0, 0, 1)
    draw_cube(-3, 0, -2, 0.5)
    
    glColor3f(1, 1, 0)
    draw_cube(5, 0, -5, 0.5)
    
    glColor3f(1, 0, 1)
    draw_cube(-5, 0, 5, 0.5)

def main():
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEMOTION:
                # Mouse look
                camera_rot[1] += event.rel[0] * 0.2
                camera_rot[0] -= event.rel[1] * 0.2
                # Clamp pitch
                camera_rot[0] = max(-90, min(90, camera_rot[0]))
        
        # Keyboard movement
        keys = pygame.key.get_pressed()
        move_speed = 0.1
        
        # Calculate forward/right vectors based on yaw
        yaw_rad = math.radians(camera_rot[1])
        forward = [math.sin(yaw_rad), 0, -math.cos(yaw_rad)]
        right = [math.cos(yaw_rad), 0, math.sin(yaw_rad)]
        
        if keys[K_w]:  # Forward
            for i in range(3):
                camera_pos[i] += forward[i] * move_speed
        if keys[K_s]:  # Backward
            for i in range(3):
                camera_pos[i] -= forward[i] * move_speed
        if keys[K_a]:  # Left
            for i in range(3):
                camera_pos[i] -= right[i] * move_speed
        if keys[K_d]:  # Right
            for i in range(3):
                camera_pos[i] += right[i] * move_speed
        if keys[K_SPACE]:  # Up
            camera_pos[1] += move_speed
        if keys[K_LSHIFT]:  # Down
            camera_pos[1] -= move_speed
        
        # Clear and set up camera
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Apply camera rotation
        glRotatef(camera_rot[0], 1, 0, 0)  # Pitch
        glRotatef(camera_rot[1], 0, 1, 0)  # Yaw
        
        # Apply camera position
        glTranslatef(-camera_pos[0], -camera_pos[1], -camera_pos[2])
        
        # Draw scene
        draw_scene()
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()