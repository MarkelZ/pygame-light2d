
class Hull:
    """
    Represents an area used for defining illuminated regions in the lighting engine.

    Args:
        vertices (list[tuple[float, float]]): List of vertices defining the hull's boundary.
        illuminate_interior (bool, optional): Whether to illuminate the interior of the hull. Default is False.
        enabled (bool, optional): Whether the hull is enabled for rendering. Default is True.
    """

    def __init__(self, vertices, illuminate_interior=False, enabled=True) -> None:
        """
        Initialize a hull.

        Args:
            vertices (list[tuple[float, float]]): List of vertices defining the hull's boundary in native coordinates.
            illuminate_interior (bool, optional): This feature has not been implemented yet.
            enabled (bool, optional): Whether the hull is enabled for rendering. Default is True.
        """

        self.vertices = vertices
        self.illuminate_interior = illuminate_interior
        self.enabled = enabled
