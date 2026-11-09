"""Explicit opaque weather-field handling; black is native artwork, not a chroma key."""
import numpy as np


def validate_native_field(image):
    pixels = np.asarray(image.convert('RGBA'))
    opaque = pixels[:, :, 3] == 255
    black = np.max(pixels[:, :, :3], axis=2) == 0
    # Native palette-zero specks can leave a few holes within an otherwise opaque black field.
    if opaque.mean() < .99 or (opaque & black).mean() < .5:
        raise ValueError('Full-frame weather requires an opaque black native field with sparse particles')


def preserve_field(image, native):
    validate_native_field(native)
    output = image.convert('RGBA')
    if output.getchannel('A').getextrema() != (255, 255):
        raise ValueError('Weather return lost the opaque native field; review instead of synthesizing its alpha')
    return output, {'method': 'explicit_opaque_native_weather_field'}
