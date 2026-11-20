# MM9 held items and sockets (2026-11-10)

The items MM9's scripts put in actors' hands (`AttachProp`: a monk's hoe, broom, hammer or wash cloth, a miner's axe,
a smith's hammer and Kira's sword, a Honk's pamphlet) and Ercc's cup (a piece of MM9's `Props/Ercc.ABC`, which our
animated Ercc, drawn with the townsman body, lacks), as rigid models our actors carry on nodes, and MM9's attach
points (an ABC's Sockets section) carried onto our creature models as those nodes. A placement holds them through
its scene `held_items: [{model, node}]`; map scripts change them (`evt.AttachActorItem`, `evt.DetachActorItem`); a
routine's `items` steps put them down for a while. Engine and data side:
[MM9 ambient animation](../../../devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md) section 4, items 9 and 10.

No paid services, no Meshy, no Codex: every item is MM9's own mesh with its skin x4 (plain Lanczos, the MM9 props
rule).

## Scripts

```sh
cd level_generation/props/mm9_held_items_claude/scripts
python3 build_items.py              # export/mm9_item_*.glb
python3 add_sockets.py [model ...]  # export/<creature>.glb: the installed creature sources with Socket_<name> nodes
python3 grip_clips.py [model ...]   # export/<creature>.glb: a hand closed round its held item (after add_sockets)
for f in ../export/*.glb; do python3 ../../../../tools/install_model.py --world mm9 "$f"; done
python3 ../../../projects/mm9r_common/review_root.py   # relink output/mm9_rework/assets_dev to the new models
```

- `build_items.py`: each item posed at its own animation's first frame, MM9's x mirrored (triangles reversed to keep
  their fronts) at 1/40 (`heldlib.ITEM_SCALE`), origin at its model origin (LithTech attaches that at the socket). A
  piece cut from a creature model keeps its frame relative to the node it is weighted to (Ercc's cup: `cup01`).
  All nine pass `check_winding.py` (0 inverted closed parts). DWARFAXE.abc's pick lies about 23 MM9 units to the
  side of its origin in both its animations, so at the socket it floated a pick's length off the miner's fist
  (2026-11-11); `GRIP_ON_HANDLE` moves it across so its handle runs through the origin like the other items'.
- `add_sockets.py`: reads the installed source of each creature model and writes it again with `Socket_<name>`
  nodes. A socket is a frame relative to one node of MM9's skeleton. Our models are that skeleton mirrored on x at
  about 1/40, in rest poses and bone axes of their own, but they play MM9's animations: our bone's world rotation
  differs from MM9's (mirrored) by a constant turn, measured over clips both play (by name, else by pose signature,
  as `generate_mm9_monster_sounds.py` matches them). The socket keeps MM9's offset and turn relative to the bone,
  anchored at our bone; its node scale takes an item at 1/40 to the model's own scale (a rigid fit of our rest
  bones to MM9's bind pose). Rerunning starts from the installed sources and replaces sockets of the same name.

| Model | Sockets | Measured over | Spread (position, turn) |
|---|---|---|---|
| `mm9_monk` | `Socket_Hoe`, `Socket_Broom`, `Socket_Hammer`, `Socket_Cloth` (on `Bip01 R Hand`) | Hoe, Sweep, Wash | 0.8-1.9 cm, 4.2 degrees |
| `mm9_peasantdm1`, `mm9_peasantdm2` | `Socket_RHand1` (on `Bip01 R Finger1`) | Standing, Walking, Running | 0.2 cm, 2.0 degrees |
| `mm9_dwarf` | `Socket_RHand1` (on `RHand1`) | Standing, Walking, Running | 0, 2.4 degrees |
| `mm9_honkm`, `mm9_honkf` | `Socket_pamphlet` (on `Bip01 L Finger1`) | Standing, Walking, Running | 1.3 / 3.0 cm, 5.2 / 11.4 degrees |
| `mm9_peasantm2` | `Socket_Cup` (cup01's frame on `Bip01 R Hand`) | ercc01a | 1.5 cm, 6.2 degrees |
| `mm9_kira` | `Socket_Sheath` (on `Bip01 L Thigh`), `Socket_RHand1` (on `Rhand1`) | Sc2_Kira17, Sc2_KIRA16b, Standing | 0.003 / 0 units, 1.5 / 15 degrees |

- `grip_clips.py` (2026-11-11): our grafted five-finger hands follow MM9's mitten loosely, so a hand holding a piece
  of MM9's model stayed open round it (Ercc's goblet floated against an open palm). It closes the fifteen finger bones
  of one hand to a fixed grip (`CUP_GRIP`: a turn about each bone's +y, its flexion axis on the MPFB hands) in every
  clip that holds the item, moves the socket so the stem runs through the fist (`Socket_Cup` by (-2.5, -3.2, -3.6)
  cm in the hand's frame: the bowl over the index finger, the foot under the little finger) and adds pose clips MM9's
  prop model has of its own (`ercc_sitting`: Ercc.ABC's `sitting`, the cup at the chest = ercc01a's first frame,
  2.03 s still). `mm9_peasantm2`: ercc01a-c, ercc02, ercc_out, ercc_sitting; reads and writes the installed source,
  so run it after `add_sockets.py` when both are rerun. Checked in Blender close-ups and in the Sturmford tavern
  (`output/held_items_check/sturmfordcity/grip_front/`).

The townsman's `ercc01` clips were reworked in the arms (their hand turns up to 50 degrees from MM9's in `ercc01c`), so
the cup follows our hand as `ercc01a` relates it.

Each creature project's README notes the step (a rebuild installed from there drops the sockets).

## Checks

- `socket_check.py <creature.glb> <Socket> <item.glb> [--clips A,B] [--hand <node>]`: the item's nearest point to the
  hand over each clip, as a fraction of the skeleton's height (H), from the GLBs alone. Every installed pairing
  (2026-11-11): 0.02-0.08 H; the dwarf axe before its fix 0.62 H. `render_held.py` renders one in Blender (its
  bone-parented placement can be off; trust socket_check and the game).
- Kira in the Argument, desktop captures (2026-11-11): the sword at her left hip on her walk, in her right hand
  from the draw, upright in the retort, by the hilt while she speaks.
- Lindisfarne Monastery, desktop captures (2026-11-10): the hoe monks hold their hoes in both hands at the ground,
  the broom monk holds the broom's handle, the wash monks' cloths lie on the washboards.

## Not done

- Items on a creature not listed here: add its ABC to `add_sockets.py` (`CREATURES`).
