
class PointLight:
    def __init__(self, position, power=1., radius=10., enabled=True) -> None:
        self.position = position
        self.power = power
        self.radius = radius
        self.enabled = enabled
        self._color = [.5 for _ in range(3)] + [1.]

    def set_color(self, R: int, G: int, B: int, A: int = 255):
        color = [R, G, B, A]
        color = [x/255. for x in color]
        self._color = color
