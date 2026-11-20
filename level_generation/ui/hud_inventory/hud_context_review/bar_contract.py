#!/usr/bin/env python3
"""Illustrate the native health/mana frame contract without altering restoration assets."""

from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
OUT = HERE / "diagnostic_alpha" / "manafrm-contract.png"


def image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")


def fill_part(source: Image.Image, amount: float) -> Image.Image:
    result = Image.new("RGBA", source.size)
    from_y = round(source.height * (1 - amount))
    if from_y < source.height:
        result.alpha_composite(source.crop((0, from_y, source.width, source.height)), (0, from_y))
    return result


def composite(frame: Image.Image, health: Image.Image, mana: Image.Image, amount: float) -> Image.Image:
    result = Image.new("RGBA", frame.size, "#233033")
    result.alpha_composite(frame)
    result.alpha_composite(fill_part(health, amount), (2, 2))
    result.alpha_composite(fill_part(mana, amount), (10, 2))
    return result


def main() -> None:
    frame_native = image(HERE / "native/engine--icons--manafrm.png").resize((20, 102), Image.Resampling.NEAREST)
    frame_candidate = image(HERE / "restored_display/engine--icons--manafrm.png")
    frame_repair = image(HERE / "targeted_repairs/manafrm-review-x2.png")
    health = image(HERE / "native/engine--icons--manag.png").resize((6, 98), Image.Resampling.NEAREST)
    mana = image(HERE / "native/engine--icons--manab.png").resize((6, 98), Image.Resampling.NEAREST)
    sheet = Image.new("RGB", (660, 690), "#192329")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), "manaFRM border with separate health and mana fills", fill="#f3dfaa")
    for row, (label, frame) in enumerate((("Native border", frame_native),
                                         ("Current x2 candidate", frame_candidate),
                                         ("True-alpha imagegen repair", frame_repair))):
        y = 40 + row * 210
        draw.text((12, y), label, fill="white")
        for column, (state, amount) in enumerate((("Empty", 0), ("Half", .5), ("Full", 1))):
            x = 45 + column * 210
            sample = composite(frame, health, mana, amount).resize((30, 153), Image.Resampling.NEAREST)
            sheet.paste(sample.convert("RGB"), (x, y + 27))
            draw.text((x + 43, y + 94), state, fill="#dae5d8")
    OUT.parent.mkdir(exist_ok=True)
    sheet.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
