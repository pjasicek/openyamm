# MM6 Goblin — native head / neck revision

Review candidate: **R4**, using the original palette-745 textured rig and all nine retained clips.
Open [the existing comparison viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_goblin/review_20261006/).
Choose **Head / neck** focus; switch **Previous model** and **Face / neck revision**. Time, camera and
annotations remain fixed. Expand the original/previous/revised comparison below the viewport for the sprite
evidence. Saved frame links identify the exact model hash and restore the corresponding version.

## What the supplied images established

The previous model loses the original's severe facial proportions. This is a geometry problem as well as a
texture/lighting difference. The selected AI front/profile guides already softened those proportions; matching
those guides alone was insufficient. The original sprites govern the corrections below. A low-resolution
sprite establishes a silhouette and relative proportions, not an exact hidden anatomical scan.

| Feature | Original evidence / target | Previous model | R4 correction |
| --- | --- | --- | --- |
| Crown | Tapered, less domed upper outline | Large round forehead | Taper the bald crown while retaining the rear skull wedge |
| Eyes / brow | Small, recessed eyes under a severe sloping brow | Prominent eyes and round brow pads | Reduce eyes with their eyelid openings; reshape the orbital ridge |
| Cheeks | Angular cheekbone above a hollow | Full rounded cheek pads | Recede cheek fullness and define cheekbone transition |
| Mouth / chin | Broad snarl and relatively short, blunt lower face | Narrow mouth and long rounded chin | Widen mouth/dentures and jaw; shorten the chin |
| Nose | Short, compact nose; native green/brown appearance | Projecting pink/brown bulb | Reduce projection; warm texture colour remains a review issue |
| Profile | Long exposed, substantially upright neck; distinct skull wedge | Deep skull, forward face and thick sloping neck envelope | Reduce skull depth by 18%, move upper skin slightly back, narrow the neck envelope and clarify jaw separation |

All five user screenshots are retained in [feedback/](feedback/). The profile target was also checked against
the genuine native `gobsta2.png`, rather than deriving an anatomical target from a moving perspective view.
The source neck joint chain is approximately upright already. Rotating it would have changed every clip and
left the excessive skull depth and neck envelope unresolved.

Inspection also found **shoulder/clavicle weights in the lower chin**. Those could pull the jaw during arm
motion. R4 reassigns 166 lower-face vertices to Head/Jaw. Head, jaw and neck pivots and the nine action curves
are retained. Skin, detached eyeballs, dentures and the three ear hoops move coherently.

## Iterations and selected files

Four local sculpt iterations were reviewed. R1/R2 were diagnostic failures: guessed lower-face masks produced
lip projection and a pointed chin. Inspection located the actual chin and the clavicle weight leakage. R3
improved the front but retained too much skull depth in profile. **R4 is the selected review candidate**;
R1–R3 are retained diagnostics and must not be used as a delivery or production base. Every iteration starts
from the same previous master, rather than accumulating deformations.

- [Editable R4 master](goblin_anatomy_r4.blend)
- [Portable textured R4 export](goblin_anatomy_r4.glb)
- [Revision record and hashes](revision_r4.json)
- [Front comparison](review/after4_front.png), [profile](review/after4_right.png), [three-quarter](review/after4_quarter.png)
- [Original profile crop](review/native_profile.png), [previous front](review/before_front.png), [previous profile](review/before_right.png)

## Validation and remaining work

[Preservation checks](review/preservation_checks.json) pass: topology, UVs, all geometry/weights below the neck,
sword, bone hierarchy/rest, all nine action curves and actual exported motion samples, four embedded texture
images and material assignments are unchanged. Only the head/neck surface, its normals and the demonstrated
lower-jaw weights change.

[Actual GLB reimport checks](review/export_reimport_checks.json) evaluated 261 poses over all nine clips,
including a denser Death sweep. The maximum surface difference from the master is about 0.019 mm.
Native clips remain within the existing 8 mm contact tolerance. **The retained Meshy Walk/Run have existing
stock contact penetration of approximately 31/39 mm**; the export reproduces it, and it needs correction in the
gait pass. Export fidelity is separate from contact quality.

[Browser validation](browser/browser_validation.json) passes 42 checks, including same-pose model switching,
old-model feedback restoration, all clips, exact endpoints, slow playback, marks and mobile layout. Neutral
textured/clay head views, gait profiles, Attack, Hit and Corpse were inspected. These checks support a review
handoff; they do not establish artistic acceptance or clear the other reported motion defects.

Current stage remains **2, anatomy revision**, with stage 3 also needing revision. Next user action: review
the face/neck candidate and return marked frame feedback if needed. Next Codex production work: resolve
remaining likeness changes, fit the skirt, correct gait contact and the shoulder-led attack/wrist path, and
fix the affected hand/cloth contacts. The original FULL delivery and its ZIP remain historical review files.
No Meshy job was submitted: spending remains **20 / 100 credits**.
