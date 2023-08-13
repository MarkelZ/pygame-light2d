
class Hull:
    def __init__(self, vertices, illuminate_interior=False, enabled=True) -> None:
        self.vertices = vertices
        self.illuminate_interior = illuminate_interior
        self.enabled = enabled
