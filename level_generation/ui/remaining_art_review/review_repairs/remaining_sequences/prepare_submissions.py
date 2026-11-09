#!/usr/bin/env python3
"""Freeze built-in imagegen prompts for the remaining complete PC effect sequences."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
DESCRIPTIONS = {
    "spell03e": "Fire-orange and gold magical arcs grow from a thin left sliver into a hollow crackling ring, then recede. Keep the distinct open center, warm rocky flame texture, and sparse endpoint phases.",
    "sp17e": "A single pointed silver-and-olive metal shield with a smoky gray reflective center assembles from a partial left piece into a whole shield. Preserve the growing silhouette and the same shield identity across all frames; do not turn the early partial frames into full shields.",
    "sp21a": "One small brown leather winged boot, with two pale feathered wings and sparse white-gold sparkles. Keep the same boot shape and position while the wings and glints animate; no second boot or person.",
    "sp25e": "An icy blue-white oval of layered curling wind or water bands. The first and last phases are very faint translucent outlines; middle frames are brighter full swirls. Preserve blue-gray shadows, ring-like bands and subtle phase changes, with no magenta or pink.",
    "sp27a": "One small gray humanoid walking in place on a broad indigo-violet circular magic platform, with scattered white sparkles. Preserve the same single figure, eight walking poses, platform shape and fixed placement. The figure and platform must not merge into a solid disc.",
    "sp38e": "A rough weathered gray stone oval or stone face forming from a top sliver into a complete upright oval, darkening and cracking before a faint final fade. Preserve the construction and dissolution phases, stone grain and native silhouette.",
    "spell46e": "A single upright gold ankh with a hollow oval loop, horizontal arms and a straight tapered stem. A brilliant white-gold star flash grows at its center in the middle phases. Sparse first and last frames stay translucent; do not close the loop or invent inscriptions.",
    "spell47e": "Small separated silver-white and pale blue star glints form a loose hollow oval, then fade. Preserve the distinct scattered-star phases and genuinely empty spaces between glints. No filled globe, solid disc or continuous opaque ring.",
    "sp51e": "One antique olive-gold oval medallion with a consistent faint woman's face and a bright vertical glint. It turns from an edge-on sliver toward a frontal face, brightens, then turns back edge-on. Preserve the same face, rim and rotation phases.",
    "sp58e": "A pale lavender-white luminous arch or layered horizontal magical bands on the UPPER THIRD of the portrait canvas. The arc expands to a central white starburst and fades. Preserve the top anchor and completely transparent lower canvas; do not recenter the arch vertically or fill the lower area.",
    "spell56e": "A radial silver-white six-armed magical snowflake or star with a warm orange glowing center. Keep each distinct spoke, the irregular cutout gaps, its warm center and the fade-in and fade-out endpoint phases. No generic filled star or extra symbols.",
    "spell67e": "Several separate rounded green-yellow light droplets in the early phases change into icy blue-white crystalline spark clusters in the later phases. Preserve each frame's fragment arrangement and the exact green-to-white color progression; transparent gaps stay empty.",
    "sp71e": "An oval of pale pink, lavender and white layered curling magical wind bands. Sparse translucent checker-pattern endpoints represent a fade, not a painted checkerboard. Middle phases are bright pink-violet swirls with gray-violet shadows, consistent size and style.",
    "sp77e": "Bright silver-white and icy blue starbursts grow in a loose vertical oval, ending as a hollow ring of individual glints. Preserve detached stars, blue shadows and each frame's intensity and location. Do not make a solid opaque egg.",
    "sp83e": "Separated white-silver and yellow-gold magical sparks swirl around a hollow vertical oval. The middle phases flash warm yellow, then return to pale silver. Preserve open interior gaps and exact color and density progression, with no solid disc.",
    "sp96h": "A crimson-red draped magical curtain or veil hangs from the TOP EDGE of the portrait canvas and descends over time, with dark red fabric folds and a bright red scalloped lower edge. Preserve the fixed top anchor and transparent area below. This is a top-anchored overlay, not an oval, banner, landscape or full-screen red fill.",
    "sp109": "The same small hooded blue-gray robed figure hovers above a separate white-gray cloud or mist oval. Keep the figure's robe, hidden face, arm spread, cloud placement and six subtle animation phases consistent. Do not add a second figure or merge the cloud into the robe.",
    "sptext01": "Four full opaque square panels of dense marbled red-and-black magical texture with subtle phase changes. Preserve the straight square boundaries, full panel coverage and dark red color. The magenta outside each square is matte only. No text, glyphs, beveled frame or rounded oval.",
}


def main() -> None:
    jobs = json.loads((HERE / "jobs.json").read_text())["jobs"]
    if set(jobs) != set(DESCRIPTIONS):
        raise ValueError("Prompt descriptions do not match all remaining sequences")
    submissions = []
    for family, job in jobs.items():
        for output in job["outputs"]:
            count = len(output["frame_numbers"])
            columns = output["columns"]
            rows = (count + columns - 1) // columns
            if len(job["outputs"]) == 1:
                image_role = (f"Image 1 is the authoritative native original containing ALL {count} consecutive "
                              f"frames in {columns} columns by {rows} rows, row-major order.")
                references = [output["reference"]]
            else:
                count_word = "SIX" if count == 6 else "THREE"
                image_role = (f"Image 1 is the authoritative native full TWELVE-frame sequence. "
                              f"Image 2 isolates native frames {output['frame_numbers'][0]} through "
                              f"{output['frame_numbers'][-1]} for this return. Render precisely those {count_word} frames "
                              f"in {columns} columns by {rows} rows; retain continuity with the entire twelve-frame cycle.")
                references = [output["full_reference"], output["reference"]]
            prompt = (
                "Use case: precise-object-edit. Asset type: OpenYAMM 2D PC portrait effect animation. "
                + image_role + " Restore the complete requested sequence together as smooth, detailed, "
                "coherent painted 2D artwork. " + DESCRIPTIONS[family] + " "
                "Treat the original as authoritative for object identity, frame order, silhouette, phase progression, "
                "relative size, material, color and placement. Keep every frame distinct but use one consistent "
                "artistic style, texture and lighting. Each complete frame must remain inside its own equal cell "
                "with wide genuinely transparent gutters on all sides and between rows; no cutoffs, overlap or "
                "neighboring-cell material. The source magenta is a transparency key only; return true RGBA alpha "
                "outside the art and through intended openings, with clean edges and no magenta spill. "
                "Do not add objects, text, labels, grid lines, black backdrops, painted checkerboards or extra frames. "
                f"Return one {columns}-column by {rows}-row spritesheet."
            )
            submissions.append({"name": output["name"], "family": family, "frame_numbers": output["frame_numbers"],
                                "prompt": prompt, "references": references,
                                "reference_hashes": [output.get("full_reference_sha256"), output["reference_sha256"]]
                                if len(references) == 2 else [output["reference_sha256"]],
                                "status": "prepared"})
    (HERE / "submissions.json").write_text(json.dumps({"schema": 1, "tool": "built-in imagegen",
                                                   "submissions": submissions}, indent=2) + "\n")
    print(f"Prepared {len(submissions)} imagegen submissions for {len(jobs)} complete sequences")


if __name__ == "__main__":
    main()
