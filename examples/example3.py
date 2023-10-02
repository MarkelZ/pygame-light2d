# Imports
import pygame
import time
from math import sin, cos, pi
import random

import pygame_light2d as pl2d
from pygame_light2d import LightingEngine, PointLight, Hull


# Initialize pygame
pygame.init()

# Create lights engine with the lightmap downscaled by 2.5
screen_res = (1280, 720)
lights_engine = LightingEngine(
    screen_res=screen_res, native_res=screen_res, lightmap_res=(int(screen_res[0]/2.5), int(screen_res[1]/2.5)))

# Initialize the clock
clock = pygame.time.Clock()

# Set the ambient light
lights_engine.set_ambient(128, 128, 128, 128)

# Load the background image
tex_background = lights_engine.load_texture('assets/puppies.png')


# Generate a random color
def random_color():
    theta = random.random()*pi
    theta2 = theta + pi/3
    theta2 = theta2 if theta2 < pi else theta2 - pi
    theta3 = theta2 + pi/3
    theta3 = theta3 if theta3 < pi else theta3 - pi
    sc = 200.
    return sc*sin(theta), sc*sin(theta2), sc*sin(theta3), 255.


# Create a point light
light_radius = 600
light_pow = 1.0
light = PointLight(position=(100, 100), power=light_pow, radius=light_radius)

# Assign a random color to the light
r, g, b, a = random_color()
light.set_color(r, g, b, a)

# Add the point light to the engine
lights_engine.lights.append(light)

# Define some constants that are used for computing the vertices of the square
PI2 = pi/2
PI3 = pi
PI4 = pi*3/2


# Generate the vertices of a square hull rotated by an angle
def generate_hull_vertices(pos, width, angle):
    x, y = pos

    v1 = [cos(angle)*width+x, sin(angle)*width+y]
    v2 = [cos(angle+PI2)*width+x, sin(angle+PI2)*width+y]
    v3 = [cos(angle+PI3)*width+x, sin(angle+PI3)*width+y]
    v4 = [cos(angle+PI4)*width+x, sin(angle+PI4)*width+y]

    return [v1, v2, v3, v4]


# Create a square shaped hull
vertices = generate_hull_vertices(pos=(600, 300), width=200, angle=0)
hull_square = Hull(vertices)

# Add the square hull to the engine
lights_engine.hulls.append(hull_square)

# Create a tirangle shaped hull
hull_triangle = Hull([[1000, 400], [1100, 586], [900, 586]])

# Add the triangular hull to the engine
lights_engine.hulls.append(hull_triangle)

# Initialize a font
font = pygame.font.Font(size=64)

# Game loop
running = True
hull_angle = 0
mspt = 16
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)

    # Measure the raw time in seconds to later compute performance
    t1 = time.time()

    # Rotate hull
    hull_angle += 0.01
    vertices = generate_hull_vertices((600, 300), 200, hull_angle)
    hull_square.vertices = vertices

    # Move the light to the mouse pointer's position
    light.position = pygame.mouse.get_pos()

    # Clear the background with black color
    lights_engine.clear(0, 0, 0)

    # Draw background image
    lights_engine.render_texture(
        tex_background, pl2d.BACKGROUND,
        pygame.Rect(0, 0, screen_res[0], screen_res[1]),
        pygame.Rect(0, 0, tex_background.width, tex_background.height))

    # Render text displaying the number of lights onto a Pygame surface
    text_sfc = font.render('Light count: ' + str(len(lights_engine.lights)), True,
                           (255, 255, 255, 255), (0, 0, 0, 0))
    # Convert the Pygame surface into a OpenGL texture
    text_tex = lights_engine.surface_to_texture(text_sfc)

    # Render the texture with the text in the foreground
    # The foreground is not affected by the lights
    text_rect = pygame.Rect(0, 0, text_sfc.get_width(),
                            text_sfc.get_height())
    lights_engine.render_texture(
        text_tex, pl2d.FOREGROUND, text_rect, text_rect)

    # Free the temporary texture from the memory
    text_tex.release()

    # Render the scene
    lights_engine.render()

    # Update the display
    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Create a new light
            light = PointLight(position=(100, 100),
                               power=1., radius=light_radius)
            # Assign a random color to the new light
            r, g, b, a = random_color()
            light.set_color(r, g, b, a)

            # Add the new light to the engine
            lights_engine.lights.append(light)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            # Remove all lights except for the mouse pointer
            lights_engine.lights.clear()
            lights_engine.lights.append(light)

    # Measure the time and compute milliseconds per tick (mspt)
    t2 = time.time()
    mspt = (t2 - t1) * 1000

    # Display mspt and fps
    pygame.display.set_caption(
        f'{mspt:.2f}' + ' mspt; ' + f'{clock.get_fps():.2f}' + ' fps')
