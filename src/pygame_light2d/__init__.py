# Standard modules
from importlib import resources
import enum


# Import tests for non-standard modules
try:
    import numpy as np
except ImportError:
    raise ImportError('Missing package: numpy.')
except Exception as e:
    raise ImportError(f'Error importing numpy: {e}')

try:
    import pygame
except ImportError:
    raise ImportError('Missing package: pygame.')
except Exception as e:
    raise ImportError(f'Error importing pygame: {e}')

try:
    import moderngl
except ImportError:
    raise ImportError('Missing package: moderngl.')
except Exception as e:
    raise ImportError(f'Error importing moderngl: {e}')

try:
    from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST
except ImportError:
    raise ImportError('Missing package: OpenGL.')
except Exception as e:
    raise ImportError(f'Error importing OpenGL: {e}')


# Local modules
from .engine import LightingEngine, Layer
from .hull import Hull
from .light import PointLight

BACKGROUND = Layer.BACKGROUND
FOREGROUND = Layer.FOREGROUND

NEAREST = moderngl.NEAREST
LINEAR = moderngl.LINEAR

__all__ = ['LightingEngine', 'PointLight', 'Hull', 'Layer'
           'BACKGROUND', 'FOREGROUND', 'NEAREST', 'LINEAR']

# Version of the pygame_light2d package
__version__ = '2.0.0'
