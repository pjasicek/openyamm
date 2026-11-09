# The 152 unbound originals: short family lookup guide

These files were visually inspected using their **embedded BMP palette**, shown in `audit/triage_00.jpg` through
`triage_02.jpg`. Their intended runtime ACT overrides are not established merely by these previews. All remain
individually listed in `triage.json`; this is a prepared exception queue, not 152 guessed animation definitions.

Use the existing referenced family/output first. Restore only after establishing the intended appearance; do not
spend another full map audit on these. An unused alternate can be explicitly retained without any paid AI call.
If the driver later asks for unbound art as a separate library, use these identities to make focused additional jobs.

| Source family | Visual finding and next lookup |
| --- | --- |
| `3gem5`, `i1_ffall`, `obj314`, `sta1a`, `sta1b`, `sta1c` | Exact full-BMP matches to referenced assets; inspect `exact_bmp_candidates`. Verify the intended palette, then reuse the accepted appearance if appropriate. No independent redraw by default. |
| `3l_stol2`, `3memcrys`, `3rattail` | Stool, memory crystal, rat tail. Compare mapped stool/crystal/item descriptors and source aliases. |
| `6swptree1..4`, `6tree31..35` | Alternate swamp/seasonal/snow trees. Compare `swptree*` and tree families; preserve tree identity, do not infer runtime usage from the prefix. |
| `trotree01..06`, `ntree5`, `mr4` | Tropical broadleaf/palm trees and a dense low tree. Compare current tropical tree/cactus/bush originals. |
| `7dec35[a-f][1-4]` | Fountain statue at additional views with animated water. Current bound sequence uses the `...0` drawings. Share the accepted statue/stone treatment; establish view/timing intent before exposing the extras. No 24 unrelated fountain redesigns. |
| `7dec24h`, `brnrock6..9`, `torskul9`, `watwalk7` | Extra fire/log, burning-rock, skull-torch and water-walk drawings. Compare the complete bound sequence first; these can be omitted/redundant tail frames. |
| `nwtrch00..09`, `lntnrev0..5`, `fire0001..6` | Torch, lantern and burning-debris sequences. Keep rigid structure fixed; reuse related accepted torch/lantern/fire styling after confirming the native palette and timeline. |
| `no0se1`, `no0se3`, `no0se4` | Noose views. Compare the bound `noose` group/view rules; do not discard thin rope in cleanup. |
| `sta1a0` | A different statue drawing, unlike the fountain images named `sta1a/b/c`; avoid a misleading filename-only alias. |
| `dec93`, `tower`, `l1` | Small cave props: mushroom/stalagmite combination, tall porous stone formation, thin pale hanging formation. Generic word hits in code/events are not references to these BMPs. |
| `lightmap` | Radial grayscale light falloff/utility image. Retain native utility behavior; no decorative AI reinterpretation. |
| `flrsak`, `herbspr01..3` | Sack and herb/clump art; compare existing sack and herb pickup aliases and intended palette. |
| `7obj015`, `7obj169`, `7obj170`, `obj101`, `obj130`, `obj196` | Weapon, potion, belt, jewelry/gem alternates. Related numbered groups are candidates, not proof of same geometry/color. |
| `obj132`, `obj286`, `obj313`, `obj351`, `obj359`, `obj362..364` | Hand/glove, lantern, jewelry, jar crate, ore, amulet parts. Compare current object registry and MM7-prefixed counterparts. |
| `i2_fire`, `i6_magic` | UI-icon snapshots whose stems equal current group names, while active frames use other names. Check the mapped sequence; preserve existing panel/symbol if retained. |
| `arr[d-f][04]`, `frard[0124]`, `frare[04]`, `frarf[04]` | Arrow/fire-arrow extra views or poses. Compare bound arrow/missile sequences; keep thin shafts and dark physical cores. Never infer timing solely from alphabetical order. |
| `6splat01[a,c,d,e]`, `sp100[c,d]` | Red splatter/particle expansions; compare bound splat and spell families, especially discarded sequence tails. |
| `explo04g`, `spell04a`, `sp07c`, `sp26c`, `sp90c`, `sp93b` | Small explosion, ring, fire, sparkle, poison and debris effect pieces. Match actual visible art, not numerical spell-name guesses. |
| `sp15b10..60`, `sp76c10`, `sp76c20` | Lightning/cold burst stages. Compare related native FX frame tables for intended order and native lifetime. Preserve soft thin arcs. |
| `oval10[a-e]` | Animated oval energy pattern. Preserve the full oval/negative space and electrical pattern; no new UI frame. |
| `zapp01..06` | Expanding red spiral/ring frames. `icon_frame_data.txt:389` defines an icon sequence and `engine/icons/` has same-named files. Inspect icon lookup/bytes before treating sprite copies as active replacements. |

Report the actual disposition with `queue.py resolve-triage`; never mark an uncertain item restored without a real
artifact. A discovered additional active family needs a small explicit job extension and palette/timing provenance.
Keep unreferenced/unresolved counts separate from the confirmed 2,571-file restoration coverage.
