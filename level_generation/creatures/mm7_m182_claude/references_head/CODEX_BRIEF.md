# MM7 Dragon head turnaround (texture references)

Scope: image generation only with your built-in image generation tool; write only into
`level_generation/creatures/mm7_m182_claude/references_head/`. No builds, no Meshy.

Input 1 is the accepted whole-body HD master (`references_hd/00_three_quarter.png`): the identity authority.
Input 2 is the original MM7 sprite set (front, three-quarter, profile, rear three-quarter, back); it confirms the crest.

Make four images, each a single isolated HEAD AND UPPER NECK of exactly this dragon, 1254×1254, true transparent
background (alpha 0), the head filling most of the frame with at least 10 % empty margins on every side (no cropped
spike or frill), neutral diffuse studio light, no cast shadow, no ground, no body, no wings, no text, no fire or glow:

| File | View |
|---|---|
| `00_three_quarter.png` | three-quarter front, face turned toward viewer-left, camera at eye height |
| `01_front.png` | straight front, symmetric |
| `02_profile.png` | true left profile, snout pointing to image LEFT |
| `03_back.png` | straight back of the head and crest; no face visible |

Keep exactly: narrow reptilian snout, mouth slightly parted with small pale teeth and a dark mouth interior, yellow
eye with dark slit pupil, crest of several short ivory-white spikes radiating back and up from the rear of the skull,
yellow-green spiny frill along the jaw line and behind the head, row of short yellow-green dorsal spines down the
neck, dark forest-green scales with lighter green highlights, segmented gold throat plates. A precise enlargement of
the existing head, not a redesign: no long horns, no extra horns, no colour changes.

Generate 00 first, then 01-03 with your selected 00 as an additional input; at most one corrective regeneration per
image. Record every generation in `generation_runs.json` (name, prompt, input sha256 list, output path, sha256,
selected, review) and stop.
