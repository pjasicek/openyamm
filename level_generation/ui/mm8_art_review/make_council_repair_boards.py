"""Make small visual comparison boards for the eleven council repairs."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE / "council_body_repair"
FONT = ImageFont.truetype("DejaVuSans.ttf", 19)


def checker(size):
    image = Image.new("RGBA", size, "#4a5559")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], 16):
        for x in range(0, size[0], 16):
            if (x // 16 + y // 16) % 2:
                draw.rectangle((x, y, x + 15, y + 15), fill="#647075")
    return image


def place(board, path, x, y, size=None, nearest=False):
    with Image.open(path) as source:
        image = source.convert("RGBA")
    if size:
        image = image.resize(size, Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    board.alpha_composite(image, (x + (220 - image.width) // 2, y + (240 - image.height) // 2))


def main():
    catalog = json.loads((HERE / "catalog.js").read_text().split(" = ", 1)[1].rstrip(";\n"))
    items = {item["id"]: item for item in catalog["items"]}
    for directory in sorted(BASE.iterdir()):
        if not (directory / "layout.json").is_file():
            continue
        layout = json.loads((directory / "layout.json").read_text())
        avatar = items[layout["avatar"]]
        avatar_candidate = next(row for row in avatar["candidates"]
                                if row["sha256"] == layout["avatar_candidate_sha256"])
        rows = layout["cells"]
        board = checker((930, 46 + len(rows) * 282))
        draw = ImageDraw.Draw(board)
        for column, title in enumerate(("Native", "Earlier candidate", "Identity repair", "Matching avatar")):
            draw.text((8 + column * 230, 12), title, font=FONT, fill="white")
        for row_index, cell in enumerate(rows):
            y = 46 + row_index * 282
            item = items[cell["id"]]
            draw.text((8, y + 244), cell["name"], font=FONT, fill="white")
            place(board, HERE / item["original"], 0, y, tuple(cell["x2_size"]), nearest=True)
            place(board, ROOT / cell["parent_artifact"], 230, y)
            place(board, BASE / "candidates" / f"{cell['id']}.png", 460, y)
            place(board, HERE / avatar_candidate["path"], 690, y, (172, 172))
        board.convert("RGB").save(directory / "review.jpg", quality=92)
        print(directory / "review.jpg")


if __name__ == "__main__":
    main()
