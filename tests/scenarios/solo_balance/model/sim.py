"""Pack fight simulator on top of the MAW model (gap.py): one solo character against N monsters that all attack.

Reports "HP used": the share of the character's maximum HP a pack takes from it before the last monster dies, with
no potions. Modifiers: P (damage), hp_mult and taken (max HP and damage-taken multipliers), aoe_targets/aoe_share
(extra monsters each swing hits, and their share), leech (share of damage dealt returned as HP), regen (share of max
HP healed per second), opener (damage-taken multiplier during the first opener_seconds: a defensive cooldown)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gap import *

def fight(name, Lm, tier, P=1.0, hp_mult=1.0, taken=1.0, aoe_targets=0, aoe_share=0.0, leech=0.0, regen=0.0,
          opener=1.0, opener_seconds=0.0, pack=None, buffs=None, step=0.02, hp_factor=1.0, dmg_factor=1.0, moncd=None,
          boss=False, free_seconds=0.0):
    m = Model.preset(name, 1)
    e = m.expected_char(Lm)
    hm, hc = HitsMon[m.d], HitsChar[m.d]
    N = pack if pack is not None else PACK[name]
    if tier == 'party5':
        rp, rv, health = 5.0, 5.0, e['health']; Lc = Lm
    else:
        p = tiers(m, Lm)[tier]
        b = p['buffs'] if buffs is None else buffs
        c = m.char(p['Lc'], skill=p['skill'], gear_level=Lm, geared=p['geared'], buffs=b, vs_level=Lm)
        rp = c['power']/e['power']; rv = c['vitality']/(e['vitality']/e.get('cover', 1)); health = c['health']; Lc = p['Lc']
    rp *= P; rv *= hp_mult/taken; health *= hp_mult
    dps = rp/(hm*SWING)/hp_factor    # B-monster HPs per second
    hit = dmg_factor/(hc*rv)         # share of max HP per monster attack
    cd = MONCD if moncd is None else moncd
    heal_scale = hm*e['power']*hp_factor/health  # one B-monster HP of damage dealt, in shares of max HP
    hps = [1.0]*int(N) + ([N-int(N)] if N > int(N) else [])
    w = [1.0]*len(hps)
    if boss:  # one monster is a boss: C level, HP x5 (MAW 2.5-7.5), damage x1.3 (1.2-1.4)
        hps[-1] = 5.0; w[-1] = 1.3
    t = 0.0; used = 0.0; peak = 0.0
    while hps and t < 900:
        mult = opener if t < opener_seconds else 1.0
        if t >= free_seconds:
            used += sum(w[:len(hps)])*hit/cd*step*mult
        dealt = dps*step
        total = min(dealt, hps[0]); hps[0] -= dealt
        for i in range(1, min(len(hps), 1+aoe_targets)):
            d = dealt*aoe_share; total += min(d, hps[i]); hps[i] -= d
        used = max(used - leech*total*heal_scale - regen*step, 0.0)
        peak = max(peak, used)
        keep = [i for i, h in enumerate(hps) if h > 1e-9]
        hps = [hps[i] for i in keep]; w = [w[i] for i in keep]
        t += step
    return dict(used=peak, ttk=t, rp=rp, rv=rv, Lc=Lc)
