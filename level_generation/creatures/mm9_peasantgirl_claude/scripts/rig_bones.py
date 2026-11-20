"""Shared rig tables (PeasantGirl, MM9 child girl skeleton PEASANTCHILDGIRL, 60 joints, Bip01 names, raw ABC: L at -x)."""
SIDES = ('L', 'R')
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
PRE = 'Bip01 '
# skirt chains by azimuth, XCOM_skirt prepended (the waist), top to hem. xbk_rt_a3 (MM9 has no xbk_rt3) is left out so the weights
# stay mirror-symmetric: the last link of both back-side chains is the *2 joint.
SKIRT_CHAINS = [['XCOM_skirt', 'xfr', 'xfr1', 'xfr2', 'xfr3'],
                ['XCOM_skirt', 'xfr_rt_a', 'xfr_rt_a1', 'xfr_rt_a2'], ['XCOM_skirt', 'xrt_a', 'xrt_a1', 'xrt_a2', 'xrt_a3'],
                ['XCOM_skirt', 'xbk_rt_a', 'xbk_rt_a1', 'xbk_rt_a2'], ['XCOM_skirt', 'xbk', 'xbk2', 'xbk3'],
                ['XCOM_skirt', 'xbk_rt', 'xbk_rt1', 'xbk_rt2'], ['XCOM_skirt', 'xrt', 'xrt1', 'xrt2', 'xrt3'],
                ['XCOM_skirt', 'xfr_rt', 'xfr_rt1', 'xfr_rt2']]
SKIRT_MIRROR = {}
for a, b in (('xfr_rt', 'xfr_rt_a'), ('xrt', 'xrt_a'), ('xbk_rt', 'xbk_rt_a')):
    for s in ('', '1', '2', '3'):
        SKIRT_MIRROR[a + s] = b + s; SKIRT_MIRROR[b + s] = a + s
SKIRT_MIRROR.pop('xbk_rt3'); SKIRT_MIRROR.pop('xbk_rt_a3')      # MM9 has xbk_rt_a3 only; it carries no weight
SPINE = ['Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2']        # bottom to top (PeasantF5's Spine1..3)
def half_pairs():
    """Half-way helpers at the joints that fold: (helper, child bone, helper's node parent, weight bones of the parent side)."""
    out = []
    for s in SIDES:
        pre = f'Bip01 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip01 Spine2', 'Bip01 Spine1')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
    out.append(('Bip01 XhalfHead', 'Bip01 Head', 'Bip01 Neck', ('Bip01 Neck',)))
    return out
