# MM8 Salamander m568 HD masters

The user requested complete Claude-playbook 3D production, preserving the serpentine silhouette and fitted weapon handling. This brief covers the image stage only.

Authority: original native sprites extracted with hash verification from `../mm8_m568/sources.json`. `../references/identity.png` is the five-view identity sheet; `../references/attack.png` records the polearm and arm action. Tier A palette 569 is bronze/ochre-black, B 570 blue-black, C 571 red-black. All are retained in `../references/tier_palettes.png`.

Generate five separate unresized transparent 1536x1024 returns: `00_three_quarter.png`, `01_front.png`, `02_back.png`, `03_left.png` (nose image-left), `04_right.png` (nose image-right). Freeze the selected primary before the four other views; use it alongside the native sheet as authority. Same A-pose, same crest, tail and proportions. The straight trailing tail is a rigging adaptation of the native J shape; neutral open five-digit hands are inferred from the original held grip. The native polearm is required in the final creature but omitted from body masters.

Exact primary prompt: `primary_prompt.txt`. Check every return for native identity, colour, single continuous snake body, no legs, the one sagittal crest, complete tail, both separated hands, same pose, alpha and canvas. Preserve actual returns, prompts, input/output hashes and selection in `generation_runs.json`; selected reference hashes belong in canonical progress. Generate the separate native polearm reference after the body identity is established. No Meshy until all five body masters pass.
