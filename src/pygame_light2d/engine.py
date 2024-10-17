import random
from enum import Enum
from importlib import resources
import moderngl
import numpy as np
# from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST, glGetUniformBlockIndex, glUniformBlockBinding
import pygame
import warnings

from pygame_render import RenderEngine
from pygame_render.util import normalize_color_arguments, denormalize_color

from pygame_light2d.light import PointLight
from pygame_light2d.hull import Hull
from pygame_light2d.double_buff import DoubleBuff


class DrawLayer(Enum):
    BACKGROUND = 1,
    FOREGROUND = 2,


class LightingEngine:
    """A class for managing lighting effects within a Pygame environment."""

    def __init__(self, screen_res: tuple[int, int],
                 native_res: tuple[int, int],
                 lightmap_res: tuple[int, int],
                 fullscreen: int | bool = 0, resizable: int | bool = 0,
                 noframe: int | bool = 0, scaled: int | bool = 0,
                 depth: int = 0, display: int = 0, vsync: int = 0) -> None:
        """
        Initialize the lighting engine.

        Args:
            screen_res (tuple[int, int]): resolution of the screen (width, height).
            native_res (tuple[int, int]): Native resolution of the game (width, height).
            lightmap_res (tuple[int, int]): Lightmap resolution (width, height).
            fullscreen (int or bool, optional): Set to 1 or True to enable fullscreen mode, 0 or False to disable. Default is 0.
            resizable (int or bool, optional): Set to 1 or True to enable window resizing, 0 or False to disable. Default is 0.
            noframe (int or bool, optional): Set to 1 or True to remove window frame, 0 or False to keep the frame. Default is 0.
            scaled (int or bool, optional): Set to 1 or True to enable display scaling, 0 or False to disable. Default is 0.
            depth (int, optional): Depth of the rendering window. Default is 0.
            display (int, optional): The display index to use. Default is 0.
            vsync (int, optional): Set to 1 to enable vertical synchronization, 0 to disable. Default is 0.
        """

        # Initialize private members
        self._screen_res = screen_res
        self._native_res = native_res
        self._lightmap_res = lightmap_res
        self._ambient = (.25, .25, .25, .25)

        # Initialize public members
        self.lights: list[PointLight] = []
        self.hulls: list[Hull] = []
        self.shadow_blur_radius: int = 3
        self.max_luminosity: float = 2.5

        # Initialize shader engine
        self._graphics = RenderEngine(screen_res[0], screen_res[1],
                                      fullscreen=fullscreen, resizable=resizable,
                                      noframe=noframe, scaled=scaled, depth=depth,
                                      display=display, vsync=vsync)

        # Load shaders
        self._load_shaders()

        # Create render textures and corresponding FBOs
        self._create_frame_buffers()

        # Create SSBO for hull vertices
        self._create_ssbos()

    def _load_shaders(self):
        # Read source files
        package_name = 'pygame_light2d'
        vertex_src = resources.read_text(
            package_name, 'vertex.glsl')
        fragment_src_light = resources.read_text(
            package_name, 'fragment_light.glsl')
        fragment_src_blur = resources.read_text(
            package_name, 'fragment_blur.glsl')
        fragment_src_mask = resources.read_text(
            package_name, 'fragment_mask.glsl')

        # Create shader programs
        self._prog_light = self._graphics.make_shader(vertex_src=vertex_src,
                                                      fragment_src=fragment_src_light)
        self._prog_blur = self._graphics.make_shader(vertex_src=vertex_src,
                                                     fragment_src=fragment_src_blur)
        self._prog_mask = self._graphics.make_shader(vertex_src=vertex_src,
                                                     fragment_src=fragment_src_mask)

    def _create_frame_buffers(self):
        # Frame buffers
        self._layer_bg = self._graphics.make_layer(
            self._native_res, components=4)
        self._layer_fg = self._graphics.make_layer(
            self._native_res, components=4)

        # Double buffer for lights
        self._buf_lt = DoubleBuff(self._graphics, self._lightmap_res)

        # Ambient occlussion map
        self._layer_ao = self._graphics.make_layer(
            self._lightmap_res, components=4, dtype='f2')
        self._layer_ao.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # Disable texture wrapping
        self._buf_lt._layer1.texture.repeat_x = False
        self._buf_lt._layer1.texture.repeat_y = False
        self._buf_lt._layer2.texture.repeat_x = False
        self._buf_lt._layer2.texture.repeat_y = False
        self._layer_ao.texture.repeat_x = False
        self._layer_ao.texture.repeat_y = False
        self._layer_bg.texture.repeat_x = False
        self._layer_bg.texture.repeat_y = False
        self._layer_fg.texture.repeat_x = False
        self._layer_fg.texture.repeat_y = False

    def _create_ssbos(self, max_num_hulls=1024):
        # Create SSBOs
        self._graphics.reserve_uniform_block(
            shader=self._prog_light,
            ubo_name='hullVSSBO',
            nbytes=6*8*max_num_hulls)

        self._graphics.reserve_uniform_block(
            shader=self._prog_light,
            ubo_name='hullIndSSBO',
            nbytes=8*max_num_hulls)

    @property
    def graphics(self) -> RenderEngine:
        """Get the graphics engine."""
        return self._graphics

    @property
    def ctx(self) -> moderngl.Context:
        """Get the ModernGL rendering context."""
        return self._graphics.ctx

    def set_filter(self, layer: DrawLayer, filter: tuple) -> None:
        """
        Set the filter for a specific layer's texture.

        Args:
            layer (Layer): The layer to apply the filter to.
            filter (tuple[Constant, Constant]): The filter to apply to the texture, can be `NEAREST` or `LINEAR`.
        """
        self._get_layer(layer).texture.filter = filter

    def set_aomap_filter(self, filter: tuple) -> None:
        """
        Set the aomap's filter.

        Args:
            filter (tuple[Constant, Constant]): The filter to apply to the texture, can be `NEAREST` or `LINEAR`.
        """
        self._layer_ao.texture.filter = filter

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

    def blit_texture(self, tex: moderngl.Texture, layer: DrawLayer, dest: pygame.Rect, source: pygame.Rect):
        """
        Blit a texture onto a specified layer's framebuffer.

        Args:
            tex (moderngl.Texture): Texture to blit.
            layer (Layer): Layer to blit the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
        """

        # # Create a framebuffer with the texture
        # fb = self.ctx.framebuffer([tex])

        # # Select destination framebuffer correcponding to layer
        # fbo = self._get_fbo(layer)

        # # Blit texture onto destination
        # glBlitNamedFramebuffer(fb.glo, fbo.glo, source.x, source.y, source.w, source.h,
        #                        dest.x, dest.y, dest.w, dest.h, GL_COLOR_BUFFER_BIT, GL_NEAREST)

        warnings.warn(
            'blit_texture is deprecated, please use render_texture', UserWarning)
        self.render_texture(tex, layer, dest, source)

    def render_texture(self, tex: moderngl.Texture, layer: DrawLayer, dest: pygame.Rect, source: pygame.Rect):
        """
        Render a texture onto a specified layer's framebuffer using the draw shader.

        Args:
            tex (moderngl.Texture): Texture to render.
            layer (Layer): Layer to render the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
        """

        # Render texture onto layer with the draw shader
        layer = self._get_layer(layer)
        dest_vertices = [(dest.x + dest.width, dest.y + dest.height),
                         (dest.x, dest.y + dest.height),
                         (dest.x, dest.y),
                         (dest.x + dest.width, dest.y)]
        section_vertices = [(source.x, source.y),
                            (source.x + source.width, source.y),
                            (source.x, source.y + source.height),
                            (source.x + source.width, source.y + source.height)]
        self._graphics.render_from_vertices(
            tex, layer, dest_vertices, section_vertices)

    def render_transformed(self, tex: moderngl.Texture, layer: DrawLayer,
                           position: tuple[float, float] = (0, 0),
                           scale: tuple[float, float] | float = (1.0, 1.0),
                           angle: float = 0.0,
                           flip: tuple[bool, bool] | bool = (False, False),
                           section: pygame.Rect | None = None):
        """
        Render a transformed texture onto a specified layer's framebuffer using the draw shader.

        Args:
            tex (moderngl.Texture): Texture to render.
            layer (Layer): Layer to render the texture onto.
            position (tuple[float, float]): The position (x, y) where the texture will be rendered. Default is (0, 0).
            scale (tuple[float, float] | float): The scaling factor for the texture. Can be a tuple (x, y) or a scalar. Default is (1.0, 1.0).
            angle (float): The rotation angle in degrees. Default is 0.0.
            flip (tuple[bool, bool] | bool): Whether to flip the texture. Can be a tuple (flip x axis, flip y axis) or a boolean (flip x axis). Default is (False, False).
            section (pygame.Rect | None): The section of the texture to render. If None, the entire texture is rendered. Default is None.
        """
        layer = self._get_layer(layer)
        self._graphics.render(tex, layer, position,
                              scale, angle, flip, section)

    def surface_to_texture(self, sfc: pygame.Surface) -> moderngl.Texture:
        """
        Convert a pygame.Surface to a moderngl.Texture.

        Args:
            sfc (pygame.Surface): Surface to convert.

        Returns:
            moderngl.Texture: Converted texture.
        """

        return self._graphics.surface_to_texture(sfc)

    def load_texture(self, path: str) -> moderngl.Texture:
        """
        Load a texture from a file.

        Args:
            path (str): Path to the texture file.

        Returns:
            moderngl.Texture: Loaded texture.
        """

        return self._graphics.load_texture(path)

    def clear(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255):
        """
        Clear the background with a color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        self._layer_bg.clear(R, G, B, A)
        self._layer_fg.clear(0, 0, 0, 0)

    def render(self):
        """
        Render the lighting effects onto the screen.

        Clears intermediate buffers, renders lights onto the double buffer,
        blurs the lightmap for soft shadows, and renders background and foreground.

        This method is responsible for the final rendering of lighting effects onto the screen.
        """

        # Clear intermediate buffers
        self._graphics.screen.clear(0, 0, 0, 1)
        self._layer_ao.clear(0, 0, 0, 0)
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

    def _get_layer(self, layer: DrawLayer):
        if layer == DrawLayer.BACKGROUND:
            return self._layer_bg
        elif layer == DrawLayer.FOREGROUND:
            return self._layer_fg

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
        self._prog_light['hullVSSBO'] = data_v

        # Store hull vertex indices in SSBO
        data_ind = np.array(indices, dtype=np.int32).flatten().tobytes()
        self._prog_light['hullIndSSBO'] = data_ind

    def _render_to_buf_lt(self):
        # Disable alpha blending to render lights
        self._graphics.use_alpha_blending(False)

        for light in self.lights:
            # Skip light if disabled
            if not light.enabled:
                continue

            # Send light uniforms
            self._prog_light['lightPos'] = self._point_to_uv(
                light.position)
            self._prog_light['lightCol'] = light._color
            self._prog_light['lightPower'] = light.power
            self._prog_light['radius'] = light.radius
            self._prog_light['castShadows'] = light.cast_shadows
            self._prog_light['native_width'] = self._native_res[0]
            self._prog_light['native_height'] = self._native_res[1]

            # Send number of hulls
            self._prog_light['numHulls'] = len(self.hulls)

            # Render onto lightmap
            self._graphics.render(
                self._buf_lt.tex, self._buf_lt.fbo, shader=self._prog_light)

            # Flip double buffer
            self._buf_lt.flip()

        # Re-enable alpha blending
        self._graphics.use_alpha_blending(True)

    def _render_aomap(self):
        # Render light buffer texture to aomap with blur
        if self.shadow_blur_radius <= 0:
            self._graphics.render(
                self._buf_lt.tex, self._layer_ao)
        else:
            self._prog_blur['blurRadius'] = self.shadow_blur_radius
            self._graphics.render(
                self._buf_lt.tex, self._layer_ao, shader=self._prog_blur)

    def _render_background(self):
        self._prog_mask['lightmap'] = self._layer_ao.texture
        self._prog_mask['maxLuminosity'].value = self.max_luminosity
        self._prog_mask['lightmap'].value = 1
        self._prog_mask['ambient'].value = self._ambient

        self._graphics.render(self._layer_bg.texture,
                              self._graphics.screen,
                              scale=(
                                  self._screen_res[0]/self._native_res[0], self._screen_res[1]/self._native_res[1]),
                              shader=self._prog_mask)

    def _render_foreground(self):
        self._graphics.render(self._layer_fg.texture, self._graphics.screen,
                              scale=(
                                  self._screen_res[0]/self._native_res[0], self._screen_res[1]/self._native_res[1]))
