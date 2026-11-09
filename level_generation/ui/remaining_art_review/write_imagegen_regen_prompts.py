#!/usr/bin/env python3
"""Freeze one reviewable imagegen prompt per prepared sprite sheet."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUN = HERE / "imagegen_regen"


def prompt(sheet: dict) -> str:
    count = len(sheet["cells"])
    name = sheet["id"]
    if name.startswith("terra-"):
        number = int(name.split("-")[1])
        if 5 <= number <= 15:
            body = ("the sun rises at the far left horizon" if number == 5 else
                    "the sun moves through the upper-left sky" if number == 6 else
                    "neither the sun nor moon is visible in these frames" if number <= 9 else
                    "the sun moves across the upper and right sky" if number <= 14 else
                    "the moon is at the far left while the sun sets at the far right horizon")
            return f"""Use case: precise-object-edit
Asset type: {count} consecutive frames of the Might and Magic terra sky UI animation, high-resolution master sprite sheet.
Input image: attached sheet is the edit target. Horizontal frames are stacked vertically and separated by pure magenta bands.
Primary request: genuinely restore the original {count} daylight/twilight frames as smooth, detailed painted fantasy sky. Preserve the exact source phase and brightness: {body}. Reconstruct the existing clouds, stars if visible, mountain horizon and dark sea without changing their positions.
Composition: keep all {count} complete opaque frames in order, with an identical fixed horizon and scene geometry. Preserve the original size, brightness, position and incremental trajectory of every visible sun and moon in each frame. Do not add any celestial body absent from the source.
Background/gutters: flat pure magenta only between and outside frames, never within the frames.
Constraints: no added sunrise/sunset, moon, stars or clouds; no changed horizon, crop, rearrangement, text, border, source-pixel enlargement, mosaic shading or blur-only upscale. Restore all frames at full width."""
        moon_region = "upper-right" if number <= 4 else "upper-left moving toward center"
        return f"""Use case: precise-object-edit
Asset type: {count} consecutive frames of the Might and Magic terra sky UI animation, high-resolution master sprite sheet.
Input image: attached sheet is the edit target. Horizontal frames are stacked vertically and separated by pure magenta bands.
Primary request: genuinely restore the low-resolution artwork into smooth, detailed painted fantasy sky. The distant mountains, stars, nebula and horizon are one fixed scene repeated in every frame; only the small shaded moon in the {moon_region} moves incrementally.
Composition: preserve all {count} complete rectangular frames, their order, the exact common sky/horizon silhouette and all boundaries. Keep the moon's original relative size and exact frame-to-frame trajectory. Restore stars, purple-blue nebula, mountain horizon and dark sea while preserving muted luminance and the black lower band. No sun is present.
Background/gutters: pure magenta between and outside frames, never inside them.
Constraints: high-resolution redraw, no enlarged pixel blocks, no blur-only filtering, no new celestial bodies, no rearrangement, no cropping, no text or borders. All frames must stay full opaque rectangles, identical except for moon motion."""
    if name.startswith("small_alpha-inventory_items-"):
        return f"""Use case: precise-object-edit
Asset type: high-resolution master spritesheet for {count} Might and Magic inventory cutouts.
Input image: attached sheet is the edit target and sole identity/geometry reference.
Primary request: redraw every low-resolution inventory item into genuinely restored high-resolution painted fantasy art. Recover continuous contours and fine metal, leather, fabric, stone, jewel and wood detail. Preserve the exact design, palette, silhouette, cutout holes, orientation and distinctive features of each item.
Composition: keep all {count} items separate in their original positions and row order, with the same relative centers and scales. Each complete object must fit within its own original rectangular canvas slot; leave clear empty gutters. Preserve every near-identical variant as a separate item.
Background: genuine transparency throughout all empty canvas and gutters, no shadows or colored halos.
Constraints: no crop, clipped tips, neighboring-cell contamination, invented items, merged objects, text, labels, borders, checkerboard, enlarged pixel blocks, mosaic shading or blur-only upscale. Restore every cell."""
    if name.startswith("small_alpha-"):
        return f"""Use case: precise-object-edit
Asset type: high-resolution master spritesheet for {count} Might and Magic UI art and animation states.
Input image: attached sheet is the edit target and sole identity/geometry reference. Its magenta is only a temporary extraction backing.
Primary request: genuinely restore every low-resolution foreground frame with continuous painted contours and fine coherent material/light detail. Preserve each original shape, orientation, palette, glow, internal landmark, size, partial fragment, faint fading state and sequence. Distinct neighboring animation states must remain distinct.
Composition: retain all {count} independent cells in original positions and row order, with complete artwork inside each original rectangular canvas slot. Keep generous clear gutters.
Background: genuine transparency outside the foreground and through intentional holes, without magenta spill or painted checkerboard.
Constraints: no missing or added states, no combining adjacent frames, no crop, no enlarged pixel blocks, no blur-only filtering, no invented faces or symbols, no text or borders. Restore every occupied cell, including small partial frames."""
    if name.startswith("small_opaque-"):
        return f"""Use case: precise-object-edit
Asset type: high-resolution Might and Magic UI control/panel master sheet with {count} source images.
Input image: attached sheet is the edit target and sole layout reference. The magenta is a separator between complete opaque rectangular UI images.
Primary request: genuinely restore every image with continuous painted texture and crisp intended UI geometry, preserving all original symbols, colors, layout, edges, state differences, lighting and internal details.
Composition: preserve {count} separate complete rectangular images in exact order, positions and proportions. Each opaque image must fill its original rectangle. Keep pure-magenta gutters separate.
Constraints: no missing/merged cells, no crop, no rearrangement, no new labels or symbols, no checkerboard, no pixel-block enlargement or blur-only upscale."""
    if name.startswith("large_opaque-"):
        return """Use case: precise-object-edit
Asset type: high-resolution master of a complete Might and Magic UI image.
Input image: attached image inside a narrow magenta border is the edit target and sole composition reference.
Primary request: genuinely restore smooth painted detail while preserving every geographic/UI landmark, object, line, symbol, color region, perspective and edge at its original position. If this is a map, all coastlines, roads, bridges, rivers, settlement blocks and marker squares are navigational data and must keep their coordinates. If this is a scene or panel, retain its exact composition, geometry and lettering.
Composition: complete original opaque rectangle, same framing and aspect; no crop or zoom. Keep only the narrow outside magenta separator.
Constraints: no new/missing geographic features, labels, symbols or objects; no changed routes or text; no source-pixel blocks, mosaic shading or blur-only upscale."""
    if name.startswith("large_alpha-"):
        return """Use case: precise-object-edit
Asset type: high-resolution Might and Magic transparent UI foreground master.
Input image: attached magenta-backed image is the edit target and sole geometry reference.
Primary request: genuinely restore the original foreground with smooth continuous painted contours, fine detail and faithful material texture. Preserve native silhouette, orientation, color, placement and all intentional holes, thin features and partial edges.
Composition: full source canvas at the same aspect and framing, complete object without clipping or recentering.
Background: genuine transparency outside the foreground, without magenta fringe.
Constraints: no invented decoration, no crop, no background panel, no text changes, no enlarged source pixels, no blur-only upscale."""
    if name.startswith("title-"):
        cell = sheet["cells"][0]
        left, top = cell["tile_origin"]
        return f"""Use case: precise-object-edit
Asset type: high-resolution title-screen illustration tile for Might and Magic: The World of Enroth.
Input image: attached crop is the edit target and comes from original-coordinate tile origin ({left}, {top}) of a larger title image. It already contains detailed art; make a faithful 2× master with finer continuous detail, preserving every subject, line, letterform, color and lighting feature in place.
Composition: exact crop boundaries and full original tile content. Adjacent tiles overlap; preserve border content precisely so they can be stitched without seams. Do not alter any part of the title lettering or invent handwriting.
Constraints: no crop, reframe, zoom, new objects, modified text, painterly simplification, oversized pixels or blur-only upscale."""
    raise ValueError(name)


def main() -> None:
    plan = json.loads((RUN / "plan.json").read_text())
    folder = RUN / "prompts"
    folder.mkdir(exist_ok=True)
    for sheet in plan["sheets"]:
        path = folder / f"{sheet['id']}.txt"
        if not path.is_file() or sheet["id"].startswith("terra-"):
            path.write_text(prompt(sheet) + "\n")
    print(f"Prompts available for {len(plan['sheets'])} sheets")


if __name__ == "__main__":
    main()
