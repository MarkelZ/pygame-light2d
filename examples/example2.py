# Imports
import pygame
import time
from math import sin, pi
import random

import pygame_light2d as pl2d
from pygame_light2d import LightingEngine, PointLight, Hull

# Initialize pygame
pygame.init()

# Create lights engine
screen_res = (1280, 720)
native_res = (320, 180)
lights_engine = LightingEngine(
    screen_res=screen_res, native_res=native_res, lightmap_res=native_res)

# Initialize the clock
clock = pygame.time.Clock()

# Set the ambient light
lights_engine.set_ambient(128, 128, 128, 128)

# Load the background image
tex_background = lights_engine.load_texture('assets/backg.png')


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
light_radius = 175
light_pow = 1.2
light = PointLight(position=(0, 0), power=light_pow, radius=light_radius)

# Assign a random color to the light
r, g, b, a = random_color()
light.set_color(r, g, b, a)

# Add the point light to the engine
lights_engine.lights.append(light)

# Create a hull with the scene's geometry
vertices = [[16, 32], [128, 32], [128, 80], [144, 80], [144, 64], [256, 64], [256, 32], [
    304, 32], [304, 160], [208, 160], [208, 128], [272, 128], [272, 96], [160, 96], [160, 160],
    [96, 160], [96, 112], [64, 112], [64, 160], [16, 160]]
hull = Hull(vertices)

# Add the hull to the engine
lights_engine.hulls.append(hull)

# Initialize a font
# font = pygame.font.Font(size=16)
font = pygame.font.SysFont(name='arial', size=14)

# Game loop
running = True
mspt = 16
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)

    # Measure the raw time in seconds to later compute performance
    t1 = time.time()

    # Mouse pointer's position on the screen
    mp = pygame.mouse.get_pos()
    # Convert to native coordinates
    mouse_native_pos = [mp[0]*native_res[0]/screen_res[0],
                        mp[1] * native_res[1]/screen_res[1]]
    # Assign the mouse pointer's position to the light
    light.position = mouse_native_pos

    # Clear the background with black color
    lights_engine.clear(0, 0, 0)

    # Draw background image
    lights_engine.render_texture(
        tex_background, pl2d.BACKGROUND,
        pygame.Rect(0, 0, native_res[0], native_res[1]),
        pygame.Rect(0, 0, tex_background.width, tex_background.height))

    # Render text displaying the number of lights onto a Pygame surface
    text_sfc = font.render('LIGHT COUNT: ' + str(len(lights_engine.lights)), False,
                           (255, 255, 255, 255), (0, 0, 0, 0))
    # Convert the Pygame surface into a OpenGL texture
    text_tex = lights_engine.surface_to_texture(text_sfc)

    # Render the texture with the text in the foreground
    # The foreground is not affected by the lights
    text_rect = pygame.Rect(0, 0, text_sfc.get_width(), text_sfc.get_height())
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
            light = PointLight(position=(0, 0),
                               power=light_pow, radius=light_radius)

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
