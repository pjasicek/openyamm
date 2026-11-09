"""MM9 EVILEYETERROR.abc bone chains shared by fit_eye.py and rig_body.py (order = 'chain' attribute index).
Legs: eight 6-bone chains hanging under Box01 (last bone is a vertex-less tip). Stalks: five eyestalks; the last
listed bone carries the stalk's eyeball (target end of the stalk = that bone's head)."""
LEGS = [
    ['Box37', 'Box38', 'Box39', 'Box40', 'Box41', 'Box58'],
    ['Box29', 'Box30', 'Box31', 'Box32', 'Box59'],
    ['Box28', 'Box25', 'Box26', 'Box27', 'Box60'],
    ['Box15', 'Box22', 'Box23', 'Box24', 'Box61'],
    ['Box33', 'Box34', 'Box35', 'Box36', 'Box75'],
    ['Box42', 'Box43', 'Box44', 'Box45', 'Box46', 'Box64'],
    ['Box48', 'Box49', 'Box50', 'Box51', 'Box73'],
    ['Box52', 'Box53', 'Box54', 'Box55', 'Box74'],
]
STALKS = [
    ['Box07', 'Box08', 'Box09', 'Box10'],
    ['Box03', 'Box04', 'Box05', 'Box06'],
    ['Box11', 'Box12', 'Box13', 'Box14'],
    ['Box19', 'Box47'],
    ['Box56', 'Box57'],
]
CHAINS = LEGS + STALKS
CORE = ['Box01', 'Box02', 'Box72']
JAW = {'Box02', 'Box72'}
# MM9's eyelid (Box70) vertices are relabelled Box01: our eye socket is part of the body shell, so it must not blink
RELABEL = {'Box70': 'Box01', 'Box71': 'Box01'}
