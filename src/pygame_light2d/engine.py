from importlib import resources
from enum import Enum
import numpy as np
import moderngl
import pygame
from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST, glGetUniformBlockIndex, glUniformBlockBinding

from pygame_light2d.light import PointLight
from pygame_light2d.hull import Hull
from pygame_light2d.color import normalize_color_arguments, denormalize_color
from pygame_light2d.double_buff import DoubleBuff


class Layer(Enum):
    BACKGROUND = 1,
    FOREGROUND = 2,


class LightingEngine:
    """A class for managing lighting effects within a Pygame environment."""

    def __init__(self, screen_res: tuple[int, int], native_res: tuple[int, int], lightmap_res: tuple[int, int]) -> None:
        """
        Initialize the lighting engine.

        Args:
            native_res (tuple[int, int]): Native resolution of the game (width, height).
            lightmap_res (tuple[int, int]): Lightmap resolution (width, height).
        """

        # Initialize private members
        self._screen_res = screen_res
        self._native_res = native_res
        self._lightmap_res = lightmap_res
        self._ambient = (.25, .25, .25, .25)

        # Initialize public members
        self.lights: list[PointLight] = []
        self.hulls: list[Hull] = []
        self.shadow_blur_radius: int = 5

        # Configure pygame
        self._check_and_configure_pygame()

        # Create an OpenGL context
        self.ctx = moderngl.create_context()

        # Load shaders
        self._load_shaders()

        # Create VAO and VBO
        self._create_screen_vertex_buffers()

        # Create render textures and corresponding FBOs
        self._create_frame_buffers()

        # Create SSBO for hull vertices
        self._create_ssbos()

    def _check_and_configure_pygame(self):
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized. Please ensure you call pygame.init() before using the lighting engine.'

        # Set OpenGL version to 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        pygame.display.set_mode(
            self._screen_res, pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

    def _load_shaders(self):
        # Read source files
        vertex_src = resources.read_text(
            'pygame_light2d', 'vertex.glsl')
        fragment_src_light = resources.read_text(
            'pygame_light2d', 'fragment_light.glsl')
        fragment_src_blur = resources.read_text(
            'pygame_light2d', 'fragment_blur.glsl')
        fragment_src_mask = resources.read_text(
            'pygame_light2d', 'fragment_mask.glsl')
        fragment_src_draw = resources.read_text(
            'pygame_light2d', 'fragment_draw.glsl')

        # Create shader programs
        self._prog_light = self.ctx.program(vertex_shader=vertex_src,
                                            fragment_shader=fragment_src_light)
        self._prog_blur = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_blur)
        self._prog_mask = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_mask)
        self._prog_draw = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_draw)

    def _create_screen_vertex_buffers(self):
        # Screen mesh
        screen_vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                                    (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        screen_tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                                      (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
        screen_vertex_data = np.hstack([screen_vertices, screen_tex_coords])

        # VAO and VBO for screen mesh
        screen_vbo = self.ctx.buffer(screen_vertex_data)
        self._vao_light = self.ctx.vertex_array(self._prog_light, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self._vao_blur = self.ctx.vertex_array(self._prog_blur, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self._vao_mask = self.ctx.vertex_array(self._prog_mask, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self._vao_draw = self.ctx.vertex_array(self._prog_draw, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

    def _create_frame_buffers(self):
        # Frame buffers
        self._tex_bg = self.ctx.texture(self._native_res, components=4)
        self._tex_bg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_bg = self.ctx.framebuffer([self._tex_bg])

        self._tex_fg = self.ctx.texture(self._native_res, components=4)
        self._tex_fg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_fg = self.ctx.framebuffer([self._tex_fg])

        # Double buffer for lights
        self._buf_lt = DoubleBuff(self.ctx, self._lightmap_res)

        # Ambient occlussion map
        self._tex_ao = self.ctx.texture(
            self._lightmap_res, components=4, dtype='f2')
        self._tex_ao.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._fbo_ao = self.ctx.framebuffer([self._tex_ao])

    def _create_ssbos(self):
        # Set block indices for the SSBOS in the shader program
        prog_glo = self._prog_light.glo

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullVSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 1)

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullIndSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 2)

        # Create SSBOs
        self._ssbo_v = self.ctx.buffer(reserve=4*2048)
        self._ssbo_v.bind_to_uniform_block(1)
        self._ssbo_ind = self.ctx.buffer(reserve=4*256)
        self._ssbo_ind.bind_to_uniform_block(2)

    def set_filter(self, layer: Layer, filter) -> None:
        """
        Set the filter for a specific layer's texture.

        Args:
            layer (Layer): The layer to apply the filter to.
            filter (tuple[Constant, Constant]): The filter to apply to the texture, can be `NEAREST` or `LINEAR`.
        """
        self._get_tex(layer).filter = filter

    def set_aomap_filter(self, filter) -> None:
        """
        Set the aomap's filter.

        Args:
            filter (tuple[Constant, Constant]): The filter to apply to the texture, can be `NEAREST` or `LINEAR`.
        """
        self._tex_ao.filter = filter

    def set_ambient(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255) -> None:
        """
        Set the ambient light color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        self._ambient = normalize_color_arguments(R, G, B, A)

    def get_ambient(self) -> tuple[int, int, int, int]:
        """
        Get the ambient light color.

        Returns:
            tuple[int, int, int, int]: Ambient light color in 0-255 scale (R, G, B, A).
        """
        return denormalize_color(self._ambient)

    def blit_texture(self, tex: moderngl.Texture, layer: Layer, dest: pygame.Rect, source: pygame.Rect):
        """
        Blit a texture onto a specified layer's framebuffer.

        Args:
            tex (moderngl.Texture): Texture to blit.
            layer (Layer): Layer to blit the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
        """

        # Create a framebuffer with the texture
        fb = self.ctx.framebuffer([tex])

        # Select destination framebuffer correcponding to layer
        fbo = self._get_fbo(layer)

        # Blit texture onto destination
        glBlitNamedFramebuffer(fb.glo, fbo.glo, source.x, source.y, source.w, source.h,
                               dest.x, dest.y, dest.w, dest.h, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def render_texture(self, tex: moderngl.Texture, layer: Layer, dest: pygame.Rect, source: pygame.Rect):
        """
        Render a texture onto a specified layer's framebuffer using the draw shader.

        Args:
            tex (moderngl.Texture): Texture to render.
            layer (Layer): Layer to render the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
        """

        # Render texture onto layer with the draw shader
        fbo = self._get_fbo(layer)
        self._render_tex_to_fbo(tex, fbo, dest, source)

    def surface_to_texture(self, sfc: pygame.Surface) -> moderngl.Texture:
        """
        Convert a pygame.Surface to a moderngl.Texture.

        Args:
            sfc (pygame.Surface): Surface to convert.

        Returns:
            moderngl.Texture: Converted texture.
        """

        img_flip = pygame.transform.flip(sfc, False, True)
        img_data = pygame.image.tostring(img_flip, "RGBA")

        tex = self.ctx.texture(sfc.get_size(), components=4, data=img_data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        return tex

    def load_texture(self, path: str) -> moderngl.Texture:
        """
        Load a texture from a file.

        Args:
            path (str): Path to the texture file.

        Returns:
            moderngl.Texture: Loaded texture.
        """

        img = pygame.image.load(path).convert_alpha()
        return self.surface_to_texture(img)

    def clear(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255):
        """
        Clear the background with a color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        R, G, B, A = normalize_color_arguments(R, G, B, A)
        self._fbo_bg.clear(R, G, B, A)
        self._fbo_fg.clear(0, 0, 0, 0)

    def render(self):
        """
        Render the lighting effects onto the screen.

        Clears intermediate buffers, renders lights onto the double buffer,
        blurs the lightmap for soft shadows, and renders background and foreground.

        This method is responsible for the final rendering of lighting effects onto the screen.
        """

        # Clear intermediate buffers
        self.ctx.screen.clear(0, 0, 0, 1)
        self._fbo_ao.clear(0, 0, 0, 0)
        self._buf_lt.clear(0, 0, 0, 0)

        # Send hull data to SSBOs
        self._send_hull_data()

        # Render lights onto double buffer
        self._render_to_buf_lt()

        # Blur lightmap for soft shadows and render onto aomap
        self._render_aomap()

        # Render background masked with the lightmap
        self._render_background()

        # Render foreground onto screen
        self._render_foreground()

    def _point_to_uv(self, p: tuple[float, float]):
        return [p[0]/self._native_res[0], 1 - (p[1]/self._native_res[1])]

    def _get_fbo(self, layer: Layer):
        if layer == Layer.BACKGROUND:
            return self._fbo_bg
        elif layer == Layer.FOREGROUND:
            return self._fbo_fg
        return None

    def _get_tex(self, layer: Layer):
        if layer == Layer.BACKGROUND:
            return self._tex_bg
        elif layer == Layer.FOREGROUND:
            return self._tex_fg
        return None

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
        vao = self.ctx.vertex_array(self._prog_draw, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use buffers and render
        tex.use()
        fbo.use()
        vao.render()

    def _send_hull_data(self):
        # Lists with hull vertices and indices
        vertices = []
        indices = []
        for hull in self.hulls:
            if not hull.enabled:
                continue
            vertices += hull.vertices
            indices.append(len(vertices))

        # Store hull vertex data in SSBO
        vertices = [self._point_to_uv(v) for v in vertices]
        data_v = np.array(vertices, dtype=np.float32).flatten().tobytes()
        self._ssbo_v.write(data_v)

        # Store hull vertex indices in SSBO
        data_ind = np.array(indices, dtype=np.int32).flatten().tobytes()
        self._ssbo_ind.write(data_ind)

    def _render_to_buf_lt(self):
        # Disable alpha blending to render lights
        self.ctx.disable(moderngl.BLEND)

        for light in self.lights:
            # Skip light if disabled
            if not light.enabled:
                continue

            # Use light double buffer
            self._buf_lt.tex.use()
            self._buf_lt.fbo.use()

            # Send light uniforms
            self._prog_light['lightPos'] = self._point_to_uv(light.position)
            self._prog_light['lightCol'] = light._color
            self._prog_light['lightPower'] = light.power
            self._prog_light['radius'] = light.radius
            self._prog_light['castShadows'] = light.cast_shadows
            self._prog_light['native_width'] = self._native_res[0]
            self._prog_light['native_height'] = self._native_res[1]

            # Send number of hulls
            self._prog_light['numHulls'] = len(self.hulls)

            # Render onto lightmap
            self._vao_light.render()

            # Flip double buffer
            self._buf_lt.flip()

        # Re-enable alpha blending
        self.ctx.enable(moderngl.BLEND)

    def _render_aomap(self):
        # Use aomap FBO and light buffer texture
        self._fbo_ao.use()
        self._buf_lt.tex.use()

        self._prog_blur['blurRadius'] = self.shadow_blur_radius
        self._vao_blur.render()

    def _render_background(self):
        self.ctx.screen.use()
        self._tex_bg.use()

        self._tex_ao.use(1)
        self._prog_mask['lightmap'].value = 1
        self._prog_mask['ambient'].value = self._ambient

        self._vao_mask.render()

    def _render_foreground(self):
        self.ctx.screen.use()
        self._tex_fg.use()
        self._vao_draw.render()
