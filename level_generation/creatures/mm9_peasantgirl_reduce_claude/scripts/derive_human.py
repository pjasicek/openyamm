#!/usr/bin/env python3
"""The human candidate's index buffers from the elf cut (family rule: one cut of the shared body, variants re-derived from it):
body = the elf body triangles under the human material name PeasantGirl_G2 (the body primitives are byte-identical in the two
installed GLBs); head = the elf head triangles minus the ear faces (any corner beyond the human head's vertex count: the human
head's vertices are the elf head's first NH vertices with the same attributes and its faces the elf faces without the ears).
Verifies those identities on the installed files first. Usage: derive_human.py <elf mp npz> <human mp npz>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, Hh = glbio.load(HERE / 'before' / 'mm9_peasantgirl.glb', 'PeasantGirl')
_, _, _, He = glbio.load(HERE / 'before' / 'mm9_peasantgirl1e.glb', 'PeasantGirl')
for k in ('P', 'UV', 'N', 'J', 'W', 'T'):
    assert np.array_equal(Hh['PeasantGirl_G2'][k], He['PeasantGirl_G1E'][k]), ('body', k)
NH = len(Hh['PeasantGirlHead']['P'])
for k in ('P', 'UV', 'N', 'J', 'W'):
    assert np.array_equal(Hh['PeasantGirlHead'][k], He['PeasantGirlHead'][k][:NH]), ('head', k)
Te = He['PeasantGirlHead']['T']; ear = (Te >= NH).any(1); assert not ((Te >= NH).any(1) & (Te < NH).any(1)).any()
assert np.array_equal(Hh['PeasantGirlHead']['T'], Te[~ear])
d = np.load(sys.argv[1]); body = d['PeasantGirl_G1E']; head = d['PeasantGirlHead']
hm = (head >= NH).any(1); assert not ((head >= NH).any(1) & (head < NH).any(1)).any()
ears_in = {tuple(t) for t in Te[ear]}; ears_out = {tuple(t) for t in head[hm]}
assert ears_in == ears_out, 'the ears changed in the cut'
np.savez(sys.argv[2], PeasantGirl_G2=body, PeasantGirlHead=head[~hm])
print('DERIVED human: body', len(body), 'head', int((~hm).sum()), '(elf head', len(head), ', ears', int(hm.sum()), 'kept exactly)',
      'LOD0', len(body) + int((~hm).sum()))
