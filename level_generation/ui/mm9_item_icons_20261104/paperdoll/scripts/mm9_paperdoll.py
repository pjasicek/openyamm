"""Fitted paperdoll art for MM9 worn equipment (pieces.yml), repainted from the new MM7/MM8-style icons.

    python3 scripts/mm9_paperdoll.py prepare <piece>        targets, Codex inputs and one job per master
    python3 scripts/mm9_paperdoll.py codex <piece> [types]  Codex image workers (at most four at once)
    python3 scripts/mm9_paperdoll.py candidates <piece>     every generation fitted and worn, to pick from
    python3 scripts/mm9_paperdoll.py fit <piece> [t<N>=<raw file> ...]
    python3 scripts/mm9_paperdoll.py review <piece>         previews on every doll in both poses, pair checks

The technique is the Hesper one (level_generation/ui/hesper_paperdoll/README.md), itself the MM9 pipeline's
(devdocs/mm9/MM9_ARMOR_PAPERDOLL_AI_GENERATION.md): the reference item's fitted MM7/MM8 files own canvas, silhouette,
pose and placement; the new icon owns the design; a generation is only an RGB proposal, keyed and fitted into the exact
target alpha. This script configures that module for MM9 instead of copying it.

Doll types: human male, human female, minotaur, troll and dwarf (the prototype left the dwarf out; the full pass of
2026-11-05 adds it). The minotaur wears no helm or boots.
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ICON_PROJECT = PROJECT.parent
ROOT = PROJECT.parents[3]
sys.path.insert(0, str(ROOT / 'level_generation/ui/hesper_paperdoll/scripts'))
sys.path.insert(0, str(ICON_PROJECT / 'scripts'))

import paperdoll as P  # noqa: E402
from finish import key  # noqa: E402

P.PROJECT = PROJECT
P.WORK = PROJECT / 'work'
P.RUNTIME = PROJECT / 'runtime'
P.RUNS = PROJECT / 'generation_runs_paperdoll.json'
P.ICON_MASTERS = PROJECT / 'work/_design'          # the new icon's full-size painting, keyed (Image 4)
P.ICONS_X2 = PROJECT / 'work/_icons_x2'            # the new x2 icon, for the review sheet
P.DRAFT_ITEMS = ROOT / 'assets_dev/worlds/mm9/data_tables/items.txt'
P.SLOT_TYPES = {'Armor': (0, 1, 2, 3, 4), 'Helm': (0, 1, 3, 4), 'Boots': (0, 1, 3, 4), 'Belt': (0, 1, 2, 3, 4),
                'Cloak': (0, 1)}
# MM9 helms are open or closed (the table's geometry); the outline is the reference's either way.
P.SLOT_RULES['Helm'] = ('Helm pixels only, inside the grey shape: the helmet\'s metal, rim and guards as Image 1 '
                        'draws them on this head. Where the grey shape leaves the face open, leave it magenta. Do not '
                        'paint skin, a face, hair, horns, the neck below the helm\'s rim, shoulders or armour.')

_hesper_prompt = P.prompt


def prompt(piece, doll_type, canvas):
    return _hesper_prompt(piece, doll_type, canvas).replace('a piece of Hesper equipment',
                                                            'a piece of Might and Magic IX equipment')


def run_codex(job):
    images = sorted(job.glob('in_*.png'))
    rel = job.relative_to(ROOT)
    brief = (PROJECT / 'CODEX_BRIEF.md').relative_to(ROOT)
    instruction = (f'Follow {brief} exactly for the job folder {rel}. '
                   f'The {len(images)} attached images are its inputs 1-{len(images)} in order.')
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', str(ROOT), '--skip-git-repo-check',
                 '--add-dir', str(Path.home() / '.codex/generated_images')]
    for image in images:
        arguments += ['-i', str(image)]
    with (job / 'raw/codex_run.log').open('a') as log:
        result = P.subprocess.run(arguments, input=instruction, text=True, stdout=log, stderr=P.subprocess.STDOUT)
    return job, result.returncode


_hesper_target_alpha = P.target_alpha


def target_alpha(piece, doll_type, weapon=False):
    """The Hesper target, plus `keep_lower` for footwear without a shaft (Fuzzy Slippers): each boot of the
    reference keeps only the lowest share of its own height, so each foot is cut at its own ankle."""
    soft, image, point, report = _hesper_target_alpha(piece, doll_type, weapon)
    share = piece.get('keep_lower')
    if share:
        labels, count = P.ndimage.label(soft > 0, structure=P.np.ones((3, 3)))
        removed = 0
        for index in range(1, count + 1):
            ys = P.np.nonzero(labels == index)[0]
            cut = int(ys.max() + 1 - (ys.max() + 1 - ys.min()) * share)
            part = labels == index
            above = part.copy()
            above[cut:] = False
            removed += int(above.sum())
            soft[above] = 0
            for offset, keep in ((0, 1 / 3), (1, 2 / 3)):      # feathered like the coverage cut
                row = part[cut + offset]
                soft[cut + offset][row] = (soft[cut + offset][row] * keep).astype(P.np.uint8)
        report['keep_lower_removed'] = removed
        report['target_alpha'] = int((soft > 0).sum())
    return soft, image, point, report


def see_through(image, darkness, minimum):
    """Opens the dark cavities of a mask-like helm (eye sockets, nose, mouth) so the doll's face shows through:
    connected regions darker than `darkness` (luminance) that lie inside the piece and are at least `minimum` physical
    pixels, holes in them filled; a one-pixel dark rim stays and the edge is feathered."""
    pixels = P.np.asarray(image.convert('RGBA')).copy()
    alpha = pixels[:, :, 3]
    lum = pixels[:, :, :3].astype(float) @ P.np.array([0.3, 0.59, 0.11])
    dark = P.ndimage.binary_opening((lum < darkness) & (alpha > 0))
    edge = P.ndimage.binary_dilation(alpha < 255, iterations=3)
    labels, count = P.ndimage.label(dark)
    keep = P.np.zeros(dark.shape, dtype=bool)
    for index in range(1, count + 1):
        part = labels == index
        if part.sum() >= minimum and not (part & edge).any():
            keep |= part
    keep = P.ndimage.binary_erosion(P.ndimage.binary_fill_holes(keep))
    ring = P.ndimage.binary_dilation(keep) & ~keep
    alpha[keep] = 0
    alpha[ring] = alpha[ring] // 2
    return P.Image.fromarray(pixels), int(keep.sum())


_hesper_fit = P.fit


def fit(name, picks):
    """The Hesper fit, then `see_through` (pieces.yml: [darkness, minimum]) on every doll file of the piece."""
    _hesper_fit(name, picks)
    piece = P.pieces()[name]
    if piece.get('see_through'):
        darkness, minimum = piece['see_through']
        for file in sorted((P.WORK / name / 'fitted').glob(f'{name}v*.png')):
            opened, count = see_through(P.Image.open(file), darkness, minimum)
            opened.save(file)
            print(file.name, 'see-through pixels', count)


P.prompt = prompt
P.run_codex = run_codex
P.target_alpha = target_alpha
P.fit = fit


def design(name):
    """The piece's design inputs from the icon project: the keyed full-size painting and the x2 icon."""
    item_id = P.pieces()[name]['id']
    designs = P.json.loads((ICON_PROJECT / 'designs.json').read_text())
    design_id = next(entry['design_id'] for entry in designs if item_id in entry['item_ids'])
    folder = ICON_PROJECT / 'items' / str(design_id)      # items sharing a source PCX share one design folder
    P.ICON_MASTERS.mkdir(parents=True, exist_ok=True)
    P.ICONS_X2.mkdir(parents=True, exist_ok=True)
    painting = key(folder / 'paint_a.png')
    painting.crop(painting.getbbox()).save(P.ICON_MASTERS / f'{name}.png')
    P.Image.open(folder / 'icon_a_x2.png').save(P.ICONS_X2 / f'{name}.png')


def main():
    command, name, *rest = sys.argv[1:]
    if command == 'prepare':
        design(name)
        P.prepare(name)
    elif command == 'codex':
        P.codex(name, rest[0] if rest else None)
    elif command == 'candidates':
        P.candidates(name)
    elif command == 'fit':
        P.fit(name, rest)
    elif command == 'review':
        P.review(name)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
