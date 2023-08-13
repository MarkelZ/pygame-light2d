
# Convert from 0-255 to 0-1, and also process the different ways
# in which arguments may be given (an int tuple vs four separate ints)
def normalize_color_arguments(R: (int | tuple[int]), G: int, B: int, A: int):
    if isinstance(R, tuple):
        if len(R) == 3:
            R, G, B = R
        elif len(R) == 4:
            R, G, B, A = R
        else:
            raise ValueError(
                'Error: The tuple must contain either RGB or RGBA values.')

    return (R/255., G/255., B/255., A/255.)


# Convert from 0-1 to 0-255
def denormalize_color(col):
    return (int(x * 255) for x in col)
