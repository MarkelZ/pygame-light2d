# External packages
import pygame
import time
from math import sin, cos, pi

# My stuff
import engine
from light import PointLight
from hull import Hull


# Screen resolution
width = 1600
height = 900

# Initialize pygame
pygame.init()
pygame.display.set_mode((width, height))

# The clock
clock = pygame.time.Clock()

# Create lights engine
lights_engine = engine.LightingEngine(width, height)

# Background image
tex_puppy = lights_engine.load_texture('puppies2.png')

# Create a point light
light1 = PointLight(position=(100, 100), color=(100, 255, 150))
lights_engine.lights.append(light1)


# Generate the vertices of a square hull rotated by an angle
pi2 = pi/2
pi3 = pi
pi4 = pi*3/2


def generate_hull_vertices(pos, width, angle):
    x, y = pos

    v1 = [cos(angle)*width+x, sin(angle)*width+y]
    v2 = [cos(angle+pi2)*width+x, sin(angle+pi2)*width+y]
    v3 = [cos(angle+pi3)*width+x, sin(angle+pi3)*width+y]
    v4 = [cos(angle+pi4)*width+x, sin(angle+pi4)*width+y]

    return [v1, v2, v3, v4]


# Create a square shaped hull
vertices = generate_hull_vertices((600, 600), 200, 0)
hull1 = Hull(vertices)
lights_engine.hulls.append(hull1)


running = True
angle = 0
mspt = 0
while running:
    clock.tick(60)

    t1 = time.time()

    # Rotate hull
    angle += 0.01
    vertices = generate_hull_vertices((600, 300), 200, angle)
    hull1.vertices = vertices

    # Move light to mouse pointer
    light1.position = pygame.mouse.get_pos()

    lights_engine.clear(0, 0, 0)

    lights_engine.render_texture(
        tex_puppy, engine.BACKGROUND, pygame.Rect(0, 0, width, height), pygame.Rect(0, 0, tex_puppy.width, tex_puppy.height))
    lights_engine.render()

    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Display mspt and fps
    pygame.display.set_caption(
        f'{mspt:.2f}' + ' mspt; ' + f'{clock.get_fps():.2f}' + ' fps')

    # Measure mspt
    t2 = time.time()
    mspt = (t2 - t1) * 1000
