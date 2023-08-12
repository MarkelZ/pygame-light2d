# Pygame Light 2D
This module provides fast 2D dynamic lighting for `pygame`. 

https://github.com/MarkelZ/pygame-light2d/assets/60424316/f0233efd-2a54-4a84-8263-d3397f164565

## Dependencies

- `Python` version >= 3.10
- `numpy` >= 1.24.1
- `pygame` >= 2.3.0
- `moderngl` >= 5.8.2
- `PyOpenGL` >= 3.1.6

Earlier versions of these packages might also work, although they haven't been extensively tested.

## Installation

Firstly, ensure that all the required dependencies are installed.

Then, run the following command:

```sh
python3 -m pip install pygame-light2d
```

To verify correct installation, open a Python terminal and import the module:

```py
import pygame_light2d
```

If there are no errors, the installation was successful!

## License

This code is licensed under the terms of the MIT license.

## Adding 2D lights to your game

This section will guide you through creating a pixel-art game with 2D lighting.

If you prefer examining a working example, take a look at the examples directory.

We will start by importing `pygame`, as well as some components from the `pygame-light2d`:

```py
import pygame
import pygame_light2d as pl2d
from pygame_light2d import LightingEngine, PointLight, Hull
```

Now initialize `pygame` with a 720p resolution:

```py
pygame.init()

screen_res = (1280, 720)
pygame.display.set_mode(screen_res)
```

Now we will create a the lighting engine with a native resolution of 320x180:

```py
native_res = (320, 180)
lights_engine = LightingEngine(
    native_res=native_res, lightmap_res=native_res)
```

The game scene will be rendered at the native resolution and then scaled to fit the screen resolution.

Since the native resolution is lower than the screen resolution, this means that we will get a pixelated image, which is what we are aiming for as we are making a pixel-art game. 

If you don't want pixelation, you can adjust it like this:

```py
lightmap_res = (screen_res[0]//3, screen_res[1]//3)
lights_engine = LightingEngine(
    native_res=screen_res, lightmap_res=lightmap_res)
```

This sets the native resolution the same as the screen resolution, getting rid of the pixels, while downscaling the lightmap's resolution for faster rendering and softer shadows.

Set the ambient light to 50% brightness:

```py
lights_engine.ambient = [0.5 for _ in range(4)]
```

Textures are loaded via the lighting engine. Let's load two sprites named `sprite1.png` and `sprite2.png` from the `assets/` directory:

```py
sprite1 = lights_engine.load_texture('assets/sprite1.png')
sprite2 = lights_engine.load_texture('assets/sprite2.png')
```

The reason for loading the textures through the engine instead of through `pygame` is that the engine creates OpenGL textures, which are much faster to render.

Now let's add a blue light:

```py
light = PointLight(position=(20, 20), power=1., radius=300)
light.set_color(50, 100, 200, 200)
lights_engine.lights.append(light)
```

Add a square-shaped hull at position (50, 50) with a side length of 75:

```py
vertices = [(50, 50), (125, 50), (125, 125), (50, 125)]
hull = Hull(vertices)
lights_engine.hulls.append(hull)
```

We will now create a simple game loop with `pygame`:

```py
clock = pygame.time.Clock()
running = True
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)

    # Game logic here!
    # ...

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

```

For more information about this loop, visit https://www.pygame.org/docs/

The remaining code for this example will be placed where the comment `# Game logic here!` is located within the loop.

First, we will have the light follow the mouse pointer. Obtain the mouse pointer's location:

```py
    mp = pygame.mouse.get_pos()
```

The mouse's position is given in screen coordinates. We need to convert it to the game's native coordinates:

```py
    mouse_native_pos = [mp[0]*native_res[0]/screen_res[0],
                        mp[1]*native_res[1]/screen_res[1]]
```

We can assign the position to the light

```py
    light.position = mouse_native_pos
```

We will now render the scene. For that, we start by clearing the screen with color white:

```py
    lights_engine.clear(255, 255, 255)
```

Now, render the first sprite in the background at position (40, 30):

```py
    lights_engine.render_texture(
        sprite1, pl2d.BACKGROUND,
        pygame.Rect(40, 30, sprite1.width, sprite1.height),
        pygame.Rect(0, 0, sprite1.width, sprite1.height))
```

Render the second sprite in the foreground at position 

```py
    lights_engine.render_texture(
        sprite1, pl2d.FOREGROUND,
        pygame.Rect(200, 60, sprite2.width, sprite2.height),
        pygame.Rect(0, 0, sprite2.width, sprite2.height))
```

Sprites rendered in the background are affected by the lights and shadows in the scene. This is how most game components would be drawn, such as the player, background, enemies, etc.

Sprites rendered in the foreground are shown in full brightness, unaffected by the ligthing. This is useful for displaying things like the HUD or menu components.

Now the scene can be rendered:

```py
    lights_engine.render()
```

Finally, we update the `pygame` display:

```py
    pygame.display.flip()
```

If everything went right, you should now have a working template for your game! 

If you encounter any issues, refer to [`examples/example1.py`](examples/example1.py).
It contains very similar code to what has been shown in this guide.
