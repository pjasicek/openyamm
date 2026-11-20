import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mawmodel import *
SWING=100/128*2.133333   # 1.667 s: one "power" attack at recovery 100
MONCD=80/128*2.133333*1.05  # 1.40 s: a melee monster's attack cycle at recovery 80
PACK={'nightmare':3.0,'madness':4.5}

def solo_skill(m, Lc, nskills):
    return m.skill_from_points(m.skill_points(Lc)/nskills)

def tiers(m, Lm):
    L5 = level_for_exp(5*exp_for_level(Lm)); L2 = level_for_exp(2*exp_for_level(Lm))
    gexp = m.geared(Lm)
    return {
      'parity': dict(Lc=Lm, skill=None, geared=gexp, buffs=None),
      'under':  dict(Lc=L2, skill=solo_skill(m, L2, 8), geared=0.6*gexp, buffs=frozenset()),
      'medium': dict(Lc=L5, skill=solo_skill(m, L5, 7), geared=min(m.geared(Lm, drop_mult=3), 0.95), buffs=frozenset()),
      'pimped': dict(Lc=L5, skill=solo_skill(m, L5, 6), geared=max(0.9, min(m.geared(Lm, drop_mult=5),1.0)), buffs=None),
    }

def evaluate(name, Lm):
    m = Model.preset(name, 1)
    e = m.expected_char(Lm)
    hm, hc = HitsMon[m.d], HitsChar[m.d]
    N = PACK[name]
    out = {}
    for t, p in tiers(m, Lm).items():
        c = m.char(p['Lc'], skill=p['skill'], gear_level=Lm, geared=p['geared'], buffs=p['buffs'], vs_level=Lm)
        # hit chance against the monster: MAW's par 0.75 (+Bless) is in power; a higher attack raises it (cap 1).
        rp = c['power']/e['power']; rv = c['vitality']/(e['vitality']/e.get('cover',1))
        swings = hm/rp; t_each = swings*SWING
        hits_to_die = hc*rv
        used = (t_each/MONCD)*N*(N+1)/2/hits_to_die
        out[t] = dict(Lc=p['Lc'], skill=c['skill'], geared=c['geared'], rp=rp, rv=rv, swings=swings, t_each=t_each,
                      ttk_pack=t_each*N, hits_to_die=hits_to_die, ttd_pack=hits_to_die*MONCD/N, used=used)
    # party of five expected members: five times the damage, hits spread over five
    t_each = hm*SWING/5
    out['party5'] = dict(Lc=Lm, rp=5, rv=1, swings=hm/5, t_each=t_each, ttk_pack=t_each*N, hits_to_die=hc,
                         ttd_pack=hc*5*MONCD/N, used=(t_each/MONCD)*N*(N+1)/2/hc/5, skill=e['skill'], geared=e['geared'])
    return out

if __name__ == '__main__':
    for name, levels in (('nightmare', (20, 50, 100, 150, 220)), ('madness', (25, 50, 100, 200, 300, 450))):
        print('=====', name)
        for Lm in levels:
            r = evaluate(name, Lm)
            for t in ('party5', 'parity', 'under', 'medium', 'pimped'):
                x = r[t]
                print(f"Lm {Lm:4} {t:7} Lc {x['Lc']:6.1f} skill {x['skill']:5.1f} geared {x['geared']:.2f} P x{x['rp']:5.2f} V x{x['rv']:5.2f} | swings/B {x['swings']:5.2f} TTK B {x['t_each']:5.1f}s pack {x['ttk_pack']:6.1f}s | hits to die {x['hits_to_die']:5.1f} TTD vs pack {x['ttd_pack']:5.1f}s | HP used by pack {x['used']*100:6.0f}%")
