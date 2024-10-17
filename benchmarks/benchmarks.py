# Imports
import pygame
import time
import random as rnd

from pygame_light2d import LightingEngine, PointLight, Hull


def benchmark1(num_lights: int, num_hulls: int, num_hull_vertices: int, iters: int, seed: int = 0) -> float:
    rnd.seed(seed)

    # Initialize pygame
    pygame.init()

    time.sleep(0.5)

    # Create a lighting engine
    screen_res = (1280, 720)
    native_res = (320, 180)
    lights_engine = LightingEngine(
        screen_res=screen_res, native_res=native_res, lightmap_res=native_res)

    def rand_point():
        return [rnd.randint(0, native_res[0]), rnd.randint(0, native_res[1])]

    # Add lights
    for _ in range(num_lights):
        light = PointLight(position=rand_point(), power=1., radius=250)
        light.set_color(50, 100, 200, 200)
        lights_engine.lights.append(light)

    # Add hulls
    lights_engine.hulls += [Hull([rand_point() for _ in range(num_hull_vertices)]) for _ in range(num_hulls)]

    # Game loop
    mspt_accum = 0
    for _ in range(iters):

        # Get raw time at the start of render
        t1 = time.time()

        # Clear the background with black color
        lights_engine.clear(255, 255, 255)

        # Render the scene
        lights_engine.render()

        # Update the display
        pygame.display.flip()

        # Get raw time at the end of render
        t2 = time.time()
        mspt = (t2 - t1) * 1000

        mspt_accum += mspt

    avg_mspt = mspt_accum / iters
    return avg_mspt


if __name__ == '__main__':
    seed = 0

    runs = [
        {'lights': 10,
         'hulls': 10,
         'vertices': 4,
         'iters': 1000},
        {'lights': 200,
         'hulls': 1,
         'vertices': 3,
         'iters': 300},
        {'lights': 10,
         'hulls': 200,
         'vertices': 4,
         'iters': 300},
        {'lights': 200,
         'hulls': 200,
         'vertices': 4,
         'iters': 100},
    ]

    for i, run in enumerate(runs):
        print(f'======== Benchmark {i} ========')
        print(f"lights: {run['lights']}, hulls: {run['hulls']}, vertices per hull: {run['vertices']}")
        print('running...')
        avg_mspt = benchmark1(num_lights=run['lights'], num_hulls=run['hulls'], 
                              num_hull_vertices=run['vertices'], iters=run['iters'],
                              seed=seed)
        print(f'Avg. mspt: {avg_mspt}')
        print()


