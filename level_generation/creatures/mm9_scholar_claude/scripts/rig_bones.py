"""Shared rig tables (Bembridge Scholar, SCHOLAR.abc Bip01 skeleton, raw ABC: R at +x, the 01 chains at +x)."""
SIDES = ('L', 'R')
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
# the eight robe chains by azimuth, waist to hem
SKIRT_CHAINS = [['XFbase', 'XFpiv', 'XFa', 'XFb', 'XFc', 'XFd', 'XFe'],
                ['XFRbase01', 'XFRpiv01', 'XFRa01', 'XFRb01', 'XFRc01', 'XFRd01', 'XFRe01'],
                ['XRbase01', 'XRpiv01', 'XRa01', 'XRb01', 'XRc01', 'XRd01', 'XRe01'],
                ['XBRpiv01', 'XBRa01', 'XBRb01', 'XBRc01', 'XBRd01', 'XBRe01'],
                ['XBbase', 'XBpiv', 'XBa', 'XBb', 'XBc', 'XBd', 'XBe'],
                ['XBRbase', 'XBRpiv', 'XBRa', 'XBRb', 'XBRc', 'XBRd', 'XBRe'],
                ['XRbase', 'XRpiv', 'XRb', 'XRc', 'XRd', 'XRe'],
                ['XFRbase', 'XFRpiv', 'XFRa', 'XFRb', 'XFRc', 'XFRd', 'XFRe']]
SKIRT_MIRROR = {}
for b in ('XFRbase', 'XFRpiv', 'XFRa', 'XFRb', 'XFRc', 'XFRd', 'XFRe', 'XRbase', 'XRpiv', 'XRb', 'XRc', 'XRd', 'XRe', 'XBRpiv', 'XBRa', 'XBRb',
          'XBRc', 'XBRd', 'XBRe', 'Yhairpiv', 'Yhair'):
    SKIRT_MIRROR[b] = b + '01'; SKIRT_MIRROR[b + '01'] = b
SKIRT_MIRROR['XRa01'] = 'XRb'; SKIRT_MIRROR['XBRbase'] = 'XBRpiv01'
def half_pairs():
    out = []
    for s in SIDES:
        pre = f'Bip01 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip01 Spine3', 'Bip01 Spine2')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
    out.append(('Bip01 XhalfHead', 'Bip01 Head', 'Bip01 Neck', ('Bip01 Neck',)))
    return out
