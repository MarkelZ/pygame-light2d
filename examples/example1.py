import pygame
import pygame_light2d as pl2d
from pygame_light2d import LightingEngine, PointLight, Hull


# Initialize pygame
pygame.init()

# Set 720p screen resolution
screen_res = (1280, 720)
pygame.display.set_mode(screen_res)

# Create a lighting engine
native_res = (320, 180)
lights_engine = LightingEngine(
    native_res=native_res, lightmap_res=native_res)

# Set the ambient light to 50%
lights_engine.ambient = [0.5 for _ in range(4)]

# Load two sprites
sprite1 = lights_engine.load_texture('assets/dragon.png')
sprite2 = lights_engine.load_texture('assets/dragon.png')

# Create and add a light
light = PointLight(position=(20, 20), power=1., radius=300)
light.set_color(50, 100, 200, 200)
lights_engine.lights.append(light)

# Create and add a hull
vertices = [(50, 50), (125, 50), (125, 125), (50, 125)]
hull = Hull(vertices)
lights_engine.hulls.append(hull)

# Game loop
clock = pygame.time.Clock()
running = True
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)

    # Clear the background with white
    lights_engine.clear(255, 255, 255)

    # Mouse pointer's position on the screen
    mp = pygame.mouse.get_pos()
    # Convert to native coordinates
    mouse_native_pos = [mp[0]*native_res[0]/screen_res[0],
                        mp[1]*native_res[1]/screen_res[1]]
    # Assign the mouse pointer's position to the light
    light.position = mouse_native_pos

    # Render sprite1 in the background
    lights_engine.render_texture(
        sprite1, pl2d.BACKGROUND,
        pygame.Rect(40, 30, sprite1.width, sprite1.height),
        pygame.Rect(0, 0, sprite1.width, sprite1.height))

    # Render sprite1 in the foreground
    lights_engine.render_texture(
        sprite1, pl2d.FOREGROUND,
        pygame.Rect(200, 60, sprite1.width, sprite1.height),
        pygame.Rect(0, 0, sprite1.width, sprite1.height))

    # Render the scene
    lights_engine.render()

    # Update the display
    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
