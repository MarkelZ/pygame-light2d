import moderngl
import pygame
import numpy as np
from enum import Enum


class Layer(Enum):
    BACKGROUND = 1,
    FOREGROUND = 2,


class LightingEngine:

    def __init__(self, width: int, height: int) -> None:
        # Screen resolution
        self.width = width
        self.height = height

        # Ambient light
        self.ambient = (0., 0., 0., .5)

        # Light and hull lists
        self.lights = []
        self.hulls = []

        # The below code should be split into helper functions
        # for readability

        # Configure pygame
        if not pygame.get_init():
            pygame.init()

        pygame.display.set_mode(
            (width, height), pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

        # Create an OpenGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Load shaders
        vertex_filepath = 'shaders/vertex.glsl'
        fragment_filepath_light = 'shaders/fragment_light.glsl'
        fragment_filepath_blur = 'shaders/fragment_blur.glsl'
        fragment_filepath_mask = 'shaders/fragment_mask.glsl'

        with open(vertex_filepath, 'r') as f:
            vertex_src = f.read()

        with open(fragment_filepath_light, 'r') as f:
            fragment_src_light = f.read()

        with open(fragment_filepath_blur, 'r') as f:
            fragment_src_blur = f.read()

        with open(fragment_filepath_mask, 'r') as f:
            fragment_src_mask = f.read()

        self.prog_light = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_light)

        self.prog_blur = self.ctx.program(vertex_shader=vertex_src,
                                          fragment_shader=fragment_src_blur)

        self.prog_mask = self.ctx.program(vertex_shader=vertex_src,
                                          fragment_shader=fragment_src_mask)

        # Screen mesh
        vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                            (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                               (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
        data = np.hstack([vertices, tex_coords])

        # VAO and VBO
        vbo = self.ctx.buffer(data)
        self.vao_light = self.ctx.vertex_array(self.prog_light, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self.vao_blur = self.ctx.vertex_array(self.prog_blur, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self.vao_mask = self.ctx.vertex_array(self.prog_mask, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Layers
        self.background = self.ctx.texture((width, height), components=4)
        self.background.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._bg_fbo = self.ctx.framebuffer([self.background])
        self.foreground = self.ctx.texture((width, height), components=4)
        self.foreground.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fg_fbo = self.ctx.framebuffer([self.foreground])

        # Ambient occlussion map
        self.aomap = self.ctx.texture((width, height), components=4)
        self.aomap.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._lm_fbo = self.ctx.framebuffer([self.aomap])

    def _point_to_coord(self, p):
        return (p[0]/self.width, 1 - (p[1]/self.height))

    def create_texture(self, path: str):
        img = pygame.image.load(path).convert_alpha()
        img_flip = pygame.transform.flip(img, False, True)
        img_data = pygame.image.tostring(img_flip, 'RGBA')

        tex = self.ctx.texture(size=img.get_size(),
                               components=4, data=img_data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)

    def draw_texture(self, tex: moderngl.Texture, layer: Layer, position: tuple[int, int] = (0, 0)):
        pass

    def draw_surface(self, sfc: pygame.Surface, layer: Layer, position: tuple[int, int]):
        texture = LightingEngine._surface_to_texture(sfc)
        self.draw_texture(texture, layer, position)

    def clear(self, R=0, G=0, B=0, A=1):
        self._bg_fbo.clear()
        self._fg_fbo.clear()
        self._lm_fbo.clear()

    def render():
        pass

    def _surface_to_texture(sfc):
        pass

    def _render_layer(self, tex):
        pass

    def _render_lights():
        pass

    def add_light(self, light):
        pass

    def remove_light(self, light):
        pass

    def add_hull(self, hull):
        pass

    def remove_hull(self, hull):
        pass
