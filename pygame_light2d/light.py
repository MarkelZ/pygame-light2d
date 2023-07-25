
class PointLight:
    def __init__(self, position, power=1., decay=10., enabled=True) -> None:
        self.position = position
        self.power = power
        self.decay = decay
        self.enabled = True
        self._color = [.5 for _ in range(3)] + [1.]

    def set_color(self, R: int, G: int, B: int, A: int = 255):
        color = [R, G, B, A]
        color = [x/255. for x in color]
        self._color = color
