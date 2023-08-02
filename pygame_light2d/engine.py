import moderngl
import pygame
import numpy as np
from enum import Enum
from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST
# from OpenGL.GL import *
# from OpenGL.GLU import *

from light import PointLight
from hull import Hull


class Layer(Enum):
    BACKGROUND = 1,
    FOREGROUND = 2,


BACKGROUND = Layer.BACKGROUND
FOREGROUND = Layer.FOREGROUND


class LightingEngine:

    def __init__(self, native_res: tuple[int, int], lightmap_res: tuple[int, int]) -> None:
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Please, initialize Pygame before the lighting engine.'

        # Try to get the current screen resolution
        try:
            screen_size = pygame.display.get_window_size()
        except:
            assert False, 'Please, initialize a pygame window before starting the lighting engine.'

        # Set the native and lightmap resolutions
        self.native_res = native_res
        self.lightmap_res = lightmap_res

        # Set the ambient light
        self.ambient = (.25, .25, .25, .25)

        # Initialize the light and hull lists
        self.lights: list[PointLight] = []
        self.hulls: list[Hull] = []

        # Configure pygame display
        pygame.display.set_mode(
            screen_size, pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

        # Create an OpenGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Load shaders
        vertex_filepath = 'shaders/vertex.glsl'
        fragment_filepath_light = 'shaders/fragment_light.glsl'
        fragment_filepath_blur = 'shaders/fragment_blur.glsl'
        fragment_filepath_mask = 'shaders/fragment_mask.glsl'
        fragment_filepath_draw = 'shaders/fragment_draw.glsl'

        with open(vertex_filepath, 'r') as f:
            vertex_src = f.read()

        with open(fragment_filepath_light, 'r') as f:
            fragment_src_light = f.read()

        with open(fragment_filepath_blur, 'r') as f:
            fragment_src_blur = f.read()

        with open(fragment_filepath_mask, 'r') as f:
            fragment_src_mask = f.read()

        with open(fragment_filepath_draw, 'r') as f:
            fragment_src_draw = f.read()

        self.prog_light = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_light)

        self.prog_blur = self.ctx.program(vertex_shader=vertex_src,
                                          fragment_shader=fragment_src_blur)

        self.prog_mask = self.ctx.program(vertex_shader=vertex_src,
                                          fragment_shader=fragment_src_mask)

        self.prog_draw = self.ctx.program(vertex_shader=vertex_src,
                                          fragment_shader=fragment_src_draw)

        # Screen mesh
        vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                            (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                               (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
        vertex_data = np.hstack([vertices, tex_coords])

        # VAO and VBO for screen mesh
        vbo = self.ctx.buffer(vertex_data)
        self.vao_light = self.ctx.vertex_array(self.prog_light, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self.vao_blur = self.ctx.vertex_array(self.prog_blur, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self.vao_mask = self.ctx.vertex_array(self.prog_mask, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Frame buffers
        self._tex_bg = self.ctx.texture(native_res, components=4)
        self._tex_bg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_bg = self.ctx.framebuffer([self._tex_bg])

        self._tex_fg = self.ctx.texture(native_res, components=4)
        self._tex_fg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_fg = self.ctx.framebuffer([self._tex_fg])

        # Double buffer for lights
        self._tex_lt1 = self.ctx.texture(
            lightmap_res, components=4, dtype='f2')
        self._tex_lt1.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._fbo_lt1 = self.ctx.framebuffer([self._tex_lt1])

        self._tex_lt2 = self.ctx.texture(
            lightmap_res, components=4, dtype='f2')
        self._tex_lt2.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._fbo_lt2 = self.ctx.framebuffer([self._tex_lt2])

        # Ambient occlussion map
        self._tex_ao = self.ctx.texture(
            lightmap_res, components=4, dtype='f2')
        self._tex_ao.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._fbo_ao = self.ctx.framebuffer([self._tex_ao])

        # SSBO for hull vertices
        self.ssbo_v = self.ctx.buffer(reserve=4*2048)
        self.ssbo_v.bind_to_uniform_block(1)
        self.ssbo_ind = self.ctx.buffer(reserve=4*256)
        self.ssbo_ind.bind_to_uniform_block(2)

    # TEMP
    def _point_to_uv(self, p: tuple[float, float]):
        return [p[0]/self.native_res[0], 1 - (p[1]/self.native_res[1])]

    def _length_to_uv(self, l: float):
        return l/self.native_res[0]

    def blit_texture(self, tex: moderngl.Texture, layer: Layer, dest: pygame.Rect, source: pygame.Rect):
        # Create a framebuffer with the texture
        fb = self.ctx.framebuffer([tex])

        # Select destination framebuffer correcponding to layer
        if layer == Layer.BACKGROUND:
            fbo = self._fbo_bg
        elif layer == Layer.FOREGROUND:
            fbo = self._fbo_fg

        # Blit texture onto destination
        glBlitNamedFramebuffer(fb.glo, fbo.glo, source.x, source.y, source.w, source.h,
                               dest.x, dest.y, dest.w, dest.h, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def render_texture(self, tex: moderngl.Texture, layer: Layer, dest: pygame.Rect, source: pygame.Rect):
        # Render texture onto layer with the draw shader
        if layer == Layer.BACKGROUND:
            fbo = self._fbo_bg
        elif layer == Layer.FOREGROUND:
            fbo = self._fbo_fg

        self._render_tex_to_fbo(tex, fbo, dest, source)

    def _render_tex_to_fbo(self, tex: moderngl.Texture, fbo: moderngl.Framebuffer, dest: pygame.Rect, source: pygame.Rect):
        # Mesh for destination rect on screen
        width, height = fbo.size
        x = 2. * dest.x / width - 1.
        y = 1. - 2. * dest.y / height
        w = 2. * dest.w / width
        h = 2. * dest.h / height
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)

        # Mesh for source within the texture
        x = source.x / tex.size[0]
        y = source.y / tex.size[1]
        w = source.w / tex.size[0]
        h = source.h / tex.size[1]

        p1 = (x, y + h)
        p2 = (x + w, y + h)
        p3 = (x, y)
        p4 = (x + w, y)
        tex_coords = np.array([p1, p2, p3,
                               p3, p2, p4], dtype=np.float32)

        # Create VBO and VAO
        buffer_data = np.hstack([vertices, tex_coords])

        vbo = self.ctx.buffer(buffer_data)
        vao = self.ctx.vertex_array(self.prog_draw, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use buffers and render
        tex.use()
        fbo.use()
        vao.render()

    # Clear background
    def clear(self, R=0, G=0, B=0, A=1):
        self._fbo_bg.clear(R, G, B, A)
        self._fbo_fg.clear(0, 0, 0, 0)

    def render(self):
        # Clear intermediate buffers
        self._fbo_ao.clear(0, 0, 0, 0)
        self._fbo_lt1.clear(0, 0, 0, 0)
        self._fbo_lt2.clear(0, 0, 0, 0)

        # SSBO with hull vertices and their indices
        vertices = []
        indices = []
        for hull in self.hulls:
            vertices += hull.vertices
            indices.append(len(vertices))

        # Store hull vertex data in SSBO
        vertices = [self._point_to_uv(v) for v in vertices]
        data_v = np.array(vertices, dtype=np.float32).flatten().tobytes()
        self.ssbo_v.write(data_v)

        # Store hull vertex indices in SSBO
        num_hulls = len(indices)
        data_ind = np.array(indices, dtype=np.int32).flatten().tobytes()
        self.ssbo_ind.write(data_ind)

        fbo_ind = 1

        self.ctx.disable(moderngl.BLEND)
        for light in self.lights:
            # Skip light if disabled
            if not light.enabled:
                continue

            # Flip double buff
            if fbo_ind == 1:
                self._fbo_lt1.use()
                self._tex_lt2.use()
                fbo_ind = 2
            elif fbo_ind == 2:
                self._fbo_lt2.use()
                self._tex_lt1.use()
                fbo_ind = 1

            # Send light uniforms
            self.prog_light['lightPos'] = self._point_to_uv(light.position)
            self.prog_light['lightCol'] = light._color
            self.prog_light['lightPower'] = light.power
            self.prog_light['radius'] = self._length_to_uv(light.radius)

            # Send number of hulls
            self.prog_light['numHulls'] = num_hulls

            # Render onto lightmap
            self.vao_light.render()
        self.ctx.enable(moderngl.BLEND)

        # Blur lightmap for soft shadows and render onto aomap
        self._fbo_ao.use()
        if fbo_ind == 1:
            self._tex_lt2.use()
        else:
            self._tex_lt1.use()
        self.vao_blur.render()

        # Render background masked with the lightmap
        self.ctx.screen.use()
        self._tex_bg.use()

        self._tex_ao.use(1)
        self.prog_mask['lightmap'].value = 1
        self.prog_mask['ambient'].value = self.ambient

        self.vao_mask.render()

        # Render foreground onto screen
        self._render_tex_to_fbo(self._tex_fg, self.ctx.screen,
                                pygame.Rect(0, 0, self.ctx.screen.width,
                                            self.ctx.screen.height),
                                pygame.Rect(0, 0, self._tex_fg.width, self._tex_fg.height))

    def surface_to_texture(self, sfc: pygame.Surface):
        img_flip = pygame.transform.flip(sfc, False, True)
        img_data = pygame.image.tostring(img_flip, "RGBA")

        tex = self.ctx.texture(sfc.get_size(), components=4, data=img_data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        return tex

    def load_texture(self, path: str) -> moderngl.Texture:
        img = pygame.image.load(path).convert_alpha()
        return self.surface_to_texture(img)
