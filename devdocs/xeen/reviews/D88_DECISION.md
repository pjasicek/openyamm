# D-88: X2's XD-06 exit — ranged disablers at the Temple of Yak (2026-11-21, fourth orchestrator's decider)

**DECISION: (b) with one change.** Move the four dark-end sprite markers (17, 22, 20, 21) out of both the exit's circles and Danulf's circle. Keep the five placed Killer Sprites at the temple front (`pop:temple_wisps`, group 63), and exempt them by name, not with the whole `xd06` waiver. Option (c) is rejected.

**WHY**
- **The A3 harm was the markers, not the temple.** The run log for reload 23 has been overwritten, so I worked this out from the monster kinds. The harm was Petrify. Nothing inside XD-06 can cause it: Cultists A–C do damage, the Yak Master's Curse is melee, Skeleton Lords curse and Ghouls paralyse in melee, Zombies diseasе. The placed guards are all Killer Sprites (11531), which Curse. In this area only a Medusa Sprite, a possible roll of the Xeen Sprite slot on the markers, casts Stone. Segment 23 clears 3,000 round the door before going in. That reaches the guards and marker 17 (about 2,800 from the door pose) but not 22, 20 or 21 (about 3,600–4,800). So the Petrify came from marker sprites near the temple door. I can't tell from the evidence whether it happened going in or coming out.
- **Placed actors and markers behave alike over time.** Neither comes back on a later visit within X2's 672-day refill. At refill the markers roll new monsters. Placed actors without `respawns_on_refill` keep their saved state (`keepActorsThroughRefill`), so dead guards stay dead even then. The difference is which ones the party is sure to have fought:
  - **The guards (873–2,885 from the exit):** entering XD-06 means standing at its only door with the Yak Stone, inside their range. The party has fought them, or chose to run past them, and comes out of the same door it went in. That is the "already faced" case D-87 was not written for. Keeping them keeps the temple set piece.
  - **The markers (2,304–4,766):** they are spread across the dark end, and the party may never have met them. X2 stays as it was while the party is in the dungeon, so a group that saw the party at the door waits there. That is the same pattern A3 recorded for D2's edge roads, and it is the harm D-87 is meant to stop.
- **The party does realistically leave right after the guards.** Segment 23 places the party at the exit, waits about 1 s, then sets its pose at Pray N Pay. A real player walks out with the guards dead, so only the markers matter there.
- **Cost:** moving four markers changes no count, slot or group size, so XP and Act II balance stay the same. The dark end keeps its sprites at the temple front. The south corners keep the sprites in the woods.

**WHO ACTS**
- **A5 (X2 `gen.py`):**
  - Move the markers: spawn 17 (-2080, -15360) to about (-6656, -14848); spawn 20 (-4800, -17280) to about (-7168, -17408); spawn 21 (3424, -16128) to about (5120, -16384); spawn 22 (448, -14656) to about (2560, -12288). Use the nearest dry cell that meets D-14.
  - Each new spot must be at least 5,888 from both exit points ((-1024, -17408) and (-1024, -17840)) and from Danulf (-3686, -9523). My figures are about 6,100–8,600.
  - Keep D-85's checks: the nest guards stay within about 1,800 of the nest, and the fork-to-ring road passes at most one group. Watch that 22's new spot does not crowd spawns 8 and 9 into one large pack.
  - Narrow the waiver in `vw.sh` from `--kept xd06` to the placed group-63 actors only, so a marker can never drift back in unnoticed.
  - Rebuild with bake and install. Run walk and hostility 2/2, `playtest_danulf_ring.yml` and the audit. Add one line to the NOTES: "D-88: temple guards kept (passed on entry), dark-end markers moved."
- **A2:** no recount. Rerun `balance.py` on the rebuilt X2, confirm Act II stays at 1.08, and confirm X2's marker count, slots and group sizes are unchanged.
- **A3:** rerun 23 and 17 in both normal and `--reload`.
  - Keep 23's Pray N Pay heal: it costs nothing.
  - Change the README's D-82 row: the cause becomes "X2's dark-end Medusa Sprite markers at the XD-06 door (moved by D-88)", not the inside of the temple.
- **A3-side:** rerun `q-c12_mirabeths_elixir.yml` (it uses the same door), `q-c17_faery_wand.yml` (nest step) and `q-c19_ligonos_skull.yml` (the south-east rim now has a group about 5,000 west of its old spot).
- **A3-promo:** rerun promotion 03 (Danulf's ring) once.

**REVERSIBLE:** yes. It is four marker coordinates in `gen.py` and a narrower waiver, then a rebuild.

**SUMMARY ROW**

| D-88 | 2026-11-21 | X2 XD-06 exit: ranged disablers at the Temple of Yak | The five placed Killer Sprites at the temple front stay (the only way in is that door, so the party faces them going in, and dead placed actors never return); the four dark-end sprite markers 17, 22, 20 and 21 move to the woods' south corners, at least 5,888 from both exit points and from Danulf, counts and slots unchanged. Reload 23's Petrify came from those markers' Medusa Sprites, not from the temple. | A5 (X2 `gen.py` four markers, waiver narrowed to group 63, rebuild with bake and tests), A2 (balance rerun, counts unchanged), A3 (23 and 17 both modes, D-82 row text), A3-side (q-c12, q-c17, q-c19), A3-promo (03) |
