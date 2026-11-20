#!/usr/bin/env python3
"""Export the approved-menu compass for Windows, Linux and Android.

Run from any directory with system Python, PyGObject/librsvg and pycairo.
The editable source is packaging/artwork/openyamm-icon.svg; no screenshot crops
or generated bitmap artwork are used. Small exports strengthen the same geometry.
"""

import io
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import cairo
import gi

gi.require_version("Rsvg", "2.0")
from gi.repository import Rsvg

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packaging/artwork/openyamm-icon.svg"
APP_ID = "io.github.openyamm.OpenYAMM"
SVG = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", SVG[1:-1])


def icon_svg(size, foreground=False, round_icon=False):
    root = ET.fromstring(SOURCE.read_bytes())
    emblem = root.find(f"{SVG}g[@id='emblem']")
    if foreground:
        root.remove(root.find(f"{SVG}g[@id='background']"))
        # Adaptive icons have a 108dp canvas and a central 66dp safe circle.
        root.set("viewBox", "0 0 108 108")
        emblem.set("transform", "translate(22 22) scale(0.64)")
    elif round_icon:
        background = root.find(f"{SVG}g[@id='background']")
        for rect in background:
            rect.set("rx", "64")
    if size <= 48:
        emblem.remove(emblem.find(f"{SVG}circle[@id='inner-ring']"))
        emblem.set("stroke-width", str(max(2.2, 64 / size)))
    return ET.tostring(root)


def render(svg, size):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    context = cairo.Context(surface)
    viewport = Rsvg.Rectangle()
    viewport.x = viewport.y = 0
    viewport.width = viewport.height = size
    Rsvg.Handle.new_from_data(svg).render_document(context, viewport)
    output = io.BytesIO()
    surface.write_to_png(output)
    return output.getvalue()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o644)


def main():
    sizes = (16, 24, 32, 48, 64, 128, 256, 512)
    frames = {size: render(icon_svg(size), size) for size in sizes}
    for size in sizes:
        write(ROOT / f"packaging/icons/hicolor/{size}x{size}/apps/{APP_ID}.png", frames[size])
    write(ROOT / "assets_dev/engine/branding/app_icon.png", frames[256])

    # PNG-backed ICO entries retain each small-size rendering, rather than
    # deriving all entries by downsampling the largest frame.
    ico_sizes = sizes[:-1]
    directory = bytearray(struct.pack("<HHH", 0, 1, len(ico_sizes)))
    offset = 6 + 16 * len(ico_sizes)
    for size in ico_sizes:
        pixels = frames[size]
        directory.extend(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(pixels), offset))
        offset += len(pixels)
    write(ROOT / "packaging/windows/openyamm.ico", directory + b"".join(frames[s] for s in ico_sizes))

    resources = ROOT / "android/app/src/main/res"
    for density, size, adaptive_size in (
        ("mdpi", 48, 108), ("hdpi", 72, 162), ("xhdpi", 96, 216),
        ("xxhdpi", 144, 324), ("xxxhdpi", 192, 432),
    ):
        destination = resources / f"mipmap-{density}"
        write(destination / "ic_launcher.png", render(icon_svg(size), size))
        write(destination / "ic_launcher_round.png", render(icon_svg(size, round_icon=True), size))
        write(destination / "ic_launcher_foreground.png",
              render(icon_svg(adaptive_size, foreground=True), adaptive_size))

    # A committed full-size master also makes the installed artwork easy to inspect.
    write(ROOT / "android/artwork/openyamm_compass_icon_master.png", render(icon_svg(1024), 1024))
    print("Exported compass icons for Windows, Linux, Android and the SDL window.")


if __name__ == "__main__":
    main()
