# Dual wielding for the solo run's first-person arms (2026-11-14)

A melee weapon in each hand: both drawn, each attack led by one hand in turn, a cross slash of both blades to close a
round. Engine side and rules: devdocs/solo_action/WEAPONS.md "Dual wielding (2026-11-14)".

The arms are Oblivion's (reference/oblivion_poc/README.md): private, never committed. Only this README and `scripts/`
are tracked; `ingame/` is git-ignored by the level_generation rules.

## Baked clips

`scripts/bake_dual_clips.py <in.glb> <in.textkeys.json> <out.glb> <out.textkeys.json>` (numpy only, about 6 s) appends
22 clips and one node to an arms GLB; every existing clip, mesh, skin and texture is copied byte for byte. It refuses
input that already holds dual clips, so always bake from the pristine copies kept in
`reference/oblivion_poc/glb/pristine_predual/` (all ten races, as of 2026-11-14 00:43). The output is written in place
into `reference/oblivion_poc/glb/arms_hd_<race>.glb`; since 2026-11-14 the engine's arms are installed from there with
`tools/install_model.py --view-model --name arms.glb` (`../crossbow_set_20261114/scripts/rebake_arms.sh` does it), no
longer shared with `assets_dev` as a hard link.

```sh
P=reference/oblivion_poc/glb/pristine_predual; S=level_generation/props/items_claude/dual_wield_20261114/scripts
python3 $S/bake_dual_clips.py $P/arms_hd_human.glb $P/arms_hd_human.textkeys.json \
    assets_dev/engine/view_model/arms.glb assets_dev/engine/view_model/arms.textkeys.json
for r in darkelf dwarf elf goblin minotaur troll undead vampire zombie; do
  python3 $S/bake_dual_clips.py $P/arms_hd_$r.glb $P/arms_hd_$r.textkeys.json \
      reference/oblivion_poc/glb/arms_hd_$r.glb reference/oblivion_poc/glb/arms_hd_$r.textkeys.json
done
```

Done for human (the engine's arms) and all nine other races (same skeleton; rest symmetry 0.0002 units in each).

How a clip is made: the right arm (`Bip01 R Clavicle` and below), the left arm and the body (spine, neck, Camera01)
each take their pose from one source; a source is a clip, or its mirror (each bone takes its partner's world transform
reflected across glTF X = 0, corrected by the rest frames so the rest pose maps onto itself).

- **Eye-relative arms.** The attack clips twist the spine far round while the engine's eye follows only Camera01's
  position (it always looks straight ahead). Locals of an idle arm on an attacking spine put the waiting hand behind
  the eye (first bake, `dualattackright` at the Hit: left wrist at z +13.5, out of view). Each arm's clavicle is
  therefore solved so the arm keeps its own source's place relative to the eye.
- **Settling.** A cutting arm blends from its clip into its raised guard from 0.06 s after the Hit to the clip's end.
  Without that, Oblivion's follow-through carries it across the waiting arm. A tried alternative, turning the waiting
  arm outward and down about its shoulder, bought little clearance and took the waiting hand off screen (wrist at
  NDC -2.6, -4.9), so it was dropped.
- **OffHandWeapon** under `Bip01 L Hand`: the `Weapon` node mirrored with its flat axis (Z) turned over, so the
  off-hand weapon is a rotated copy of a right-hand placement, never a reflected one (no inside-out winding). Templates
  and our held.yml grips work unchanged in either hand.

| Clip | Right arm | Left arm | Body | Keys |
|---|---|---|---|---|
| `dualidle`, `dualforward` ... `dualfastright`, `dualblockidle`, `dualblockhit` | onehand clip | its mirror (sideways steps: the opposite step's mirror) | mean | the source's |
| `dualequip`, `dualunequip` | onehand clip | its mirror 0.25 s later | mean | Attach/Detach of the right |
| `dualattackright`, `_chop` | `onehandattackright[_chop]`, settling | mirrored idle | the cut's | Hit, a:L |
| `dualattackleft`, `_chop` | idle | mirrored cut, settling | the mirrored cut's | Hit, a:R |
| `dualattackleftpower` / `dualattackrightpower` | `onehandattackleftpower` / idle | mirrored idle / its mirror | the leading arm's | the source's |
| `dualattackforwardpower` | `onehandattackforwardpower` (lunge) | mirrored idle | lunge | the source's |
| `dualattackbackpower` | idle | mirrored `onehandattackbackpower` | its | the source's |
| `dualattackpower` (cross slash) | `onehandattackright` | its mirror 0.1 s later | mean | Hit at the right blade's (0.333 s), no chain |

Both hands doing the lunge or the step-back cut met in the middle (blades through each other), so those are led by one
hand. The backhand cuts (`onehandattackleft`) are not mirrored: in the dual combo each hand leads with a forehand.

## Gates

`scripts/clearance.py <arms.glb> [blade length]`: per dual clip, the closest approach between the blades and between
each blade and the other forearm, and how far each wrist goes on screen (the engine's projection, checked against
`viewmodel path`). Human, final bake:

| Clip | Closest | Waiting wrist on screen |
|---|---|---|
| `dualidle` | 22.0 | x 0.64, y -1.27 (both) |
| `dualattackright` / `left` | 0.1 at 0.59 s, out of view (the cutting arm settling past the far side) | x 0.65, y -1.29 |
| `dualattackright_chop` / `left_chop` | 6.4 | x 0.65, y -1.29 |
| `dualattackleftpower` / `rightpower` | 6.6 | x 0.65, y -1.28 |
| `dualattackpower` | 1.9 (forearms crossing) | — |
| `dualblockidle`, `dualblockhit` | 0.0 (the crossed guard) | x 0.59, y -0.76 |
| `dualequip` | 0.0 at 0.18 s, before Attach (weapons hidden) | — |

## In-game checks

`scripts/run_ingame.sh <pair> <outdoor|indoor> [tag]`: MAW solo run, 1600x900, `viewmodel equip` gives the new knight
both weapons (the real kit path), then idle and the held poses `dualattackright 0.30`, `dualattackleft 0.30`,
`dualattackpower 0.40`. Outdoors oute3 at the start; indoors 6d05 from the entrance looking into the cave. Pairs:
`sword` (Iron Longsword + Templar's Sword: low and high tier skins), `daggersword` (Dark Elven Longsword + Crystal
Dagger), `axe` (Battleaxe + Battle Hatchet), `mace` (Sturdy Mace + Temple Mace), `minotaur` (two battle axe templates
by `viewmodel kit dual`: the stock knight wields a two-handed axe two-handed). Final captures: `ingame/final/`; the
settling check: `ingame/v4/sword_outdoor/`.

Live play (`viewmodel trace on`, Attack pressed seven times): dualattackright, dualattackleft, dualattackright (the
combo restarts after a second's pause), dualattackleft, dualattackright_chop ...; each blow released at the clip's Hit
(clip 0.345-0.351 s, Hit 0.333 s) at the recovery-fitted rate.

Verdict at full size: both grips right in every pair (the left hand closes on the hilt like the right), blades and axe
edges lead in the direction of the cut, the waiting weapon stays raised and in view, the cross slash crosses with two
trails, nothing reaches into the camera. The battle axes fill the top corners at idle (a Minotaur's are big). The axe
and mace templates read dark indoors (their inside-out winding, fixed separately).
