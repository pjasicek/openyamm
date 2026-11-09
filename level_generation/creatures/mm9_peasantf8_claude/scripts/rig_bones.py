"""Shared rig tables (PeasantF8, MM9 human female skeleton, raw ABC names)."""
SIDES = ('L', 'R')
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
# skirt chains by azimuth, XCOM_skirt prepended (the waist), top to hem; raw ABC: the _a / unsuffixed L-R pairs as MM9 names them
SKIRT_CHAINS = [['XCOM_skirt', 'xfr', 'xfr1', 'xfr2', 'xfr3', 'xfr4'],
                ['XCOM_skirt', 'xfr_rt_a', 'xfr_rt_a1', 'xfr_rt_a2'], ['XCOM_skirt', 'xrt_a', 'xrt_a1', 'xrt_a2', 'xrt_a3', 'xrt_a4'],
                ['XCOM_skirt', 'xbk_rt_a', 'xbk_rt_a1', 'xbk_rt_a2', 'xbk_rt_a3', 'xbk_rt_a4'], ['XCOM_skirt', 'xbk1', 'xbk2', 'xbk3', 'xbk4'],
                ['XCOM_skirt', 'xbk_rt', 'xbk_rt1', 'xbk_rt2', 'xbk_rt3', 'xbk_rt4'], ['XCOM_skirt', 'xrt', 'xrt1', 'xrt2', 'xrt3', 'xrt4'],
                ['XCOM_skirt', 'xfr_rt', 'xfr_rt1', 'xfr_rt2']]
SKIRT_MIRROR = {}
for a, b in (('xfr_rt', 'xfr_rt_a'), ('xrt', 'xrt_a'), ('xbk_rt', 'xbk_rt_a'), ('xpony', 'xpony_a')):
    for s in ('', '1', '2', '3', '4'):
        SKIRT_MIRROR[a + s] = b + s; SKIRT_MIRROR[b + s] = a + s
def half_pairs():
    """Half-way helpers at the joints that fold: (helper, child bone, helper's node parent, weight bones of the parent side)."""
    out = []
    for s in SIDES:
        pre = f'FHP {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'FHP Spine3', 'FHP Spine2')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
    out.append(('FHP XhalfHead', 'FHP Head', 'FHP Neck', ('FHP Neck',)))
    return out
