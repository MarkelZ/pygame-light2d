import moderngl
from pygame_render import RenderEngine


class DoubleBuff:
    def __init__(self, graphics: RenderEngine, resolution: tuple[int], components=4, dtype='f2', filter=moderngl.LINEAR) -> None:
        # Create the frame buffers
        self._layer1 = graphics.make_layer(
            size=resolution, components=components, dtype=dtype)
        self._layer1.texture.filter = (filter, filter)

        self._layer2 = graphics.make_layer(
            size=resolution, components=components, dtype=dtype)
        self._layer2.texture.filter = (filter, filter)

        # The active texture, fbo and their index
        self._ind = 1
        self.tex = self._layer2.texture
        self.fbo = self._layer1

    # Flip the double buffer
    def flip(self):
        if self._ind == 1:
            self._ind = 2
            self.tex = self._layer1.texture
            self.fbo = self._layer2
        else:
            self._ind = 1
            self.tex = self._layer2.texture
            self.fbo = self._layer1

    # Clear both buffers
    def clear(self, R=0, G=0, B=0, A=0):
        self._layer1.clear(R, G, B, A)
        self._layer2.clear(R, G, B, A)
