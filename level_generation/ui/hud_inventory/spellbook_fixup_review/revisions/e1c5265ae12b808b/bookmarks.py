"""Composite retained school emblems onto one parchment bookmark.

The measured source ellipses locate the individually drawn old badge rims. Only
their interiors are transferred; every output uses the same master rim, paper,
edge and alpha. The inactive drawing is extracted as ink, removing its old paper.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont


RECIPE = {
    "master_source": "installed/stdrd.png",
    "master_center": [48.17, 39.26],
    "master_inner_radii": [33.9, 32.9],
    "paper_source": "layers/common_book.png",
    "paper_crop": [880, 380, 976, 458],
    "master_paper_rgb": [239, 207, 146],
    "book_paper_rgb": [235, 204, 146],
    "ink_rgb": [58, 33, 13],
    "paper_rejection": 12,
    "inactive_rim_inset": 3.4,
    "active_rim_inset": 5.0,
    # Each entry is [center x, center y, horizontal radius, vertical radius].
    # These are measured source coordinates, never per-state destination bounds.
    "source_badge_ellipses": {
        "Fire": [[48.66, 39.88, 35.40, 35.32], [47.44, 38.91, 36.66, 35.69]],
        "Air": [[47.52, 40.33, 36.49, 35.65], [48.54, 39.89, 37.00, 36.69]],
        "Water": [[48.65, 40.34, 35.66, 35.01], [47.95, 39.36, 37.00, 36.82]],
        "Earth": [[48.80, 39.39, 36.25, 36.15], [47.12, 39.73, 36.93, 36.73]],
        "Spirit": [[47.54, 39.76, 35.61, 35.72], [47.94, 39.15, 37.00, 36.66]],
        "Mind": [[47.76, 41.00, 35.21, 34.64], [47.88, 41.00, 36.49, 36.31]],
        "Body": [[48.69, 40.73, 35.68, 35.74], [47.88, 40.46, 36.43, 35.76]],
        "Light": [[48.14, 39.48, 35.19, 35.59], [48.04, 39.73, 37.00, 36.22]],
        "Dark": [[47.16, 40.33, 36.04, 35.70], [48.44, 39.96, 36.61, 36.35]],
        "DarkElf": [[48.75, 38.98, 36.36, 36.03], [48.29, 39.22, 36.90, 36.46]],
        "Vampire": [[48.27, 41.00, 35.47, 35.35], [47.53, 41.00, 35.97, 36.11]],
        "Dragon": [[48.17, 39.26, 36.06, 34.93], [46.30, 37.71, 35.74, 35.40]],
    },
}
LUMA = np.array([.2126, .7152, .0722])


def ellipse_mask(size):
    yy, xx = np.mgrid[:size[1], :size[0]]
    cx, cy = RECIPE["master_center"]
    rx, ry = RECIPE["master_inner_radii"]
    distance = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return Image.fromarray(np.uint8(np.clip((1 - distance) * min(rx, ry) + .5, 0, 1) * 255))


def extract_ink(source, ellipse):
    pixels = np.asarray(source).astype(np.float64)
    luminance = pixels[:, :, :3] @ LUMA
    yy, xx = np.mgrid[:source.height, :source.width]
    cx, cy, rx, ry = ellipse
    interior = ((xx - cx) / (rx - 4)) ** 2 + ((yy - cy) / (ry - 4)) ** 2 < 1
    paper_luminance = np.percentile(luminance[interior & (luminance > 150)], 75)
    ink = np.array(RECIPE["ink_rgb"])
    reject = RECIPE["paper_rejection"]
    opacity = np.clip((paper_luminance - luminance - reject) / (paper_luminance - ink @ LUMA - reject), 0, 1)
    pixels[:, :, :3] = ink
    pixels[:, :, 3] = np.rint(opacity * pixels[:, :, 3])
    return Image.fromarray(np.uint8(pixels))


def fit_emblem(source, ellipse, mask, inactive):
    cx, cy = RECIPE["master_center"]
    rx, ry = RECIPE["master_inner_radii"]
    sx, sy, source_rx, source_ry = ellipse
    inset = RECIPE["inactive_rim_inset" if inactive else "active_rim_inset"]
    ax, ay = (source_rx - inset) / rx, (source_ry - inset) / ry
    fitted = source.transform(mask.size, Image.Transform.AFFINE,
                              (ax, 0, sx - ax * cx, 0, ay, sy - ay * cy), Image.Resampling.BICUBIC)
    pixels = np.asarray(fitted).copy()
    pixels[:, :, 3] = np.uint8(np.rint(pixels[:, :, 3].astype(np.float64) * np.asarray(mask) / 255))
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels)


def make_bookmarks(schools, directory, save):
    original = Image.open(directory / RECIPE["master_source"]).convert("RGBA")
    mask = ellipse_mask(original.size)
    pixels = np.asarray(original).astype(np.float64)
    pixels[:, :, :3] *= np.array(RECIPE["book_paper_rgb"]) / np.array(RECIPE["master_paper_rgb"])
    master = Image.fromarray(np.uint8(np.clip(pixels, 0, 255)))
    paper = Image.open(directory / RECIPE["paper_source"]).convert("RGBA").crop(RECIPE["paper_crop"])
    master.paste(paper, (0, 0), mask)
    # The retained tab contains fractional matte-removal alpha inside its badge.
    # This is opaque parchment, so close those interior pinholes once in the
    # master; coloured overlays must never change the bookmark's transparency.
    pixels = np.asarray(master).copy()
    pixels[:, :, 3][np.asarray(mask) > 0] = 255
    master = Image.fromarray(pixels)
    common = {"master": save(master, "bookmarks/master.png"),
              "emblemMask": save(mask, "bookmarks/emblem_mask.png")}
    alpha = np.asarray(master)[:, :, 3]
    outside = np.asarray(mask) == 0
    for school in schools:
        button = school["button"]
        button["proposedStates"], button["emblems"] = {}, {}
        for index, state in enumerate(["default", "pressed"]):
            source = Image.open(directory / button["states"][state]["path"]).convert("RGBA")
            assert source.size == master.size == (96, 78)
            ellipse = RECIPE["source_badge_ellipses"][school["key"]][index]
            inactive = state == "default"
            if inactive:
                source = extract_ink(source, ellipse)
            emblem = fit_emblem(source, ellipse, mask, inactive)
            candidate = Image.alpha_composite(master, emblem)
            assert np.array_equal(np.asarray(candidate)[:, :, 3], alpha), school["key"]
            assert np.array_equal(np.asarray(candidate)[outside], np.asarray(master)[outside]), school["key"]
            name = school["key"].lower() + ("-normal" if inactive else "-selected")
            button["emblems"][state] = save(emblem, "bookmarks/emblems/" + name + ".png")
            button["proposedStates"][state] = save(candidate, "bookmarks/" + name + ".png")
        # The game changes school on click; merely hovering retains the ink state.
        button["proposedStates"]["highlighted"] = button["proposedStates"]["default"]
    return common


def comparison_sheet(schools, directory):
    font = ImageFont.truetype(str(directory / "fonts/lucida.ttf"), 18)
    small = ImageFont.truetype(str(directory / "fonts/lucida.ttf"), 14)
    sheet = Image.new("RGB", (1500, 870), (34, 32, 29))
    draw = ImageDraw.Draw(sheet)
    draw.text((22, 14), "One parchment bookmark, twelve school emblems", font=font, fill="#f1dfbd")
    draw.text((22, 43), "Left: installed / Right: shared master    ·    inactive and selected", font=small, fill="#c8baa0")
    for index, school in enumerate(schools):
        x, y = (index % 4) * 374 + 16, (index // 4) * 260 + 82
        draw.text((x, y), school["name"], font=font, fill="#f1dfbd")
        for column, group in enumerate(["states", "proposedStates"]):
            for row, state in enumerate(["default", "pressed"]):
                im = Image.open(directory / school["button"][group][state]["path"]).convert("RGBA")
                im = im.resize((120, 98), Image.Resampling.LANCZOS)
                sheet.paste(im, (x + 5 + column * 165, y + 35 + row * 103), im)
    destination = directory / "evidence/bookmark_comparison.png"
    destination.parent.mkdir(exist_ok=True)
    sheet.save(destination)
