# Transparent spell foreground review stage

**Superseded by [the full-master v2 stage](../spell_foreground_stage_v2/index.html).** This first stage reused
incomplete extracted candidates and cut some glyphs or neighboring cells. Its files remain as attempt provenance;
do not use its previews for approval.

Open [index.html](index.html) directly in a browser. The page compares each native original, prior 2× candidate,
and transparent 2× foreground on checker, dark or light backgrounds. Color and sepia states are grouped by spell.
Use **Approve** or **Flag** per state, add a reason and note, then download the review JSON. Browser decisions bind
the native source and staged candidate SHA-256 hashes. Nothing here changes game assets or checkpoint acceptance.

The stage contains 111 pairs / 222 states:

- 58 states from 15 newly edited paired sheets. Each source sheet and actual imagegen prompt is in `batches/NN/`.
- 18 states use the separately saved ink from accepted Air spell assemblies.
- 146 states retain an existing foreground with genuine alpha, including Air spells without accepted ink assemblies.

`prepare.py` reconstructs the references from the full review catalog. `finalize.py` finds the returned transparent
gutters, extracts each color/sepia pair with shared fitting, writes exact native-times-two PNGs in `candidates/`,
and records raw hashes, source hashes, crop positions and alpha measurements in `manifest.json` / `manifest.js`.
All new sheet edits used the built-in image generation tool. The original sheet returns remain in each batch's
`raw.png`; no generated image is referenced only from the Codex image store.

The stage is for visual approval. Check the identity and position of every glyph, pair colors, fine hatching and
soft edges. Some edited returns have warm red edge pixels, especially in sepia states; they are exposed on the
light/dark backdrops for review. The native page and any accepted page restoration are separate from these
foreground files. A transparent icon stage does not establish the final in-game composition or placement.
