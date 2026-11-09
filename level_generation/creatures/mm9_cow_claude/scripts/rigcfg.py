"""MM9 COW.abc rig configuration shared by the project's scripts (fit, weights, reduction, UVs, gates).
+X is the cow's LEFT side (the MM9 '01' bones)."""
NAME = 'Cow'
CHAINS = {
    'leg_fl': ['Xflegpiv01', 'Xfleg01', 'Xfankle01', 'Xffoot01'],
    'leg_fr': ['Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot'],
    'leg_hl': ['Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01'],
    'leg_hr': ['Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot'],
    'tail': ['XtailA', 'XtailC', 'XtailD', 'XtailE', 'Xtail'],
}
BLEND = {'leg_fl': 0.14, 'leg_fr': 0.14, 'leg_hl': 0.16, 'leg_hr': 0.16, 'tail': 0.08}
TAIL_MAXDIST = 0.09        # tail region: within this distance of the MM9 tail chain (it hangs against the rump)
LEG_TOP = 0.1
HEAD_BONES = ['Xheadpiv', 'Xhead', 'Xjawpiv', 'Xearpiv', 'Xearpiv01']
SKULL = 'Xhead'            # upper head (muzzle) bone
JAW_BONES = ['Xjawpiv']
EAR_BONES = ['Xearpiv', 'Xearpiv01']
NECK_BONES = ['Xneckbase', 'Xneckpiv']
MIRROR = {}                # L/R bone pairs: name <-> name01
for _a in ['Xearpiv', 'Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot', 'Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot']:
    MIRROR[_a] = _a + '01'
    MIRROR[_a + '01'] = _a
UPPER_BODY_ROOT = 'Xback'
FIT_SKIP = ['tail']   # our tail hangs where MM9's does; the chain estimate on the thin tail is unreliable
# role -> (MM9 clips, loop); Tipover/Standup (cow tipping) have no role in the engine yet
ROLES = {
    'Standing': (['Stand'], True),
    'Walking': (['Walk'], True),
    'Running': (['Run'], True),
    'Fidget': (['Fidget1'], False),
    'Hit': (['Wince1'], False),
    'Death': (['Die1'], False),
}
# Jaw channel: the HD mouth is closed in the bind pose. a' = soft_max(0, (a + offset) * scale) on the MM9 keys.
JAW_FIX = {'bones': ['Xjawpiv'], 'apply': 'Xjawpiv', 'offset_deg': 0.0, 'scale': 1.0, 'soft_deg': 1.0}
# weight_refine.refine(): (root, child, chain index, kept past this axis fraction, within this radius)
REFINE = {
    'keep': [('Xflegpiv01', 'Xfleg01', 0, 0.7, 0.25), ('Xflegpiv', 'Xfleg', 1, 0.7, 0.25),
             ('Xblegpiv01', 'Xbleg01', 2, 1.0, 0.3), ('Xblegpiv', 'Xbleg', 3, 1.0, 0.3),
             ('XtailA', 'XtailC', 4, 0.0, 9.0)],
    'keep_bones': ('Xhead', 'Xjawpiv', 'Xearpiv', 'Xearpiv01'),
    'mid': [(('Xflegpiv', 'Xflegpiv01'), 'Xback', (0.0, 0.3), (-9.0, 0.3)),
            (('Xblegpiv', 'Xblegpiv01'), 'XbackC', (0.0, 0.3), (0.3, 9.0))],
    'sigma': 0.1,
}
# weights_v2.py: limb bones (one side each), spine bone, z where the limb has no share left, z of the full share
LIMB_FADE = [(['Xblegpiv', 'Xbleg', 'Xblegpiv01', 'Xbleg01'], 'XbackC', 1.0, 0.55),
             (['Xflegpiv', 'Xflegpiv01'], 'Xback', 1.05, 0.6)]
TAIL_TUBE = {'bones': ['Xtailbase', 'Xtailpiv', 'XtailA', 'XtailC', 'XtailD', 'XtailE', 'Xtail'], 'core': 'XbackC',
             'tip_filter': 'y > 1.0 and abs(x) < 0.1 and z > 0.3 and z < 1.0', 'tip_key': 'y - 0.3 * z', 'bin': 0.03, 'thin': 0.14,
             'root_blend': 0.12}
BELLY = {'y': (-0.14, 0.0, 0.66, 0.8), 'core': 'XCENTER', 'bones': ['Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot', 'Xflegpiv01', 'Xfleg01', 'Xfankle01', 'Xffoot01', 'Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot', 'Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01']}
