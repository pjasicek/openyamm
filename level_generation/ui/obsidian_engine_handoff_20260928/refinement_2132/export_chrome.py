"""Rasterize this revision's code-native SVG chrome; never processes generated artwork."""

import ctypes
import ctypes.util
from pathlib import Path
import xml.etree.ElementTree as ET


def bind(library, name, arguments, result=None):
    function = getattr(library, name)
    function.argtypes = arguments
    function.restype = result
    return function


root = Path(__file__).resolve().parent
assets = root.parents[3] / "assets_dev/engine/icons_x2"
rsvg = ctypes.CDLL(ctypes.util.find_library("rsvg-2"))
cairo = ctypes.CDLL(ctypes.util.find_library("cairo"))
gobject = ctypes.CDLL(ctypes.util.find_library("gobject-2.0"))
pointer = ctypes.c_void_p
new_handle = bind(rsvg, "rsvg_handle_new_from_file", [ctypes.c_char_p, ctypes.POINTER(pointer)], pointer)
render = bind(rsvg, "rsvg_handle_render_cairo", [pointer, pointer], ctypes.c_int)
new_surface = bind(cairo, "cairo_image_surface_create", [ctypes.c_int, ctypes.c_int, ctypes.c_int], pointer)
new_context = bind(cairo, "cairo_create", [pointer], pointer)
write_png = bind(cairo, "cairo_surface_write_to_png", [pointer, ctypes.c_char_p], ctypes.c_int)
destroy_context = bind(cairo, "cairo_destroy", [pointer])
destroy_surface = bind(cairo, "cairo_surface_destroy", [pointer])
release = bind(gobject, "g_object_unref", [pointer])

for source in sorted((root / "art").glob("*.svg")):
    size = ET.parse(source).getroot().attrib
    error = pointer()
    handle = new_handle(str(source).encode(), ctypes.byref(error))
    if not handle:
        raise RuntimeError(f"Cannot load SVG: {source}")
    surface = new_surface(0, int(size["width"]), int(size["height"]))
    context = new_context(surface)
    target = assets / (source.stem + ".png")
    try:
        if not render(handle, context) or write_png(surface, str(target).encode()) != 0:
            raise RuntimeError(f"Cannot export SVG: {source}")
        target.chmod(0o644)
    finally:
        destroy_context(context)
        destroy_surface(surface)
        release(handle)
    print(target.relative_to(root.parents[3]))
