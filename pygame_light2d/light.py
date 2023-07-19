
class PointLight:
    def __init__(self, position, color, power=1., decay=100.) -> None:
        self.position = position
        self.color = color
        self.power = power
        self.decay = decay
