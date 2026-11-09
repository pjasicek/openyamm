# Native motion and final source selection

Native MM6 lzd uses 1/16 s units: standing .125 s, walk .75 s, attack and attack2 .75 s with the same bow frames,
hit .75 s, death .625 s then held corpse, fidget .75 s. Source frames live in the read-only sibling `mm6_lzd/native/`.
Its hit filenames are `lzdwin*`, despite the descriptor's `lzdwnc` role alias; native corpse aliases use `lzddet*`.

G1 mannequin previews and ROM extraction preceded modelling; the selected rig retains those source rest frames.
Final source and adaptation:

| Role | Source and choice | Duration |
|---|---|---:|
| Standing | 2HandBowIdle, relaxed free arm, solved four-digit left grip | 2.0 s |
| Walking | 2HandBowWalk, relaxed right arm with knee clearance | .8 s |
| Running | RelaxRunForward, BowWalk arms; upright trunk | .8 s |
| Attack | 2HandBowAttack1, .3 s lead, 20% planted leg motion, equipped bow release | 1.1 s |
| Cast | Authored palm gesture from review round 2; low bow, small planted step, relaxed endpoints | 1.4 s |
| Hit | Authored native recoil, planted knee flex, torso/arm/bow response; source shrug rejected | .5 s |
| Death | 2HandBowDeath1, stable claw articulation, fitted tail and complete equipment floor support | 1.033333 s |
| Dead | Held final Death pose | 1.0 s |
| Fidget | Native stance adjustment and head scan, knees/arms/bow move | 1.0 s |

The original bow-set run was replaced by the upright Relax run after side review. Source GetHitF1 was reviewed but its
shrug was unsuitable for this broad reptilian head. A shorter authored Hit gives a clear recoil without shoulder/head
penetration. Clip durations intentionally preserve readable source motion rather than uniformly scaling native loops.

No paid animation and no Mixamo clip. Source finger rotation jumps were replaced by smooth fitted claw articulations;
wrapped twist angles are unwrapped before distributing them. The fitted animal has three fingers and an opposed thumb;
unused source digit chains remain unweighted.

The equipped GLB determines event time: forward string snap starts .733333 s, measured velocity peak .734375 s,
fully relaxed .766667 s. Use .734375 s for bow attack events, when arrow alignment to target is 0.9963. The earlier
source-only .766667 estimate is superseded. B's native fire arrow retains Attack. C's Lightning Bolt uses the distinct Cast clip, with the measured
forward palm release at .667708333 s through Socket_Palm_R. The hand gesture is authored from the review brief,
not inferred from an absent native hand-cast frame.
Bow/string/arrow contact, left grip and both hands were checked from the actual export; blade-edge gates are replaced
by the ranged draw/alignment/release measurements because this prop has no cutting blade.

Round 2 adds an all-clip signed elbow/forearm gate. Right-arm roll corrections preserve hand targets and remove
out-of-plane bending; distributed forearm twist is limited to 90°. See `review/cast_gate.json`.
