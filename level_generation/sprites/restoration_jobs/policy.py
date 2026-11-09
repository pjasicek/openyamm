"""Authored art directions for the frozen non-creature restoration queue.

These are visual restoration profiles, not declarations of engine blending modes.
"""

QUALITY = """**NON-NEGOTIABLE: RECONSTRUCT HIGH-RESOLUTION ART, DO NOT ENLARGE PIXEL ART.**
The native reference supplies identity, pose, palette and placement, NOT a pixel texture to preserve.
Redraw continuous natural contours, fine material structure and coherent high-resolution shading throughout
EVERY sprite. Inspect both outlines AND interiors: no enlarged square texels, stair-step branches/bars,
block-shaped highlights, source-grid dithering, or pixel blocks under a layer of sharpening/noise.
Blurred or smoothed enlargement alone is also a failure. Reconstruct readable fine detail appropriate to
wood, stone, metal, foliage or flame, with clean antialiased contours and natural shading transitions.
**QUALITY TAKES PRIORITY OVER PIXEL-EXACT SILHOUETTE COPYING.** Modestly thicker branches, slightly different
leaf clusters or small contour variations are welcome when the result is appealing, convincing and faithful
to the asset overall. This overrides overly literal shape-matching language elsewhere in this request.
Preserve identity, overall proportions, native scale, pose, contact/attachment anchors and animation coherence.
Do not move the sprite in its cell or make grounded objects float. A large output canvas is not evidence of
restoration quality. The full-resolution master must stand up to close inspection before downsampling.
"""

COMMON = """Use case: precise image restoration for an actual Might and Magic VI-VIII game sprite.
The FIRST reference is the edit target: correctly paletted original art, with exact cell positions.
Restore the SAME depicted asset(s), perspective, pose, component count, proportions and material colors.
Clarify realistic material detail and smoothly reconstruct the intended contour beneath the low-resolution
pixel staircase. Do not preserve enlarged square pixel blocks. Do not redesign the object or add decoration.
Keep the original dark tonal weight, directional shading and readable large shapes. Avoid bright studio
lighting, plastic, cartoon outlines, excessive sharpening, oversaturation, new rim lights or added bloom.
Dark painted regions are NOT holes. Preserve only openings actually transparent in the reference.
Keep all original detached pieces, thin stems, tips, handles and supports. Do not invent a ground plane,
cast shadow, text, border, labels, checkerboard or watermark. No cropped or duplicated parts.
"""

PROFILES = {
    'foliage': {
        'direction': 'Preserve species, crown shape, trunk bends, branch structure, leaf clusters, seasonal color, '
                     'fruit/flower count and snowy or dead state. Reconstruct small natural leaves and bark inside '
                     'the existing masses, with airy gaps and fine twigs; no enlarged clumps of plastic foliage.',
        'checks': ['Species/state and silhouette match; no extra fruit, snow or flowers.',
                   'Dark foliage, fine twigs and transparent gaps survive on light and dark backgrounds.'],
    },
    'solid': {
        'direction': 'Preserve the original stone, wood, metal, bone, fabric or glass material boundaries. '
                     'Clarify wear, facets, seams and small highlights already suggested by the source. '
                     'Keep dents and asymmetry. For small ground items preserve the lying/slanted orientation; '
                     'do not turn the item upright as a product photograph.',
        'checks': ['Materials, angle, count, thin parts and true holes match the native source.',
                   'No new geometry or falsely transparent dark patches; no matte-colored contour.'],
    },
    'animated_prop': {
        'direction': 'This is one prop at successive native animation moments. Rigid supports, pots, poles, '
                     'chains, pedestal bases, cages and lantern shells must remain identical. Animate ONLY '
                     'the source moving elements (flames, sparks, cloth, light, swinging or bobbing parts). '
                     'Follow actual source motion, not an invented spin. Fire must retain soft luminous tips '
                     'without turning dark iron/wood into transparent light. Match loop endpoints.',
        'checks': ['Rigid components do not melt, breathe or change design between frames.',
                   'Source motion/timing/loop preserved, including deliberate bobbing or swinging.',
                   'Flame/glow fringe survives cleanup; dark physical support remains opaque.'],
    },
    'water_prop': {
        'direction': 'Keep the rock, fountain basin, statue or support identical across frames. Only water, '
                     'foam, spray and reflections change as in the original. Preserve the native waterline '
                     'and localized footprint; no extra pond, landscape or blue opaque halo. Water and spray '
                     'retain soft edges, while solid stone stays solid. Match the native loop.',
        'checks': ['Rock/basin silhouette remains fixed; waterline and splash reach match.',
                   'No opaque background-colored water fringe or erased fine spray.'],
    },
    'soft_fx': {
        'direction': 'Restore the exact visible spell/effect shapes and their native time evolution, including '
                     'small particles, trails, wisps and dark smoke where present. Preserve hue, energy, '
                     'extent and quiet/bright moments. Do not inflate the effect into a cinematic explosion. '
                     'Maintain soft falloff and internal translucency. If a physical core is visible, retain '
                     'its original opacity and shape. No hard cutout rim around light or smoke.',
        'checks': ['Timing progression, hue, footprint, quiet frames and detached particles match.',
                   'Soft energy survives on black/gray; smoke still darkens a light background.',
                   'No assumption that every FX sprite is additive; preserve the source look.'],
    },
    'ui': {
        'direction': 'This is original game interface artwork, not a world prop. Preserve the exact sign, '
                     'hand gesture, symbol, border, inset square and negative space seen in the source. '
                     'Keep its native visual weight and orientation. Animate only the depicted hand, sand, '
                     'boots, water or symbol changes. Do not add a panel or erase an existing panel.',
        'checks': ['UI border/negative space/symbol/gesture and animation state match.',
                   'No ground anchor substituted for UI placement; retain canvas and table flags.'],
    },
    'weather': {
        'direction': 'This is a repeating weather particle field. Keep its density, streak direction, '
                     'particle length distribution and sparse/empty regions. Reconstruct smooth fine '
                     'rain streaks or snow specks without adding clouds, scenery, glow or large flakes. '
                     'Keep the original full-frame field placement and native sequence.',
        'checks': ['Full-frame field density, motion direction and coverage retained.',
                   'Inspect repeated tiles for obvious borders; no invented weather scenery.'],
    },
}

# Contact-sheet audit 2026-09-09: actual images take precedence over vague object-list labels.
SOLID_EFFECT_IDS = {91, 623, 681, 686, 702, 708, 709, 725, 770, 771, 805, 813,
                    869, 875, 911, 918, 919, 7761, 7763, 8019, 17030, 17036, 17039,
                    17047, 17061, 17067, 17106, 17118, 17142, 17206, 17212, 17225,
                    17240, 17256, 17271, 17294, 17298, 17327, 17333, 17336, 17389,
                    17405, 17410, 17416, 17595, 17658, 17660, 17662, 17702, 17812,
                    17961, 17963}
SOFT_DECORATION_IDS = {876, 896}  # OrMatt proxies: actual fireball / light sprite.
WATER_GROUPS = {'splash', '7splash', '6splash', 'fount1', 'searka01', 'searkb01', '7dec35'}
UI_HINTS = {
    'newhand1': 'animated hand cursor/gesture', 'newglas1': 'animated hourglass',
    'c2_hero': 'heroism overlay', 'c3_haste': 'haste overlay', 'c4_shild': 'shield overlay',
    'c5_sskin': 'stone skin overlay', 'guardang': 'guardian angel overlay', 'c1_bless': 'bless overlay',
    'turnmode': 'red stop-hand turn indicator', 'wizeye': 'wizard eye indicator',
    'aframe1': 'animated oval selection frame', 'fly1': 'flying boots indicator',
    'i1_fall': 'feather-fall icon', 'i2_fire': 'fire protection icon', 'i3_ltng': 'lightning protection icon',
    'i4_cold': 'cold protection icon', 'i5_poisn': 'poison protection icon',
    'i6_magic': 'magic protection icon', 'watwalk1': 'water-walking boots indicator',
}
REPAIRS = {
    'shape': 'Correct ONLY the silhouette/components to match the original edit-target cells. '
             'Restore missing thin parts and fill falsely invented holes. Keep accepted material detail.',
    'pixel_steps': QUALITY + 'Reconstruct this failed candidate from the native reference; replace pixel blocks '
                   'in interior shading as well as edges. Preserve native anchors and overall identity.',
    'motion': 'Lock rigid structure and shared material details across cells. Restore the original '
              'frame-by-frame pose/extent and cell-relative placement. Do not normalize all poses to one size.',
    'spill': 'Remove backdrop-colored rim, reflections and halo from the foreground, including holes. '
             'Preserve genuine colored material and ONLY the soft light/smoke present in the FIRST native reference. '
             'Remove invented clouds, fog and broad glow from the failed candidate wherever the native reference '
             'has empty space, including ring centers and gaps between sparks. Do not keep haze merely because '
             'it appears in the SECOND candidate. Keep fine reconstructed foreground detail and native placement. '
             'Return true RGBA transparency in all empty areas; do not paint a backdrop or transparency preview.',
    'layout': 'Restore the requested equal-cell grid exactly. Keep each sprite in its assigned cell at '
              'the reference position/scale, with the remaining cells empty. No borders or labels.',
    'tone': 'Match the original darker material tonal weight without crushing black detail. '
            'Preserve native hue variation and luminosity changes across the sequence.',
}

ALPHA_MASK = """Use case: precise opacity-mask extraction from an existing restored game sprite sheet.
The FIRST reference is the exact generated RGB sheet to mask, not an image to redesign. The SECOND is
the original native sheet, supporting which dark areas are solid and which gaps are genuinely empty.
Return ONLY a grayscale opacity mask, on the exact first-image canvas and grid: pure white for opaque
foreground (including dark materials and foreground colors similar to the backdrop), pure black for the
flat backdrop and actual holes, and appropriate smooth gray opacity for antialiased edges, thin leaves,
spray, flame/glow and smoke. Do not redraw, move, thicken, crop, enlarge or simplify any silhouette.
Do not turn internal shadows into transparent holes. Preserve every disconnected sprite fragment.
No color, labels, border or checkerboard. Pixel registration with the first reference is critical.
"""


PLACEMENT = """PLACEMENT AND ANCHOR PRESERVATION — REQUIRED
The native reference is authoritative for identity and placement; QUALITY permits modest contour variation.
Preserve each object's position, scale, proportions and empty margins within its reference cell.
Do not independently centre, enlarge, shrink or bottom-align the visible object. Preserve the
reference layout and cell boundaries.
For grounded objects, keep actual solid contact points (trunk roots, feet, pole bottom, pedestal
base, rock underside) at their original coordinates. Faint pixels, shadows or detached details
must not substitute for solid contact.
Preserve relative internal landmarks: trunk versus canopy, pedestal base versus bowl, pole versus
flag, supports versus body. Improve detail and smooth edges without changing these relationships.
For animation/state variants, keep rigid geometry and its anchor consistent. Change only parts
that change in the native sequence. Preserve intentional bobbing/movement; do not normalize each
frame to the same bounding box. For suspended objects, water objects and effects, preserve their
native anchor instead of inventing ground contact. Do not add ground, shadows, supports, padding
or objects absent from the reference. Keep empty areas genuinely transparent (alpha 0).
"""

LEGACY_MAGENTA_BACKGROUND = ('Background contract: opaque flat pure magenta RGB(255,0,255) '
              'outside the sprite and in true holes. '
              'Do not draw a checkerboard, ground or shadows. Keep backdrop color out of foreground contours. '
              'Retain real magenta material, dark solid supports, and soft transitions in flame/water/smoke. '
              'A legacy reference may have another backdrop; change only its backdrop to the requested magenta.\n')

BACKGROUND = ('Background contract: genuine transparent RGBA; empty areas and true holes must have alpha 0. '
              'No painted checkerboard, matte, ground or shadow. Keep solid materials opaque and preserve '
              'soft effect transitions. A legacy reference may have a colored backdrop; remove only that backdrop.\n')
