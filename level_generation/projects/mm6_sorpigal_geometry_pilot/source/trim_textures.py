"""Trim textures that belong to the material they sit on: one Codex image job per texture, in parallel.

  python3 source/trim_textures.py [stem ...]      # all of TRIMS when no stem is given

Each trim is a dressed (cut, smoothed) or board version of a host texture of the town: the same colour family and
surface grain, so coping, caps, sills and plinths read as part of the building (user, 2026-11-11: borrowed light
granite on dark rubble looked pasted on). Writes textures/codex/BRIEF_<stem>.md and textures/codex/<stem>.png;
source/make_textures.py turns the PNGs into the source tree.
"""
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
CODEX = PROJECT / 'textures/codex'
MASTERS = ROOT / 'assets_source/worlds/mm6/textures_x4'

ASHLAR = """- Dressed ashlar: rectangular cut stone blocks in running bond, 4 courses over the tile height, blocks 1.5 to 2.5
  times as long as they are high, thin mortar joints (2-4 % of the tile), slightly chamfered block edges."""
BOARDS = """- Wooden boards running horizontally across the tile: 4 boards over the tile height, butt joints staggered,
  thin dark gaps between boards, visible grain and a few nail heads."""

# stem: (host texture, use, content, colour)
TRIMS = {
    'rblcut': ('rblbw', 'coping stones on the town walls, cap stones on the gate pillars and wall piers, rims of '
               'planters and wells, plinth courses',
               ASHLAR, 'the same grey river stone as the stones in input 1: the same mid grey with lighter and darker '
               'speckle, mean brightness about 1.1x that of input 1, faces hewn flat but keeping the stone grain'),
    'tewcut': ('tewd', 'quoins, cornice, plinth, sills, coping and battlements of a black goblin castle',
               ASHLAR, 'the same near-black rough stone as input 1, cut into blocks: same colour, same pitted rock '
               'grain on the faces, mean brightness about 1.15x that of input 1, edges catching a little light; '
               'not smooth, not blue, not uniform grey'),
    'tavcut': ('tav128wl', 'sills, string courses, plinths and coping on a tawny sandstone tower and tavern',
               ASHLAR, 'the same tawny ochre sandstone as input 1, a little lighter and finer grained (dressed '
               'faces), mean brightness about 1.1x that of input 1'),
    't1cut': ('t1wl5lea', 'sills, plinths and coping on the pink-veined marble temple and town hall',
              ASHLAR, 'the same pale pink marble with red-brown veins as the blocks in input 1, joints the dark '
              'grey of input 1, mean brightness like input 1'),
    'thcut': ('thle', 'window sills, plinths and coping on red-brick buildings with the terracotta pilasters of '
              'input 1', ASHLAR, 'the warm terracotta of the carved pilaster in input 1, between it and the red '
              'brick, a little lighter than the brick (a green-grey trim looked pasted on, r2)'),
    'slatecap': ('pbtrm', 'ridge and hip caps and fascia on roofs of the charcoal and grey striped slates of input 1',
                 ASHLAR.replace('4 courses', '2 courses'), 'charcoal grey slate like the darker stripes of input 1, '
                 'smooth, faintly blue-grey, no red or brown'),
    'rhwood': ('rhctr', 'window sills, fascia boards and post caps on red-painted barns and stables',
               BOARDS, 'the dark barn-red painted wood of the frame boards in input 1, paint worn at the edges '
               'showing dark wood, mean brightness like the frame boards in input 1'),
    'pxshcap': ('pxshings', 'ridge and hip caps and fascia boards on roofs of the weathered cedar shingles in '
                'input 1', BOARDS, 'the same weathered brown-orange cedar as the shingles in input 1, a little '
                'darker (mean brightness about 0.85x of input 1)'),
    'plrcap': ('plruf01', 'ridge and hip caps and fascia boards on roofs of the grey weathered shingles in input 1',
               BOARDS, 'the same silver-grey weathered wood as the shingles in input 1, a little darker (mean '
               'brightness about 0.85x of input 1)'),
    'dockdeck': ('cedvwal1', 'the deck of a wooden pier, with the planks laid across the pier, and the thick edge '
                 'boards and piles of the same pier',
                 '''- Deck planks running VERTICALLY in the image (top to bottom), 4 broad planks across the tile width, each
  plank one piece over the tile height or with one staggered butt joint, thin dark gaps between planks, a pair of
  nail heads where each plank crosses a joist (2 rows of nails over the tile height, at 25 % and 75 %).''',
                 'clean golden-brown seasoned timber like input 1 but less orange and with fewer knots, fine grain, '
                 'slight wear, mean brightness like input 1'),
    # Frozen Highlands, Free Haven, Silver Cove and Castle Ironfist (2026-11-12).
    'cscut': ('csbr128', 'coping, sills, plinths and caps on castles of the purple-grey ashlar of input 1',
              ASHLAR, 'the same cool purple-grey stone as input 1, dressed smoother, a step lighter (about 1.15x)'),
    'strcut': ('strctr', 'sills, coping and plinths on houses of the pink-brown flagstone rubble of input 1',
               ASHLAR, 'the same warm pink-brown stone as the flags in input 1, dressed flat, joints the pale grey '
               'of input 1, a step lighter (about 1.1x)'),
    'hccut': ('hcwall', 'coping, cornices, plinths and sills on the tan ashlar castle of input 1',
              ASHLAR, 'the same pale tan sandstone as input 1, larger and smoother blocks, a step lighter'),
    'gbcut': ('gbcnt', 'sills, coping and plinths on buildings of the dark charcoal brick of input 1',
              ASHLAR, 'dark charcoal grey dressed stone matching the bricks of input 1, a step lighter (about 1.3x)'),
    'dkwood': ('dkwle', 'sills, fascia boards and post caps on dark plank walls framed by the orange-brown beams '
               'of input 1', BOARDS, 'the orange-brown stained timber of the frame beams in input 1'),
    'snowcap': ('sgstrrf', 'ridge and hip caps and fascia boards on the snow-laden plank roofs of input 1',
                BOARDS, 'the same red-brown planks as input 1 with a thin crust of the same snow along the upper '
                'edge of each board, a little darker than input 1'),
    'pbrcap': ('pbroof', 'ridge and hip caps and fascia on the grey-green standing-seam metal roofs of input 1',
               BOARDS.replace('Wooden boards', 'Folded metal strips').replace('visible grain and a few nail heads',
               'faint rust streaks and rivets'), 'the same weathered grey-green metal as input 1 with its rust, '
               'a little darker'),
    'thatchcap': ('strroof1', 'the ridge and hip rolls of the straw thatch roofs of input 1',
                  '''- A thatch ridge roll: dense straw bundles laid across the tile, bound by two thin dark hazel
  rods running horizontally at 30 % and 70 % of the tile height.''', 'the same golden-brown straw as input 1, '
                  'a little darker and denser'),
    'roofcap': ('roof', 'ridge and hip caps and fascia boards on the brown wooden shingle roofs of input 1',
                BOARDS, 'the same red-brown weathered wood as the shingles in input 1, a little darker (0.85x)'),
}

BRIEF = """# Texture brief: {stem}

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
{out}

Use: {use}, in New Sorpigal, a town of Might and Magic VI (OpenYAMM). It sits directly on the texture in input 1
({host}.png) and must look like part of the same building: {colour}.

Content:
{content}
- No moss, no colour cast beyond input 1's own, no carving, no decoration.

Rules:
- Seamless on both axes: the left edge continues into the right edge and the top into the bottom with no visible
  seam; courses or boards must line up across the top/bottom edge.
- Straight-on orthographic view, even flat lighting, no cast shadows, no perspective, no vignette, no text.
- Painterly-realistic texture matching the 1990s-remastered style of input 1; detail readable at 512x512.

Generate it with your built-in image generation tool, check the seams yourself (offset the image by half in both
axes with a quick script) and compare its mean colour with input 1's; regenerate once if a seam, a perspective or a
clear colour mismatch is visible. Save only the PNG.
"""


def main():
    stems = sys.argv[1:] or list(TRIMS)
    jobs = []
    for stem in stems:
        host, use, content, colour = TRIMS[stem]
        out = CODEX / f'{stem}.png'
        brief = CODEX / f'BRIEF_{stem}.md'
        brief.write_text(BRIEF.format(stem=stem, out=out.relative_to(ROOT), use=use, host=host, colour=colour,
                                      content=content))
        prompt = (f'Follow the brief in {brief.relative_to(ROOT)} exactly. The attached image is input 1 '
                  f'({host}.png). Use your built-in image generation tool. Do not modify any other file.')
        log = open(CODEX / f'run_{stem}.log', 'w')
        jobs.append((stem, subprocess.Popen(
            ['codex', 'exec', prompt, '-c', 'model_reasoning_effort=medium', '-C', str(ROOT), '-s',
             'workspace-write', '--add-dir', str(Path.home() / '.codex/generated_images'),
             '-o', str(CODEX / f'last_{stem}.md'), '-i', str(MASTERS / f'{host}.png')],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)))
    for stem, job in jobs:
        print(stem, 'exit', job.wait(), 'ok' if (CODEX / f'{stem}.png').exists() else 'MISSING')


if __name__ == '__main__':
    main()
