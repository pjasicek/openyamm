# MM8 indoor exploration, visible sectors and actor activation

Investigated 2026-09-29 with Rizin against **`mm8_orig/MM8-Rel.exe`**, SHA-256
`5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b`.
The hash was checked again. This is the executable verified against the supplied GOG installer, not the
GrayFace-patched `mm8.exe`. Addresses below are virtual addresses in this executable. The investigation is
static; no executable bytes were changed and no original-game runtime experiment is claimed.

See the [Rizin guide](RIZIN_GUIDE.md), [annotations](mm8_rel_5326d564_indoor_activation.rz),
[actor audio](ACTOR_AUDIO.md) and [creature movement](CREATURE_MOVEMENT.md).
Local OpenEnroth supplied structural hints; conclusions below were checked against MM8 instructions.
No reference implementation was copied into OpenYAMM.

## Finding

**Current OpenYAMM policy (2026-09-30):** the user selected MM8-style discovery after the Castle Darkmoor
rotation profile exposed a large cost in the added strict exploration pass. Discovery now reuses the normal
portal render result; the extra wall/door subtraction pass and its API were removed. The two Goblinwatch
exploration fixes described below are historical, superseded experiments. Door collision, faction alerts,
actor detection and their optimizations are separate and remain in place. See the Darkmoor performance section
for the measured regression and correction.

**Current actor detection (2026-10-28, revised 2026-11-04):** monsters notice the party by sight, a neighbour's
alarm or damage, never by sector membership or by hearing through walls. See
[detection by sight, hearing and neighbours](#openyamm-detection-by-sight-hearing-and-neighbours-2026-10-28).

The subsequent [Goblinwatch entrance audit](#goblinwatch-entrance-parity-audit-2026-09-30) found additional
portal traversal differences. The [implemented follow-up](#mm8-portal-traversal-corrections-2026-09-30) removes
aperture enlargement and rejected-portal recovery, uses live door vertices, and restores the verified facing,
near-portal and projected-height gates. It retains OpenYAMM's floating-point renderer; its numerical limits
are recorded below. The available MM6 executable places the face-discovery write later than verified MM8,
so an MM6 minimap screenshot is not an exact specification of the selected MM8 policy.

There is **no shared persistent “visited sector activates its monsters” gate** in the traced original paths.
MM8 maintains separate state for rendering, automap discovery and actor scheduling:

| State | Owner and lifetime | Used for |
| --- | --- | --- |
| Sectors reached by portal rendering | Renderer; rebuilt for the current view | Selecting geometry, actors and decorations to draw |
| Seen face bit `0x80` and discovered outline bit `1` | Faces/outlines; stored in the indoor map delta | Minimap and map-book exploration |
| Active `0x4000`, Nearby `0x8000`, FullAI `0x400` | Each actor; different update/reset rules | Selecting actors for full AI |
| Disabled/Removed and other AI states | Each actor | Actual restrictions on simulation; also controlled by events |

Consequently, a monster in an unexplored room can enter full AI, and an explored room can contain monsters
outside the full-AI list. Actors outside that list still receive background updates. “Inert until encountered”
describes some visible behavior, but does not mean the engine stops processing every actor in an unvisited room.

## 1. The renderer's sectors are temporary visibility state

The indoor render chain resolves a sector from the render position at `0x43e569–0x43e58c`, with a fallback
using party XY if that query fails. `0x43d61a` starts the face list afresh, initializes the first view node with
that sector and viewport, and invokes sector traversal. It does not consult automap exploration bits.

`0x43e3aa` enumerates a sector's non-BSP faces and, when sector flag `0x10` is present, traverses its BSP at
`0x43e42b`. This sector flag selects a geometry traversal path; it is not a visited/AI activation flag.
The two portal/face submission routines are `0x4b002a` for software and `0x4b137c` for Direct3D.
They use portal orientation, projection/clipping and the current view-node bounds to reach adjoining sectors.
There are special cases near a portal; this is not an unconditional flood through every connected room.
Nonportal faces are queued with their view-node IDs.

`0x43cfde` resets the visible-sector count and extracts unique sector IDs from this frame's view nodes.
The resulting globals are count `0x580568` and IDs `0x58056c`. The actor billboard builder at `0x43db2a`
uses this list to reject actors whose sector is absent (`0x43dcbf–0x43dce6`). This is a **drawing gate**.
The AI-list builder does not read this list.

The normal portal expansion branches compare the view-node count against 150, and nonportal submission
compares the face count against 1000. These are renderer limits, independent of the 30-actor AI list.
They should not be described as 150 permanently active rooms: nodes are views through portals, not unique rooms.

### Closed doors and render-sector selection (2026-09-30 follow-up)

Rechecked the same original executable with Rizin 0.10.0, including the portal-clipping helpers, while profiling
OpenYAMM's fresh Goblinwatch entrance. The original traversal is conservative about **opaque geometry**:

- `0x4b13a8–0x4b13b1` tests face attribute `1` (portal). An ordinary face takes the branch at
  `0x4b18e5–0x4b18fe`, which only appends its face ID and view-node ID to the draw queue. It does not subtract
  that wall or door from the portal aperture. Software submission has the same split at `0x4b004b` / `0x4b0405`.
- A portal rejects the entry portal, checks its orientation, projects/clips its polygon using `0x422778`,
  rejects screen bounds outside the parent view, and intersects its scanline window with the parent window
  through `0x42347e`. The parent window is a **portal window**, not accumulated opaque-face coverage:
  the helper intersects left/right bounds at `0x4237d4–0x4238db` and produces the child window.
- Direct3D additionally clips the portal polygon against the parent's four portal planes (`0x435648`,
  called at `0x4b1845`) and builds the child's portal bounds/planes through `0x49b92f` / `0x49b9d6`.
  The ordinary accepted branch then recurses at `0x4b18c7`, subject to the 150-node bound.
- The BSP routine `0x43e42b` orders its two children according to the camera's plane side; it visits both
  existing children around the node's faces. This is not a general wall/door occlusion test either.
- At the initial node, the near-portal special case uses a bounding-box margin of 16 units and an absolute
  plane-distance threshold of `0x90000` in fixed-point units. It can enter the adjoining sector with the full
  viewport, making this branch deliberately conservative near a portal.

There is no general closed-door-state query, solid-face raycast or explored-sector gate in this traced selection
chain. An ordinary opaque door can hide pixels without preventing the renderer from queuing the room behind it.
Authored portal placement/geometry and subsequent face rendering still matter; this is not a claim that every
closed room is selected, or that original MM8 produces OpenYAMM's exact sector count at a different aspect ratio.
This conclusion is from static code, not an original-game GPU capture.

OpenYAMM already caches its portal traversal while the camera and geometry remain unchanged. Reusing the saved
exploration set as a render mask would be incorrect. General solid-geometry occlusion would also go beyond the
original traversal and needs transparency/door-motion validation; it is not required for MM8 fidelity.

## 2. How indoor exploration is drawn and remembered

Indoor automap lines come from authored outline records, not from a fog grid of sector visits. The outline
block pointer is `0x6f3bc8`; it contains a count followed by 12-byte records. Each outline names two vertices,
two adjoining faces, a Z value and flags.

### Where a face becomes seen

The queued-face dispatcher at `0x43e896` invokes the software or Direct3D face renderer. The persistent
`SeenByParty` bit lives at face offset `0x2c`, mask `0x80`:

- Direct3D sets it at **`0x4b0fbf`**, after rejecting invalid indices, faces with fewer than three vertices and
  invisible faces, but before texture lookup and subsequent facing/clipping checks.
- The ordinary software face path sets it at **`0x4b04b3`**, after invisible/special-surface handling and a
  successful texture lookup, before projection/clipping later in the routine. Special sky/fluid branches
  have separate handling; this is not a claim that every special surface uses this exact write.

Thus “seen” is coarse render-processing history, **not proof that a face contributed a visible pixel**.
Faces submitted from a reached room can reveal its outline even when individual faces are later rejected.
It is also not necessary to step into every room: portal traversal can submit adjoining rooms' faces.

### Minimap and map book

The HUD minimap routine `0x43f7f4`, indoor branch `0x43f8cd–0x43fb36`, processes each outline:

1. Both adjoining faces must lack the Invisible flag `0x2000`.
2. Draw the outline if its discovered flag is already set, or either adjoining face has SeenByParty `0x80`.
3. On first discovery, set outline flag `1` and the corresponding packed discovery bit at `0x6f3c44`.
4. Project the outline's XY vertices around the party at the chosen map zoom. The ordinary line shade depends
   on `min(abs(outlineZ - partyZ) / 8, 100)`, with palette index `200 - that value`.

The discovery write is `0x43f93f–0x43f95e`. Bit packing is most-significant-bit first:
byte `i / 8`, mask `1 << (7 - i % 8)`. The map-book routine `0x440450` repeats the same discovery conditions
and writes the same bit array at `0x4405c0–0x4405e6`.

Wizard Eye's clickable/event outline coloring is a later branch of the minimap logic. It is not the condition
that makes ordinary geometry explored, nor an AI activation operation.

Wizard Eye's actor markers are separate from those outlines. The loop at `0x440108` skips Removed (11)
and Disabled (19), then admits Dead (5) actors or actors with **Nearby `0x8000`**. The bit test is
`0x44012b`: the pointer is actor `+0xb8`, and byte `[pointer-0x93] & 0x80` is attributes byte `+0x25`.
It projects actor XY and clips to the minimap; this branch does not require an explored sector, a currently
visible billboard, or the party's floor height. Hostile `0x1000000` selects the hostile color at `0x4401b7`.

### Persistence

Indoor delta serialization copies **875 bytes** of outline discovery (`0x45ea65–0x45ea74`), followed by the
32-bit attributes of each face (`0x45ea8f–0x45eab8`). That is storage for 7000 outline bits, not 7000 sector bits.
Loading copies the outline bits back at `0x4999fa–0x499a33`, restores individual outline flag `1` from them
at `0x499a4d–0x499a97`, and restores face attributes at `0x499aac–0x499b19`.
These records preserve discovery across ordinary saves/revisits; map refill/reset behavior is a separate concern.

Actor records are serialized separately, using stride `0x3cc` (`0x45eaf2–0x45eb06`, `0x499b79–0x499b8e`).
They do not derive their activation flags from the outline bitmap on load.

### Save/load: discovery, encounter memory and temporary caches

The ordinary save/load path preserves discovery and actor encounter memory, while the renderer and AI
scheduler rebuild their current working lists. These are distinct even when their bits happen to be stored
in the same serialized actor record:

| State | Saved/restored? | First normal use after loading |
| --- | --- | --- |
| Current renderer-visible sectors and portal view nodes | No persistent discovery record for this list | Rebuilt from the current camera and geometry |
| Face SeenByParty and discovered outlines | Yes, in the indoor `.dlv` map delta | Previously discovered geometry remains on the automap |
| Actor Nearby `0x8000` | Yes, in the actor attributes | Retained; can bypass a fresh detection check during AI selection |
| Actor Active `0x4000` | Yes, in the actor attributes | Still subject to the ordinary range/CanAct clearing and same-sector selection rules |
| Actor FullAI `0x400` | Its bit is included in the raw record | Cleared and selected again by the next indoor AI-list build |
| Actor Visible `0x8` | Its bit is included in the raw record | Cleared and set again by the next actor-billboard build |

Evidence for the save/load distinction:

- Save routine `0x45e3d2` writes the actor count at `0x45eae6–0x45eaed`, then copies
  `actorCount * 0x3cc` bytes directly from `0x61c458` at `0x45eaf2–0x45eb06`. This includes all actors,
  not just visible or full-AI actors. There is no activation-bit mask at serialization.
- Indoor loader `0x498050` restores the count at `0x499b5f–0x499b67` and copies the entire actor array
  back at `0x499b79–0x499b8e`. The record includes attributes at `+0x24`, current HP at `+0x28`,
  position at `+0x96`, sector at `+0xa6` and AI state at `+0xb8`.
- Load-game routine `0x45ddb0` sets global flag `0x2000` at `0x45e320` (the instruction ORs `0x2001`
  into `0x6f38bc`). Indoor setup tests it at `0x45fa3e`: when set, it skips actor initialization
  `0x40928c` and sprite-object initialization `0x40933c`, then consumes the flag at `0x45fa51`.
  Thus an ordinary save reload does not perform the map-entry reset of eligible actors to home positions,
  restored HP and standing actions. The indoor loader also uses this flag at `0x499874–0x49987d` to
  extend the refill interval to `0x1baf800`, suppressing an ordinary timed refill during save loading.
- The following actor setup at `0x45fd63–0x45fde1` prepares sprites and handles disabled/zero-HP states;
  it does not clear Nearby or Active. Sprite preparation `0x45830d` also leaves these flags intact.
- Indoor selection clears FullAI at `0x401776`; it can clear Active at `0x401828` but retains Nearby,
  which is tested at `0x40194c`. The saved FullAI bit does not preserve membership of the old working list.
- Indoor billboard construction clears Visible at `0x43db53` and sets it when submitting an actor
  at `0x43dd7e`. This bit is current drawing eligibility, not permanent “the player has seen this monster.”

Loading an earlier save **replaces** discovery and actor flags with that save's data; it does not merge
the current session's later discoveries into them. Outline restoration explicitly sets or clears flag `1`,
and face attributes and actor records are copied from the loaded delta. A corridor already recorded in a
save therefore stays explored after reloading, even if its door is now shut. A renderer cache from another
view is not the persistence mechanism.

Leaving and re-entering a map is different from loading a save: without the skip-reset flag, indoor setup
calls `0x40928c`. That routine resets eligible actors' home position/HP/action and clears other state, but
its attribute masks at `0x409304` and `0x409308` clear `0x80000` and `0x800000`, **not Nearby**.
Map refill, authored events and explicit actor replacement are separate cases; this finding does not claim
that encounter state survives those operations.

### Faction alerts do not themselves grant encounter memory

Original MM8 routine **`0x439278`** propagates aggression to nearby matching actors. Party damage calls
it after killing (`0x438101`) or stunning (`0x438174`) the victim, with the aggression argument set to 1.
It scans actors that CanAct, excludes the victim, checks the faction helper `0x4391ca`, skips actors whose
Ally field (`+0x350`) is 9999 when aggression is 1 (`0x4392e8`), then requires approximate 3D distance
**strictly below 4096**. The comparison at `0x439345` uses float constant `4096.0` at `0x4ea5f0`.

The faction helper `0x4391ca` takes each actor's class from its Ally field (`+0x350`) or, when that is zero,
`(monsterId - 1) / 3 + 1` (`0x4391cc–0x4391fe`), the column of `hostile.txt`. The two actors match when
both classes are equal (`0x43926d–0x439271`) or both are 7–8, the Dark Elf peasants (`0x43920e–0x439220`);
the other constant comparisons between `0x4391ff` and `0x439267` only repeat equality. Event groups and class names play no part.

The alert has no line-of-sight or explored-sector test, but its writes are limited:

- Set the other actor's hostility type at `+0x3d` to 4 (`0x439354`).
- When the aggression argument is 1, set Aggressor `0x80000` (`0x43935a`); the victim gets that bit
  separately at `0x439298`.
- It does **not** set Nearby `0x8000`, Active `0x4000` or FullAI `0x400`.

Therefore “a nearby ally was attacked” and “this actor has detected/encountered the party” are different
state changes. Ordinary indoor selection still determines whether the alerted actor receives full AI.

**OpenYAMM alert rule (2026-10-28), indoors and outdoors.** Allies are matched by MM8's class rule
(`MonsterTable::sharesAlertFaction`, after a world's `relations.yml` add-on), not by event group or by the first
word of the class name as before. The old rules let a gog hit in Nighon Tunnels rouse the dwarves of its spawn
group, let the Misty Islands Assassin (`PeasantF3`) rouse the `PeasantF1`/`PeasantF2` villagers, and let any
hostile dragon struck in Garrote Gorge rouse the Dragon Hunters (all "Dragon ..."). Actors fighting for the
party are skipped. OpenYAMM keeps its rule that peasants and guard groups 38/55 alert one another.

One deliberate deviation: a victim **hostile on its own** (by its map, its monster template or an event) alerts no
friendly actor; indoors it still marks hostile allies Aggressor with hostility type 4. MM8 has no such test, so
striking a raiding warlock of Mount Nighon's hostile group 56 near town would turn the friendly town warlocks of the
same class. A victim the party made hostile (it was struck while friendly, or alerted by such a strike) keeps
rallying its class, so the alert still spreads from villager to villager; the runtimes remember this as
`angeredByParty`, saved since save version 138 (older saves load it as false). Striking a friendly actor rouses its
whole class as in MM8. Scenarios `mm6/mist_faction_alerts.yml`,
`mm7/nighon_tunnels_faction_alerts.yml`, `mm7/mount_nighon_faction_alerts.yml` and
`mm8_garrote_gorge_faction_alerts.yml` cover these maps; each fails with the previous rule.

## 3. Full AI is selected per actor

`0x40172e` constructs the indoor list used by `0x401ad8`. Actors live at `0x61c458`, stride `0x3cc`;
attributes are at actor offset `0x24`, sector ID at `0xa6`. The selection proceeds as follows:

1. Resolve the party's current sector from its **feet**, using `RoomFromPoint` at `0x401755`.
2. Clear FullAI `0x400` on every actor. Require `CanAct` (`0x4093f1`) for candidates.
3. Compute the approximate 3D feet-to-feet distance, subtract the actor radius and clamp to zero.
   Candidates must be **strictly below 10,240**. For sorted absolute coordinate deltas `a >= b >= c`,
   the integer approximation is `a + (11*b >> 5) + (c >> 2)`. Ineligible/out-of-range actors lose Active
   `0x4000` at `0x401828`; this pass does not clear Nearby `0x8000`.
4. Sort candidates by distance. Accept a candidate if Nearby is already set, or the actor-to-party detection
   helper succeeds. Set Nearby on acceptance. Stop this first pass after 30 accepted actors
   (`0x401937–0x401994`).
5. Scan all actors again. Append actors that can act and share the party's current sector, unless already
   selected; set Active on these additions (`0x4019ab–0x4019fd`). This pass has no distance test of its own.
6. Append remaining in-range candidates with **either** Active or Nearby (`0x401a18–0x401a71`).
7. Retain the first **30 total** and mark only those FullAI (`0x401a78–0x401ad1`).

The flags are not synonyms. Active can be set on a same-sector actor that loses out to the final cap.
Nearby avoids repeating detection on subsequent selections. The eligible real-time full-AI update itself also
sets Nearby at `0x4020de–0x4020ec`, so that bit is not exclusively proof of a successful visual ray test.
These are encounter/scheduling flags, not a record that the player saw an actor on screen.

This explains the apparent awakening after entering a room: same-sector membership offers a route into full AI,
and processed actors acquire cached Nearby state. After leaving, they can continue to qualify while in range
even without a fresh portal detection result. Range, ability to act and the list cap still matter.
This is not a guarantee of perpetual combat or of every previously encountered actor updating every tick.

### What detection actually checks

The helper is **`0x407be3`**. For an actor versus party, it uses actor XY and approximately 70% of actor height,
and party XY plus party eye height. The actor supplies its stored sector; the party endpoint's sector is
resolved from that eye position (`0x407cf3–0x407d15`).

- Distance is a separate 3D square-root distance, rejected only when **greater than 5120**
  (`0x407d92–0x407dc6`). This is not the 10,240 approximate candidate distance.
- After that range check, equal endpoint sectors succeed (`0x407e4c–0x407e4f`).
- For different indoor sectors, it traces the actor-to-target ray across the current sector's authored portal
  faces: facing/sign and bounding-box tests, plane intersection, then point-in-polygon (`0x4080d8`).
- It switches to the portal's opposite sector, allowing at most **30 transitions**. Reaching the target sector
  succeeds; failing to find a crossing or exhausting the bound fails (`0x407e55–0x4080d3`).

There is **no camera yaw/FOV, renderer-visible-sector list, SeenByParty bit or explored-outline test** here.
It is a portal connectivity test along a ray, not a general route search or a ray cast against every solid face.
In particular it does not separately consult door state or test nonportal door/wall faces. Whether a particular
closed doorway prevents this detection can depend on its authored portal geometry and how that geometry moves.
Do not infer a universal “closed door makes the room inactive” rule from this helper.

## 4. What non-selected monsters still do

In real time, `0x401c9a–0x401eb9` scans the **entire actor array**, independently of the full-AI list:

- Skip Dead (5), Removed (11), Disabled (19), and actors marked FullAI.
- Process zero HP/death, buff expiry and the background recovery/action timers.
- Paralysis/petrification prevent ordinary action advancement.
- On action expiry, finish dying/summoning states or call StandOrBored (`0x401e9d`). That path can fidget
  and request actor audio, including from an unexplored sector.

These actors are not running the full target-selection/combat/wandering decision loop. They can therefore
appear to wait in place. However, fidgets and voices do not require a previous encounter or a visited room.
The ordinary sound mixer's 8192-unit cutoff remains independent; see [actor audio](ACTOR_AUDIO.md).

Physics is also separate: `0x46fb6d` iterates the full actor array, skipping Removed, Disabled, Summoned and
zero-movement-speed cases at entry, then applying floor, motion and collision rules. It has no explored-sector
or FullAI entry gate. An existing movement action can continue before the background scheduler changes it to
standing/bored. Actor-to-actor collision candidates use the selected actor list (`0x470063–0x47011b`), so this
does not mean every actor checks every other actor. See [creature movement](CREATURE_MOVEMENT.md).

Disabled/Removed actors are a different case: these states really exclude ordinary processing. Events and
load/setup can impose them. They must not be confused with an ordinary actor simply missing the current
30-entry list. `CanAct` also excludes Dying, Dead, Summoned, paralysis and petrification.

Turn-based mode branches to its own scheduler at `0x401c82–0x401c95`, before the real-time background loop.
The all-actor background behavior above is specifically a real-time finding.

## 5. Comparison with current OpenYAMM

The following snapshot was checked on 2026-09-29 after the actor-audio fixes, before the exploration correction below.
The binary research itself did not change runtime behavior.

- `IndoorWorldRuntime::selectIndoorActiveActors` follows the detected/same-sector/cached selection structure.
  Its detection helper already uses the 5120 range and a portal traversal. Its candidate distance is floating-point
  target-height distance rather than MM8's integer approximate feet distance; its final cap is **48**, although
  its initial detected-actor pass stops at 30. These are separate fidelity differences from sector visitation.
- `collectIndoorActorAiFrameFacts` routes other eligible actors through shared background AI without a visited
  sector prerequisite. That agrees with the central original scheduling/audio distinction.
- OpenYAMM nevertheless has a persistent `m_activatedIndoorSectorMask`. `refreshActivatedIndoorSectors`
  marks the party's feet and eye sectors. That mask still excludes actors from
  `collectMapActorIndicesWithinRadius`, `actorMovementCollidersForActorMovement`, and
  `actorMovementCollidersForPartyMovement`. The original AI/physics/exploration chains above do not justify
  treating this party-visited mask as a general simulation eligibility rule.
- Before the correction below, OpenYAMM exploration marked faces belonging to `visibleIndoorMapRevealSectorIds`, including entire
  supplied sectors, with an additional closed-door bounds heuristic in the renderer. The original writes SeenByParty
  during the individual face-render paths. Both can reveal more than visible pixels, but their exact conditions
  differ. OpenYAMM's reveal cache also keys on sector IDs and surface/topology revisions, rather than camera
  position/yaw; turning or moving within the same sector need not trigger its portal-reveal recalculation.

If revising this area, keep current render visibility, persistent automap discovery, actor encounter state and
explicit Disabled/Removed state distinct. In particular, do not make an audio fix depend on the automap or on
the party having physically entered a room. Any removal of the remaining OpenYAMM visitation gates should be
validated as a collision/spell behavior change, rather than hidden inside audio work.

### Goblinwatch exploration correction (superseded)

This historical implementation was removed after the Darkmoor profile and the user’s choice to restore MM8 discovery.

The reported fresh-MM6 Goblinwatch pose `(576, 6912, 192)`, yaw `4.663`, reproduced the detached eastern
corridor in a native desktop run. The scene's outline bitmap and geometry's SeenByParty bits both start empty.
The erroneous discovery came from runtime visibility handling:

- The old reveal filter inspected accepted render portals individually, so rejecting an intervening portal
  did not reject its descendants.
- Render traversal expands thin portal markers using shared sector bounds. Those conservative openings can
  extend behind solid walls and doors, making render-sector membership too permissive for permanent discovery.
- The reveal cache did not follow camera changes or each door-animation geometry update.

Exploration now uses the portal traversal with solid-geometry occlusion enabled and current, moved portal vertices.
Some MM8 doorway portals collapse to a line in their stored geometry and expand when the door opens.
Current door polygons and walls along the traversal path occlude openings before admitting another sector.
It combines covering faces,
allows partial openings and uses the existing portal clipping tolerance for door-fit seams. It does not infer
physical closure from mechanism endpoint names: Goblinwatch's initial zero-distance door pose is physically shut.
Only nonportal faces in admitted sectors become seen. The renderer's visibility revision invalidates the discovery
cache for camera position, direction, viewport and geometry changes.

This is an OpenYAMM correction to prevent unseen rooms leaking onto the map, not a claim that the original
binary performed this additional polygon occlusion pass. The original coarse face-history behavior above remains
the RE finding. Existing saved discovery is retained; the fix prevents new false discoveries without erasing
legitimately explored areas. Rendering and actor scheduling retain their separate eligibility rules.

Regression coverage is in `tests/IndoorPortalVisibilityTests.cpp`: the real Goblinwatch entrance in four directions,
its first opened door, blocked descendants, mechanism endpoint independence, double doors, partial openings,
hidden faces and doors beside or beyond an opening. The open Goblinwatch chest doorway and MM8 Necromancer's
Guild side-room doors also exercise the exploration path, in addition to their existing rendering checks.

### GW_3: activated actors beneath unexplored map geometry

The user-supplied `GW_3` is `saves/save19.oysav`, map `6d01.blv`. A read-only inspection using the engine's
save decoder found party position approximately `(1356.65, 4589.76, 0)`, sector 45. The red cluster in the
marked minimap area contains actors **110–115**: five Blood Suckers and one Brain Sucker. Their positions
are around X `1595–1671`, Y `3807–3845`, Z `-632`, in sector **24**. Several markers overlap.

All six have saved attributes **`0x0108c400`**: Hostile, Aggressor, Nearby, Active and FullAI. Their saved
`hasDetectedParty` values are true and their motion state is Pursuing. Thus these are already activated
actors in the save, not just an automap rendering artifact. A probe through the current engine's portal
detection helper, using the saved moved-door geometry and the runtime's 75%-actor-height / party-Z+96
endpoints, failed to leave sector 24 for all six. A fresh detection test at this pose does not activate them.

The previous OpenYAMM faction-alert path could produce this state:

1. `IndoorWorldRuntime::applyPartyAttackMeleeDamage` calls `aggroNearbyMapActorFaction`.
2. That helper scans living matching actors within 4096 units without a wall, floor, sector-visit or detection
   gate, then calls `setMapActorHostilityFromEvent(otherActorIndex, true)`.
3. The event-hostility setter also marks Active and FullAI and sets both runtime detection booleans to true.
4. Selection subsequently treats that detection boolean as cached detection and latches Nearby.
   Wizard Eye displays the hostile marker, independently of geometry discovery.

The original's radius alert itself is also independent of walls, but it does not perform step 3's detection
and activation writes. Reusing the event-hostility setter for faction alerts therefore activated actors
more broadly than original MM8. `GW_3` also contains a dead Blood Sucker (actor 199) near the party, which
is consistent with this mechanism; the save does not record the exact historical hit that first alerted
the group.

The indoor faction-alert path now sets hostility type 4, Aggressor and the runtime hostility values directly.
It preserves detection, action state and selection flags. Unseen allies still require normal detection;
previously encountered allies retain their encounter memory. The radius alert continues to ignore walls,
as in MM8. Explicit event hostility and direct damage retain their separate behavior. The outdoor alert
already leaves detection to its ordinary AI path and does not call the indoor event-hostility setter.

`tests/IndoorActorFactionRuntimeTests.cpp` exercises this through the real indoor runtime and Goblinwatch
geometry: surviving/killed victims, unseen lower-room allies, remembered allies, unrelated/out-of-range
actors, Wizard Eye, snapshot restore and a later encounter in the lower room. Build and run with:

```bash
cmake --build build --target openyamm_runtime_tests -j25
./build/tests/openyamm_runtime_tests --test-case='*indoor faction*'
```

This fix does not rewrite `GW_3` or erase encounter memory on load. Its six marked actors already have the
incorrect state serialized; clearing every actor that currently lacks detection would also erase legitimate
past encounters.

### Goblinwatch entrance walk: initial detection through solid walls

The follow-up reproduction starts at `(565.634, 6210.096, 0)`, opens the entrance door through event 1,
and walks to `(535.851, 4885.110, 0)`. This reproduces fresh activation without damage, faction alerts or
pre-existing encounter memory. Opening the entrance alone does not wake the goblins. During the walk,
two main-room goblins first detect the party near `(541, 5120, 0)`, before it reaches the corner.

The portal-only detector accepts the chain **4 -> 3 -> 2**, crossing portal faces **116** and **1967**.
The same ray also intersects solid faces **1586, 1587, 1596 and 50**, among others. The existing combat
line-of-sight check rejects it. A separate eastern-room goblin can similarly detect through the chain
**45 -> 3** during the approach. Once accepted, the actors retain Nearby/detection memory, explaining why
they remain engaged at the final position even after the particular false detection ray is gone.

Initial OpenYAMM party detection now uses the existing combat visibility check, including moved door/wall
geometry and endpoint-sector resolution. Remembered encounters retain their previous shortcut; this does
not clear saved detection or tie AI to automap discovery. The same-sector scheduling pass and background
updates remain separate from granting detection. This deliberately tightens the original MM8 portal-only
detection rule documented above; it is not an additional solid-face test found in the original binary.

`tests/IndoorActorDetectionRuntimeTests.cpp` replays the entrance event and walk against Goblinwatch's
actual geometry, checks that opening the goblins' own door allows detection, and checks encounter memory
after snapshot restore. The entrance-walk regression failed before the change. A full-runtime replay with
the original spawned population also remains undetected along the walk and for 30 seconds at its end.
These tests run in `openyamm_runtime_tests` alongside the faction-alert regressions.

### Goblinwatch closed-room reveal during the approach (superseded, 2026-09-30)

This investigation concerns the removed strict exploration pass, not the current MM8-style discovery policy.

The reported movement starts at `(-183.015, 4869.934, 0)`, yaw `4.654`, pitch `-14.095` degrees,
and ends at `(-105.284, 4517, 0)`, yaw `5.667`, pitch `-9.969` degrees. Neither endpoint alone
reveals the room in a fresh map. Intermediate views can: one reproduction is
`(-167.4688, 4799.3472, 0)`, yaw `5.792311668`, pitch `-0.2` radians.

This was an OpenYAMM polygon-clipping precision error, independent of actor detection. The reveal
traversal accepted portal **116**, sector **3 -> 4**, while door **23** remained physically closed.
Subtracting the opaque wall/door shadows from the enlarged sector-boundary opening left a fragment
about 222 units long but only about `0.00001` units wide. Its area exceeded the old absolute area
tolerance, so an effectively zero-width fragment permanently marked the room's faces as seen.
The final screenshot retained that discovery even though its current view correctly rejected the portal.

The area test now scales its tolerance by polygon perimeter and checks the surviving fragments.
This rejects numerical strips while retaining real partial door openings. Rendering's conservative
sector traversal and saved exploration history are unchanged. The Goblinwatch regression covers both
reported endpoints, 64 headings at each of nine intermediate positions, and successful discovery after
opening the room's door. Ten of those closed-door checks failed before the correction. A separate
121-position/64-heading sweep found no remaining reveals along the approach after the correction.

The isolated native OpenGL/Wayland capture reproduced the permanent reveal before the change and
kept the room hidden afterward, using the same three-pose tour and fresh map state:
[before](../output/goblinwatch_visibility_20260930/before/03-at-closed-door.png),
[after](../output/goblinwatch_visibility_20260930/after/03-at-closed-door.png),
[tour](../output/goblinwatch_visibility_20260930/tour.yml).

### Initial actor-detection cost (2026-09-30)

The stricter wall/door test is retained. Three changes remove redundant work without changing its
range, actor memory, same-sector scheduling, background updates, or save format:

- Reject fresh detection candidates beyond 5120 units before resolving endpoint sectors. This uses
  the unadjusted target-point distance, preserving the distinction from the radius-adjusted 10240-unit
  AI scheduling range. Remembered encounters still bypass fresh detection.
- Resolve the party target's sector once per selection pass, only if a fresh in-range query needs it.
- Reuse the successful portal trace's sector list when collecting solid faces, instead of tracing
  the same segment twice. Ordinary combat visibility shares this code; actor-to-actor target selection
  retains its existing portal-only rule.

There is no new persistent visibility cache or invalidation policy. Each selection still uses current
party/actor positions and the runtime's current moved geometry.

A warmed CPU benchmark of `selectIndoorActiveActors`, using the normal optimized desktop libraries
and the same 217-actor fresh Goblinwatch snapshot, produced these median microseconds per selection:

| Pose/state | Before | After |
| --- | ---: | ---: |
| Closed entrance | 137.5 | 30.6 |
| Open entrance | 136.2 | 30.7 |
| Earlier false-detection trigger | 92.6 | 39.1 |
| End of entrance walk | 97.4 | 30.3 |
| Before this door approach | 88.3 | 30.7 |
| At the closed door | 92.9 | 36.2 |
| Goblin-room door open | 91.4 | 34.9 |

Each median uses nine rounds of 1024 selections. Encounter flags are restored outside the timed
selection so positive detection cannot turn later samples into remembered-encounter shortcuts.
All selected actor indices match before/after; the open-door case selects actors 51 and 199.
The reduction is 58–78% for this selection stage, not a whole-frame or Android performance claim.
[Raw timings](../output/goblinwatch_visibility_20260930/activation_timings.tsv).

Validation: the normal game builds; 41 focused portal/exploration unit cases (2191 assertions)
and all four detection/faction runtime cases (803 assertions) pass, including closed/open doors and
encounter memory after restore. Previously saved discovery is retained; reproduce the reveal fix with
fresh map discovery rather than expecting already explored saves to be cleared.

### OpenYAMM detection by sight, hearing and neighbours (2026-10-28)

An October change let any monster within 5120 in the party's sector, or one portal hop from it, detect the
party without a geometry test, through walls and closed doors. Large MM6 sectors made this wake whole room
groups at once. The user selected sight-based detection instead. `selectIndoorActiveActors` now grants fresh
detection in these ways only:

| Trigger | Rule |
| --- | --- |
| Sight | The full wall/door combat line of sight, within 5120, along either of two rays: from the monster's eyes (90% of its height) to the party's (160 above its feet), then, only if that is blocked, from its chest (75%) to the party's body (96). Each unaware monster checks on one AI step in 16 (eight times a second, staggered by actor index). |
| Hearing | Removed on 2026-11-04 at the user's request: it woke monsters through walls and ceilings. It was horizontal edge distance up to 512 and feet within 256 of the party's height, without a wall test. |
| Neighbour wake | A monster that newly detects the party (sight or its own AI gaining sight) or is hit by the party wakes every unaware hostile monster within 128 (3D, centre to centre, feet within 256) with full line of sight between the two, without a count limit. Woken monsters do not wake others. The radius was 1024 from 2026-11-04 to 2026-11-12 and 512 with at most five woken before that. A scene opts out with `actor_detection: {wakes: none}` (MM9's outdoor regions; devdocs/INDOOR_OPEN_SKY.md "Monster wakes"). |
| Damage | Unchanged: the struck monster detects the party; its neighbours now wake as above. |

The same-sector scheduling pass is unchanged: monsters in the party's feet sector still enter full AI, but they
engage only once they see the party. Remembered detection, the 30/48 caps, faction alerts (hostility only) and
background updates are unchanged. The height band keeps wakes on one floor; line of sight already stops
sight-based detection between floors. The world runtime's per-sector neighbour
lists existed only for the removed shortcut and were dropped from its geometry cache.

The eye ray was added on 2026-10-29 after a Castle of Air report (MM8 `d27.blv`, party at `(-532, -517, 0)`):
air elementals across the fountain in the party's own sector, both sides in plain view, never engaged because
the fountain rim hid the chest-to-body ray. The fallback ray keeps the old reach under low lintels. A blocked
monster costs one more check per interval.

`tests/IndoorActorDetectionRuntimeTests.cpp` covers same-sector and one-hop monsters behind walls, sight across
two portals, sight over a low rim but not a higher wall, no detection through a close wall or a ceiling, neighbour
wakes without chaining or a count limit, damage wakes, the Goblinwatch entrance walk and the closed/opened doorway
with restore.

**Wake radius survey (2026-11-04).** Over all 161 MM6–MM8 dungeons, the 1,983 sectors holding monsters (spawn
points and placed actors; 968 hold two or more groups) have a median floor-area radius of 696 and a median
half-diagonal of 1131. Groups in one sector are a median 1180 apart (90th percentile 3845); the nearest group in
another sector is at least 1042 away for three monsters in four. A direct wake covers every group of 23 % of
multi-group sectors at 512, 39 % at 768, 52 % at 1024, 61 % at 1280, 68 % at 1536 and 80 % at 2048. The user chose
1024 after comparing the radii in Ethric's Tomb (`6d14.blv`, central hall 2304 x 2560): a monster wakes its own part
of a room, and the far groups of a large hall stay asleep. The wake matters only for monsters that cannot see the
party; any monster with a line of sight to it within 5120 notices it anyway. Chained wakes were rejected: through
open doorways they could rouse half a dungeon.

**Wake radius 128 (2026-11-12).** The user lowered the radius from 1024 to 128: when the party looks round a corner
into a room of several groups and one monster sees it, only that monster's group comes, not the others. Over the
`assets_dev` scene files of MM6-MM8, the monsters of a spawn point start within 64 of it (the first on the point,
the rest at fixed offsets of 64 or less: `resolveIndoorEncounterPlacement`), so at most 128 apart, while the nearest
other spawn point indoors is a median 689 (MM6), 1004 (MM7) and 653 (MM8) away (10th percentile 192, 273 and 302).
Hand-placed dungeon monsters stand mostly alone (median 512-746 to the nearest other one) and wake nobody at 128.
A group member that has wandered more than 128 from the one that noticed the party stays asleep until it sees the
party itself.

Measured at the fresh MM6 Goblinwatch start pose (feet `(576, 6912, 192)`, the 2026-09-30 startup save and pose),
1600x900 windowed, VSync off, desktop OpenGL, 6-second warmup and 22-second interval, runs in the order
before, after, after, before with nothing else running. Medians of the per-second diagnostics:

| | Before | After | After repeat | Before repeat |
| --- | ---: | ---: | ---: | ---: |
| Monsters in full AI | 4 | 0 | 0 | 4 |
| Sight checks per second | 7808 | 520 | 520 | 7808 |
| Active-actor selection per AI step, microseconds | 44 | 10 | 11 | 40.5 |
| Actor fact collection per AI step, microseconds | 182.5 | 129 | 135 | 174 |
| Game frame, microseconds | 270 | 238 | 248 | 254 |
| FPS | 1859 | 1876 | 1897 | 1848 |

Before the change, the one-hop shortcut had already put four monsters behind the closed entrance doors into
full AI at this pose; afterwards nobody notices the party. Selection is about four times cheaper, with roughly
65 unaware monsters within 5120 each checked eight times a second instead of 128. The FPS difference (1–2%)
is within run-to-run variation: actor AI is a small share of this frame. Run records, settings, the pose and
`summarize.py` are in [`output/goblinwatch_detection_20261028/`](../output/goblinwatch_detection_20261028/).

## Native idle Goblinwatch performance (2026-09-30)

Profiled a fresh MM6 `6d01.blv` instance at feet `(576, 6912, 192)`, yaw `4.672` radians,
pitch `-14.353` degrees. Native desktop OpenGL/NVIDIA on Wayland, 1600×900, VSync off, normal optimized
`build/game/openyamm`, Ryzen 9 5950X. The same newly generated startup save and pose were reused in all
comparison runs. Six seconds of warmup preceded each 22-second timing interval. Existing performance/FPS
diagnostics were enabled consistently. No builds or other analysis jobs overlapped the reported timing intervals.

The screenshot tour applies the exact camera pose after loading, then returns to normal simulation with
`exit: false`; measurements exclude its screenshot/readback. This also avoids relying on the startup snapshot's
indoor camera-angle restore. The [before](../output/goblinwatch_idle_perf_20260930/before-hud-cache.png) and
[after](../output/goblinwatch_idle_perf_20260930/after-hud-cache.png) captures show the intended closed entrance.

The scene is inactive in the expected gameplay sense: only sector **1** is explored, **zero full-AI actors**,
215 background actors, no actor movement integrations and no path plans. Background scheduling still runs at
128 steps/second. The full actor update averages about **6 microseconds per rendered frame**; the activation
selector averages **47 microseconds per AI step**, about **1.7 microseconds per rendered frame** at this FPS.
Stopping actor activation work therefore cannot account for a large frame-rate improvement in this scene.

The render list is deliberately broader than exploration: sectors `[1,2,3,4,5,6,20,53]`. Each frame submits
65 textured world batches, 22 actor billboards, 11 decoration billboards and four sprite objects, despite
the opaque entrance doors. A bgfx frame sample reports **207 draw calls total** with the HUD. At about
3500 FPS that is approximately 725,000 draw calls per second; simple geometry does not eliminate command,
uniform, state-change and driver overhead.

`perf record -e cycles:u -F 199 --call-graph dwarf,16384` attached to the warmed isolated game's PID for
25 seconds. The baseline captured 9340 samples with zero lost samples; the indexed-lookup follow-up captured
9553, also with zero lost samples. Approximately **56% of baseline sampled userspace cycles** were on the bgfx
render thread, including driver work; `RendererContextGL::submit` accounted for about 52% inclusive. These
are CPU samples across threads, not GPU percentages or additive elapsed frame times. Main-thread call-stack
unwinding was incomplete in this build; leaf symbols and existing per-stage timers supplied its breakdown.

Two contained optimizations were implemented:

1. `MergedBolsterMonsterTable::findById` used a linear scan and accounted for **2.24% of all sampled CPU cycles**.
   Build an ID-to-row index when loading the table. Sparse IDs, first duplicate wins, reload and copied-table
   ownership are preserved. Its cost falls below the follow-up report's 0.5% threshold.
2. HUD portrait arc meshes were rebuilt for every draw, even with unchanged geometry and meter values.
   A runtime-owned CPU cache retains up to 64 meshes and keys all position, dimension, stroke, angle and fill
   inputs. Texture/colour selection and draw order stay live, with no new GPU resource lifetime. The maximum
   retained mesh payload is about 788 KiB. This avoids repeated trigonometry and tessellation, while continuing
   to composite the HUD each frame. It is not a cache of the entire HUD image.

Medians of the one-second diagnostic samples, microseconds unless shown as FPS:

| Stage | Baseline | Indexed lookup | Baseline repeat | Index + HUD mesh reuse |
| --- | ---: | ---: | ---: | ---: |
| Actor rendering | 37 | 25.5 | 36 | 26 |
| Whole world-render callback | 90 | 78 | 88 | 78 |
| HUD rendering | 83.5 | 83 | 82 | 72 |
| Main game-frame callback | 208 | 195.5 | 203.5 | 185 |
| `bgfx::frame` time, including waiting | 68 | 82 | 75.5 | 90 |
| FPS | 3480 | 3458 | 3432 | 3496 |

The main callback loses roughly **20–23 microseconds** of work, but much of that becomes extra waiting for
the render thread. These runs do **not** establish a meaningful FPS gain. Draw count remains 207. The shared
lookup and arc changes reduce CPU work without changing actor activation or tightening sector visibility.
The party HUD rectangle `(670,680)–(920,900)` is pixel-identical between the before/after native captures;
torch animation accounts for scene differences.

Further FPS work should first target draw submission, for example batching or precomposing appropriate static
HUD layers. The whole HUD cannot simply be skipped: the new world frame must still be composited with it, and
portraits, meters, highlights, time, counters, buffs and minimap content have distinct change conditions.
General wall/door occlusion adds a separate correctness problem and is not an original-MM8 requirement; see
the closed-door rendering investigation above. No such render-culling change was made in this performance pass.

Validation: normal game and unit-test targets build. All 39 focused table, bolster and HUD cases pass
(3395 assertions), covering sparse/duplicate IDs, copies/reloads, arc input changes, eviction, empty arcs,
closed rims and the existing HUD geometry rules. Native OpenGL captures and timing runs complete normally.
[Machine-readable timings](../output/goblinwatch_idle_perf_20260930/measurements.json),
[baseline perf self costs](../output/goblinwatch_idle_perf_20260930/before-perf-self.txt),
[baseline inclusive costs](../output/goblinwatch_idle_perf_20260930/before-perf-inclusive.txt), and
[indexed perf self costs](../output/goblinwatch_idle_perf_20260930/indexed-perf-self.txt) retain the evidence.
The output directory also preserves the isolated startup save, pose tour, per-run hashes and timing logs.

Example comparison launch (run sequentially, with no compilation/profiling work competing during FPS timings):

```bash
./tools/run_game.sh --isolated goblin-idle --world mm6 \
  --save "$PWD/output/goblinwatch_idle_perf_20260930/startup.oysav" \
  --warmup 6 --seconds 22 --set video.vsync=false \
  --set debug.screenshot_tour_path="$PWD/output/goblinwatch_idle_perf_20260930/pose.yml"
sudo -n perf record -e cycles:u -F 199 --call-graph dwarf,16384 \
  -p GAME_PID -o /tmp/goblin-idle.data -- sleep 25
```

For sampling, start a longer isolated run, read its PID from `run.json`, and attach after warmup. The sampling
command is separate from the unprofiled 22-second comparisons. Matching baseline and indexed executables are
retained locally at `/tmp/openyamm-goblin-perf-before` and `/tmp/openyamm-goblin-perf-indexed`; raw captures are
`/tmp/goblin-inert-before.data` and `/tmp/goblin-inert-indexed.data`. Do not interpret profiler-affected FPS as the
comparison result. No Vulkan or Android performance result is claimed.

## Castle Darkmoor rotation: restore MM8 discovery (2026-09-30)

The reported MM6 `cd2.blv` pose, feet `(14534.587, 7661.890, -180)`, yaw `4.886` radians,
pitch `0.602` degrees, reproduced a severe CPU regression during continuous mouse-look. Standing still
reused the visibility result; every turn rebuilt both render visibility and the additional strict exploration
result. The latter repeatedly subtracted opaque wall/door shadows from portal polygons.

The baseline `perf` capture contains 6005 samples with zero lost samples. Across sampled userspace CPU cycles,
`clipPolygonToPlane` accounts for 19.36%, `polygonHasArea` for 14.11%, and `malloc`/`cfree` together for 13.37%.
These are leaf CPU samples, not GPU timings. The minimap change, rather than a requirement to activate nearby
monsters when turning, was the source of the multi-millisecond visibility work.

The original executable's hash was rechecked, then Rizin rechecked `0x4b0fbf`, `0x4b04b3` and
`0x43f904–0x43f95e`. MM8 sets the face SeenByParty bit during ordinary render-face processing, before
subsequent facing/clipping rejection, and latches outline discovery from those bits. It has no corresponding
second opaque-polygon subtraction pass. This is static code evidence; no original-MM8 FPS measurement is claimed.

The user explicitly selected **Restore MM8 discovery rules**. The final implementation therefore:

- Reuses the normal portal traversal for discovery and removes the strict occlusion pass, its input option
  and its polygon-shadow implementation. It does not retain an expensive hidden mode or add a delayed reveal.
- Advances discovery's visibility revision only when the reached sector set changes. Turning within the same
  set still updates render frustums but does not repeatedly scan all faces/outlines for unchanged discovery.
  Existing surface revisions, door geometry invalidation and map/save lifecycle handling remain authoritative.
- Retains the separate door-collision, actor-detection and faction-alert fixes. Saved discovery is not erased.

This restored MM8's discovery policy, not every portal traversal rule. At this stage, OpenYAMM's conservative
sector-boundary portal expansion remained; the later portal corrections below remove it.
Adjoining rooms can become mapped before entry or while an opaque door still hides their pixels. The discarded
strict-exploration tests were replaced with coverage of the selected portal-based policy; render visibility,
door states, portal frustums, actor activation and revision checks remain covered.

Native comparison uses the same fresh startup save, 1600×900 desktop OpenGL/NVIDIA, VSync off, and the normal
optimized build on the Ryzen 9 5950X. The camera pose is applied once with a screenshot tour; simulation then
runs normally. A mouse-input tour waits 10 seconds, turns at 400 pixels/second (1.8 radians/second) for 30 seconds,
and stops. Immortality is enabled consistently to keep the fresh party alive; monsters continue updating.
No builds or profiling jobs overlap the FPS comparison runs. Samples near phase transitions are excluded.

| Median diagnostic | Strict exploration baseline | Ordinary-traversal control | Final restored discovery |
| --- | ---: | ---: | ---: |
| Initial stationary FPS | 2369 | 2276 | 2339 |
| Continuous rotation FPS | 353 | 2594 | 2494 |
| Visibility rebuild, microseconds | 2145 | 55 | 57 |
| World-render callback while turning, microseconds | 2137 | 133 | 125 |
| Main game-frame callback while turning, microseconds | 2810 | 324 | 331 |

The control is the same task-start implementation with only the extra discovery traversal bypassed; it is
not presented as a historical release binary. The final result returns to that single-traversal performance
range, roughly seven times the regressed turning FPS. Different directions submit different scene content,
and live actor simulation adds run-to-run variation; stationary and rotating FPS are not expected to be identical.
A second final-build run measured **2710 FPS** median while turning, with a **54.5-microsecond** visibility
rebuild and a **300-microsecond** main callback. The two final runs bracket the 2594-FPS control, supporting
restored performance rather than a claim of a further consistent gain over the ordinary traversal.

The normal game and unit-test targets build. All 39 focused cases pass (1102 assertions). The final native
capture was inspected. [Run records, logs, phase measurements and replay inputs](../output/darkmoor_rotation_perf_20260930/)
retain the evidence, including executable hashes and the copied starting save. `summarize.py` regenerates
the phase statistics from the archived logs. The optional native input-tour `look_rate` operation is documented
in [Desktop game runs](../tools/RUN_GAME.md); ordinary gameplay launches do not use it.

## Goblinwatch entrance parity audit (2026-09-30)

The reported comparison shows OpenYAMM's map book with an eastern corridor and southern rooms already mapped,
versus an MM6 entrance minimap showing only the entrance and a short western passage. This section records
the audit before the implementation below; its "current" comparisons refer to that earlier binary.

### Reproduction in OpenYAMM

A temporary native probe loads `assets_dev/worlds/mm6/maps/6d01.blv` and its scene YAML, creates fresh map/event
state, applies mechanism vertices and builds the normal portal graph. Before traversal there are **zero seen
faces and zero discovered outline bits**. The reproduced excess does not require a previous save or cached visit.

The entrance pose uses camera eye `(576, 6912, 352)`, sector 1, yaw `4.672`, pitch `-0.250507` radians,
vertical FOV 60 degrees and aspect 16:9. Feet are `(576, 6912, 192)`. Independent probe variants produce:

| Traversal variant | Reached sectors |
| --- | --- |
| Current renderer | `1, 2, 3, 4, 5, 6, 20, 53` |
| Disable sector-boundary/synthesized aperture expansion only | `1, 2, 5, 20` |
| Disable clipped-portal recovery only | `1, 2, 3, 4, 5, 20, 53` |
| Disable both; also tighten near-portal checks, retain child clipping for horizontal portals and check portal side | `1, 2, 5, 20` |

These are OpenYAMM probe results, not original-MM8 sector measurements. The last variant is not a complete
emulation of MM8's fixed-point projection and scanline-window processing.

The current south-facing path admits `1 -> 2 -> 3 -> 4 -> 53`, `1 -> 5 -> 6`, and `1 -> 20`.
An east-facing entrance view admits `1, 20, 21, 48`, explaining how the distant eastern corridor can be added
as the party looks around. With aperture expansion disabled, that east-facing view at the same downward pitch
reaches only `1, 20`. Discovery accumulates across views; one screenshot need not represent one traversal.

The three authored portals out of sector 1 are especially revealing:

| Face | Linked sectors | Initial geometry | Linked mechanism |
| --- | --- | --- | --- |
| 1935 | 20 / 1 | One-unit-high strip at X=960, Y=6272..6528, Z=0..1 | Door 16 |
| 1443 | 1 / 2 | Six-unit-high strip at Y=6016, X=448..704, Z=0..6 | Door 1 |
| 1972 | 1 / 5 | One-unit-wide strip at Y=6272, X=-65..-64, Z=0..256 | Door 2 |

All three mechanisms have initial distance zero. These are door-linked authored apertures; their small initial
size does not establish malformed geometry. Current adjusted vertices and static vertices agree at this pose,
so changing vertex sources alone does not resolve the initial overexploration.

The probe also enumerated non-BSP faces plus all reachable BSP nodes in each of the eight selected sectors.
Their union covers every face in the corresponding sector face lists. Using all sector faces rather than
these BSP lists is therefore not the cause of this particular entrance reproduction.

### Remaining differences from verified MM8

The original executable hash was rechecked and Rizin rechecked the portal submission, projection and window
intersection routines. Remaining OpenYAMM differences include:

| Area | OpenYAMM | Verified MM8 |
| --- | --- | --- |
| Portal aperture | `buildSharedSectorBoundaryPortalPolygon` and `buildDegenerateVerticalPortalBoundaryPolygon` can replace authored vertices with a larger sector-boundary rectangle. | Uses the portal's live vertices; no corresponding synthesized sector-boundary rectangle in the traced path. |
| Door movement | `IndoorRenderer::buildVisibleSectorMask` passes static map vertices as `pPortalVertices`, although adjusted vertices are separately available. | Projection reads the live vertex array. |
| Near-portal shortcut | Bounding-box slack 128, at any traversal depth, with no separate 9-unit plane-distance restriction. | Initial node only, bounding-box margin 16 and absolute plane distance at most 9 units; `0x4b13cf–0x4b1474`. |
| Rejected portals | Can recover a clipped-away portal within 512 or 1024 units at shallow depths. | Ordinary path must pass projection and parent-window intersection. |
| Child view | Horizontal or nearby portals can restore the full camera frustum; some recovery paths also retain the parent frustum. | Ordinary child view is narrowed through the accepted portal; the initial near-portal branch is a separate exception. |
| Facing | Broad behind-camera rejection. | Checks the oriented portal-plane side relative to the current sector before projection; `0x4b1586–0x4b15e1`. |
| Projection | Continuous floating-point frustum clipping. | Fixed-point projection and integer scanline windows; equal minimum/maximum projected Y rejects at `0x4234f3`, and the final intersected Y range must have positive extent at `0x42388a`. |

The first and fourth differences have isolated causal evidence in the table above. The others are verified
implementation differences, not separately proven causes of every extra outline in the screenshot. In particular,
no arbitrary world-space or one-pixel cutoff has been established as a correct replacement for the original
window algorithm. Camera pitch, FOV, aspect ratio and raster resolution also matter when comparing tiny apertures.

### MM6 comparison: discovery happens later

The available comparison executable is
`reference/Misc-MM8Patch-2.5.7/MMPatches/Install/MM6patch/Files/MM6.exe`, SHA-256
`fe3adb9ed62cb300f979ef337a9c093a0115d656ebf9ed758408532699ebf4d7`.
It is a **patch-distribution binary, not authenticated vanilla MM6**: its entry stub loads `MM6patch.dll`
at `0x4b8ddf–0x4b8de4`. The following is disk-code evidence only; runtime DLL hooks and the exact executable
used for the supplied MM6 screenshot were not established. Keep these addresses separate from MM8 annotations.
The [MM6 disk-code annotations](mm6_fe3adb9e_indoor_discovery.rz) record these sites with that provenance.

Rizin located the minimap through the outline pointer `0x5f7d50`, then traced its face-bit dependency:

- The MM6 HUD outline logic at `0x437347–0x4373ad` uses the same basic rule: both faces must be visible,
  and an existing outline discovery flag or either face's `0x80` bit admits the line. It latches an MSB-first
  packed discovery bit at `0x5f7dac`.
- In the ordinary MM6 face path `0x494ef0`, invisible faces return first and sky/water take separate paths.
  The normal path calls projection/facing helper `0x491990` at `0x494f53` and returns on failure. It then calls
  scanline-window intersection `0x4924b0` at `0x494f6f` and again returns on failure at `0x494f76`.
- Only after these gates and valid texture lookup does it OR `0x80` into the face attributes at
  `0x494feb–0x494ff0`. The helper rejects a back-facing nonportal face at `0x4919fe–0x491a16` and intersects
  the projected window at `0x492878–0x49299b`.
- Verified MM8's ordinary software and D3D paths set the bit earlier, at `0x4b04b3` and `0x4b0fbf` respectively,
  before their later projection/clipping checks, as documented above.

Thus the inspected MM6 code provides a concrete reason for less exploration even with a similar portal sector
set: selecting a sector does not itself mark all of its ordinary faces seen. This still does not establish
per-pixel opaque-door visibility, nor prove the exact captured MM6 outline set without matching runtime conditions.
The renderer's sectors, persistent discovery and actor AI remain separate systems in this comparison.

To inspect this comparison independently after checking the stated MM6 hash:

```bash
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -i re_mm8/mm6_fe3adb9e_indoor_discovery.rz \
  -c 'pd 38 @ 0x437347;pd 52 @ 0x494f53;pd 24 @ 0x4919d0;pd 3 @ 0x4b8ddf' \
  reference/Misc-MM8Patch-2.5.7/MMPatches/Install/MM6patch/Files/MM6.exe
```

### Consequence for further fixes

The inexpensive fidelity direction is to correct the existing traversal's use of authored, moving apertures
and its exceptional clipping rules. The current expansion/recovery rules also have tests for previously
reported open-door and thin-portal rendering failures; replacing them requires verifying those real openings,
not just changing expectations to accept missing geometry. The Goblinwatch entrance and Castle Darkmoor rotation
should be checked together with those cases.

Matching MM6's later face-discovery gate would be a further behavior choice beyond the selected MM8 policy.
It should share the appropriate render-face result rather than add a second opaque-geometry traversal. The
audit itself made no new FPS claim or production change. The user subsequently confirmed MM8 as the target.

## MM8 portal traversal corrections (2026-09-30)

The implementation now uses the authored portal polygon after mechanism movement, without constructing a
larger opening from adjoining sector bounds. An ordinary portal must face the current sector, intersect the
eight-unit camera near plane and current portal frustum, and produce a narrowed child frustum. Horizontal
portals retain that clipping too. A rejected opening is not recovered because it is nearby or shallow in
the traversal. The full-view exception is restricted to the initial node, within nine units of the plane
and sixteen units of its live bounds, following `0x4b13cf–0x4b1474`.

Render queries additionally reject polygons whose projected minimum and maximum screen rows are equal,
matching the verified nonzero-Y-extent gate at `0x4234f3`/`0x42388a`. Framebuffer height participates in the
visibility cache key. Gameplay geometry queries retain resolution-independent frustums. Discovery still
reuses the one render traversal and advances its revision only when the reached sector set changes.

### Collapsed door portals need their stored plane orientation

The Necromancer's Guild (`d19.blv`) explains an earlier apparent need for the synthesized aperture. Portal
3772 connects sectors 2 and 3. Its base vertices are `(1024,2880,384)`, `(1024,2880,0)`,
`(1024,2880,0)`, `(1024,2880,384)`: a line with zero polygon area. Its authored fixed-point normal is still
`(0,-65536,0)`. Doors 61/62 move different vertex pairs and create the real opening. Deriving a normal only
from the base polygon loses this valid orientation and incorrectly hides the open doorway.

`IndoorMapDataLoader` now retains the native 16.16 plane normal. Portal traversal combines this original
orientation with current mechanism vertices, as the MM8 routine does. The native writer preserves it on
round trips and writes derived normals for newly authored geometry. Tests cover both the original map and
an exported/reloaded copy, views through the opening at several angles and the return path to the lobby.
An audit of the 162 mounted BLV files found nonzero stored normals for all 5,302 portal records using the
MM7/8 face layout; no runtime asset repair or guessed replacement aperture was needed.

This also removes the need to allocate a whole-map `IndoorFaceGeometryCache` on each visibility rebuild.
Imported portal traversal uses the stored normal directly; procedural geometry computes one when needed.

### Scope and numerical limits

This follows verified MM8 traversal and discovery conditions, not MM6's later face-discovery write. Ordinary
opaque faces are still not subtracted from portal windows, and a closed door can retain a small authored
aperture. Adjacent outlines can therefore appear while the door still hides room pixels. Actor detection
and wall/door collision retain their separate checks. Existing saved exploration is preserved; a fresh
map state is required to compare initial discovery.

The renderer remains floating point with its current FOV, aspect ratio and framebuffer dimensions. It does
not emulate MM8's complete fixed-point scanline-window intersections or its D3D four-extrema child-quad
construction (`0x49b92f`, `0x49b9d6`, `0x49bd40`). OpenYAMM clips the actual polygon and builds planes from
its edges. Original node/face capacity limits are also not emulated. Consequently, this is not a claim of
identical sector sets at every subpixel boundary or of an exact match to the supplied MM6 screenshot.

The normal game and unit-test targets build. All 119 focused indoor/map-state cases pass, with 19,333
assertions, including closed/open Goblinwatch apertures, the real `6d02` moving slit, `d19` collapsed portals,
horizontal child clipping, the initial-node near exception, face orientation and native export round trips.
The fresh [Goblinwatch map-book capture](../output/mm8_portal_parity_20260930/goblin/map_book.png) shows the
entrance and short adjoining passages without the distant eastern corridor or large southern rooms.

Headless runtime scenarios opened Goblinwatch door 1 and Guild doors 61/62 through their normal interactions,
checked the resulting mechanism states and saved private snapshots. Native captures verify the
[Goblinwatch corridor](../output/mm8_portal_parity_20260930/goblin-open/01-door-opening.png),
[Guild room](../output/mm8_portal_parity_20260930/d19-open/01-door-front.png) and
[return view](../output/mm8_portal_parity_20260930/d19-open/02-door-return.png).

### Darkmoor rotation cost after these corrections

Four sequential runs reused the earlier fresh Darkmoor save and replay: desktop OpenGL/NVIDIA, 1600x900,
VSync off, six-second warmup, 55-second interval and 30 seconds of mouse turning. Builds and profilers did
not overlap. The order was old binary, corrected binary, corrected repeat, old control. The old binary here
already contains the earlier removal of strict exploration, so this measures the additional portal changes.

| Turning median | Before | Before repeat | Corrected | Corrected repeat |
| --- | ---: | ---: | ---: | ---: |
| FPS | 3153 | 3039 | 3006 | 3021 |
| Visibility rebuild, microseconds | 51 | 51.5 | 8 | 8 |
| World-render callback, microseconds | 109 | 110 | 70 | 69 |
| Main callback, microseconds | 261 | 267 | 238.5 | 236 |

Visibility rebuilds are approximately 84% cheaper. This is a measured CPU saving, not an overall FPS gain:
the corrected runs remain near 3000 FPS, with baseline medians 1–5% higher in these runs. The bgfx frame
wait is also different (41–43 microseconds before versus 85 after), and live simulation/scheduling vary.
There is no recurrence of the earlier multi-millisecond exploration pass or its 353-FPS rotation result.
[Run records, inputs, logs, captures and phase statistics](../output/mm8_portal_parity_20260930/README.md)
preserve both executable hashes and the raw measurements.

## Reproduction: original binary research

Run from the repository root after checking the binary hash, using the cached analysis project described in
the [guide](RIZIN_GUIDE.md). These commands need no decompiler plugin and do not open the binary for writing:

```bash
sha256sum re_mm8/mm8_orig/MM8-Rel.exe
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -p re_mm8/work/mm8-rel-5326d564-base.rzdb \
  -i re_mm8/mm8_rel_5326d564_indoor_activation.rz \
  -c 'pdf @ 0x40172e;pdf @ 0x407be3;pdf @ 0x43cfde;pdf @ 0x43e896'
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -p re_mm8/work/mm8-rel-5326d564-base.rzdb \
  -c 'pd 36 @ 0x43f904;pd 36 @ 0x440581;pd 20 @ 0x4b0f99;pd 24 @ 0x4b0495'
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -p re_mm8/work/mm8-rel-5326d564-base.rzdb \
  -c 'pd 8 @ 0x45e320;pd 8 @ 0x45fa3e;pd 12 @ 0x45eae6;pd 17 @ 0x499b5f;pd 12 @ 0x43db47'
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -p re_mm8/work/mm8-rel-5326d564-base.rzdb \
  -c 'pdf @ 0x439278;pf f4 @ 0x4ea5f0;pd 17 @ 0x440108'
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -p re_mm8/work/mm8-rel-5326d564-base.rzdb \
  -c 'pdf @ 0x4b137c;pdf @ 0x4b002a;pdf @ 0x42347e;pdf @ 0x43e42b'
```

Automatic function discovery sometimes assigns overlapping/oversized boundaries. Some long disassembly batches
also emitted invalid instructions where a new, aligned short disassembly decoded valid bytes. Verify relevant
branches at their instruction addresses rather than inferring behavior from a truncated or misaligned listing.
