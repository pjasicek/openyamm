"""MM9 GOAT.abc rig configuration shared by the project's scripts (fit, weights, reduction, UVs, gates).
+X is the goat's LEFT side (the MM9 '01' leg bones; the ears are the other way round: Xear at +X)."""
NAME = 'Goat'
CHAINS = {
    'leg_fl': ['Xflegpiv01', 'Xfleg01', 'Xfankle01', 'Xffoot01'],
    'leg_fr': ['Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot'],
    'leg_hl': ['Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01'],
    'leg_hr': ['Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot'],
    'tail': ['Xtailpiv', 'Xtail'],
}
BLEND = {'leg_fl': 0.08, 'leg_fr': 0.08, 'leg_hl': 0.09, 'leg_hr': 0.09, 'tail': 0.04}
TAIL_MAXDIST = 0.06
LEG_TOP = 0.05
HEAD_BONES = ['Xheadpiv', 'Xhead', 'Xjawpiv', 'Xjaw', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01']
SKULL = 'Xhead'
JAW_BONES = ['Xjawpiv', 'Xjaw']
EAR_BONES = ['Xearpiv', 'Xear', 'Xearpiv01', 'Xear01']
NECK_BONES = ['Xneckbase', 'Xneckpiv', 'Xneck']
MIRROR = {}
for _a in ['Xearpiv', 'Xear', 'Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot', 'Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle',
           'Xbfoot']:
    MIRROR[_a] = _a + '01'
    MIRROR[_a + '01'] = _a
UPPER_BODY_ROOT = 'Xback'
# role -> (MM9 clips, loop)
ROLES = {
    'Standing': (['Stand'], True),
    'Walking': (['Walk'], True),
    'Running': (['Run'], True),
    'Fidget': (['Fidget1'], False),
    'AttackMelee': (['HAttack1'], False),
    'Hit': (['Wince1'], False),
    'Death': (['Die1'], False),
}
# Jaw channel: MM9's bind jaw hangs open of its idle (Stand chews 33-17 deg closed of the bind by the Xjawpiv + Xjaw
# twist), the HD mouth is closed in the bind pose. a' = soft_max(0, (a + offset) * scale) on the MM9 keys: Stand chews
# 0-5.6 deg, HAttack1 reaches 17, the Run jaw 12-27.
JAW_FIX = {'bones': ['Xjawpiv', 'Xjaw'], 'apply': 'Xjaw', 'offset_deg': 26.0, 'scale': 0.6, 'soft_deg': 1.0}
# weight_refine.refine(): (root, child, chain index, kept past this axis fraction, within this radius)
REFINE = {
    'keep': [('Xflegpiv01', 'Xfleg01', 0, 0.7, 0.12), ('Xflegpiv', 'Xfleg', 1, 0.7, 0.12),
             ('Xblegpiv01', 'Xbleg01', 2, 1.0, 0.15), ('Xblegpiv', 'Xbleg', 3, 1.0, 0.15),
             ('Xtailpiv', 'Xtail', 4, 0.0, 9.0)],
    'keep_bones': ('Xhead', 'Xjawpiv', 'Xjaw', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01'),
    'mid': [(('Xflegpiv', 'Xflegpiv01'), 'Xback', (0.0, 0.15), (-9.0, 0.12)),
            (('Xblegpiv', 'Xblegpiv01'), 'XbackC', (0.0, 0.15), (0.12, 9.0))],
    'sigma': 0.06,
}
# weights_v2.py: limb bones (one side each), spine bone, z where the limb has no share left, z of the full share
LIMB_FADE = [(['Xblegpiv', 'Xbleg', 'Xblegpiv01', 'Xbleg01'], 'XbackC', 0.62, 0.34),
             (['Xflegpiv', 'Xflegpiv01'], 'Xback', 0.62, 0.36)]
TAIL_TUBE = {'bones': ['Xtailpiv', 'Xtail'], 'core': 'XbackC', 'tip_filter': 'y > 0.45 and abs(x) < 0.1',
             'tip_key': 'y', 'bin': 0.02, 'thin': 0.13, 'root_blend': 0.05}
BELLY = {'y': (-0.12, -0.04, 0.33, 0.42), 'core': 'XCENTER', 'bones': ['Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot', 'Xflegpiv01', 'Xfleg01', 'Xfankle01', 'Xffoot01', 'Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot', 'Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01']}
