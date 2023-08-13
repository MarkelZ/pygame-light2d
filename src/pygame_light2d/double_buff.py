import moderngl


class DoubleBuff:
    def __init__(self, ctx: moderngl.Context, resolution: tuple[int], components=4, dtype='f2', filter=moderngl.LINEAR) -> None:
        # Create the textures
        self._tex1 = ctx.texture(
            resolution, components=components, dtype=dtype)
        self._tex1.filter = (filter, filter)

        self._tex2 = ctx.texture(
            resolution, components=components, dtype=dtype)
        self._tex2.filter = (filter, filter)

        # Create the frame buffers
        self._fbo1 = ctx.framebuffer([self._tex1])
        self._fbo2 = ctx.framebuffer([self._tex2])

        # The active texture, fbo and their index
        self._ind = 1
        self.tex = self._tex2
        self.fbo = self._fbo1

    # Flip the double buffer
    def flip(self):
        if self._ind == 1:
            self._ind = 2
            self.tex = self._tex1
            self.fbo = self._fbo2
        else:
            self._ind = 1
            self.tex = self._tex2
            self.fbo = self._fbo1

    # Clear both buffers
    def clear(self, R=0, G=0, B=0, A=0):
        self._fbo1.clear(R, G, B, A)
        self._fbo2.clear(R, G, B, A)
