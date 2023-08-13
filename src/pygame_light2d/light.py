from pygame_light2d.color import normalize_color_arguments, denormalize_color


class PointLight:
    def __init__(self, position, power=1., radius=10., enabled=True) -> None:
        self.position = position
        self.power = power
        self.radius = radius
        self.enabled = enabled
        self._color = [0., 0., 0., 1.]

    def set_color(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255) -> None:
        self._color = normalize_color_arguments(R, G, B, A)

    def get_color(self) -> tuple[int]:
        return denormalize_color(self._color)
