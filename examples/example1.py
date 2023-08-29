import pygame
import pygame_light2d as pl2d
from pygame_light2d import LightingEngine, PointLight, Hull


# Initialize pygame
pygame.init()

# Create a lighting engine
screen_res = (1280, 720)
native_res = (320, 180)
lights_engine = LightingEngine(
    screen_res=screen_res, native_res=native_res, lightmap_res=native_res)

# Set the ambient light to 50%
lights_engine.set_ambient(128, 128, 128, 128)

# Load two sprites
sprite = lights_engine.load_texture('assets/dragon.png')

# Create and add a light
light = PointLight(position=(0, 0), power=1., radius=250)
light.set_color(50, 100, 200, 200)
lights_engine.lights.append(light)

# Create and add a hull
vertices = [(125, 50), (200, 50), (200, 125), (125, 125)]
hull = Hull(vertices)
lights_engine.hulls.append(hull)

# Game loop
clock = pygame.time.Clock()
running = True
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)

    # Mouse pointer's position on the screen
    mp = pygame.mouse.get_pos()
    # Convert to native coordinates
    mouse_native_pos = [mp[0]*native_res[0]/screen_res[0],
                        mp[1]*native_res[1]/screen_res[1]]
    # Assign the mouse pointer's position to the light
    light.position = mouse_native_pos

    # Clear the background with black color
    lights_engine.clear(255, 255, 255)

    # Render sprite1 in the background
    lights_engine.render_texture(
        sprite, pl2d.BACKGROUND,
        pygame.Rect(40, 50, sprite.width, sprite.height),
        pygame.Rect(0, 0, sprite.width, sprite.height))

    # Render sprite2 in the foreground
    lights_engine.render_texture(
        sprite, pl2d.FOREGROUND,
        pygame.Rect(210, 50, sprite.width, sprite.height),
        pygame.Rect(0, 0, sprite.width, sprite.height))

    # Render the scene
    lights_engine.render()

    # Update the display
    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
