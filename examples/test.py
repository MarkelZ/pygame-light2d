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
screen = pygame.display.set_mode((width, height))

# The clock
clock = pygame.time.Clock()

# Create lights engine
lights_engine = engine.LightingEngine(width, height)

# Background image
tex_puppy = lights_engine.load_texture('puppies2.png')

# Create a point lights
light1 = PointLight(position=(100, 100), power=1., decay=10.)
light1.set_color(200, 100, 50, 255)

light2 = PointLight(position=(550, 550), power=.9, decay=10.)

lights_engine.lights.append(light1)
lights_engine.lights.append(light2)

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
vertices = generate_hull_vertices((600, 300), 200, 0)
hull1 = Hull(vertices)
lights_engine.hulls.append(hull1)


running = True
t = 0
mspt = 0
while running:
    clock.tick(60)

    t1 = time.time()

    t += 0.01

    # Rotate hull
    vertices = generate_hull_vertices((600, 300), 200, t)
    hull1.vertices = vertices

    # Move light1 to mouse pointer
    light1.position = pygame.mouse.get_pos()

    # Change light2 color
    r, g, b = sin(t)*255, sin(t+1)*255, sin(t + 2)*255
    light2.set_color(r, g, b)

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

    t2 = time.time()
    # Measure mspt
    mspt = (t2 - t1) * 1000
