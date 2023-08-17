from pygame_light2d.color import normalize_color_arguments, denormalize_color


class PointLight:
    """
    Represents a point light source within the lighting engine.

    Args:
        position (tuple[float, float]): Position of the light source.
        power (float, optional): Power of the light source. Default is 1.0.
        radius (float, optional): Radius of the light source. Default is 10.0.
        enabled (bool, optional): Whether the light source is enabled. Default is True.
    """

    def __init__(self, position, power=1., radius=10., enabled=True) -> None:
        """
        Initialize a point light source.

        Args:
            position (tuple[float, float]): Position of the light source.
            power (float, optional): Power of the light source. Default is 1.0.
            radius (float, optional): Radius of the light source in native coordinates. Default is 10.0.
            enabled (bool, optional): Whether the light source is enabled. Default is True.
        """

        self.position = position
        self.power = power
        self.radius = radius
        self.enabled = enabled
        self.cast_shadows = True
        self._color = [0., 0., 0., 1.]

    def set_color(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255) -> None:
        """
        Set the color of the point light source.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """

        self._color = normalize_color_arguments(R, G, B, A)

    def get_color(self) -> tuple[int]:
        """
        Get the color of the point light source.

        Returns:
            tuple[int]: Denormalized color values (R, G, B, A) in the range of 0 to 255.
        """

        return denormalize_color(self._color)
