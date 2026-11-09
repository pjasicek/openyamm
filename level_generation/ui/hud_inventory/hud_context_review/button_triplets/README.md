# Seven active button triplets · review candidate

The active gameplay YAML uses `but20`–`but26` in U (default), H (highlighted) and D (pressed) states. Their native
75 × 26 icons and prior exact-x2 review images were assembled into aligned [native](native_reference.png) and
[previous x2](current_reference.png) sheets. The [source manifest](source_manifest.json) hashes every source.
`buthireh` and `butn_dportal_3h` are outside this 21-state group because they are not used in the active HUD
layouts; the latter also lacks a matching D state.

Built-in imagegen edited the whole 21-button family twice. The [first master](imagegen_master_v1.png) had chunky
stone texture and weak pressed differentiation; the [second master](imagegen_master_v2.png) resolves those defects.
The exact [first](imagegen-call-v1.txt) and [second](imagegen-call-v2.txt) tool prompts are retained. The final
[fitted contact sheet](fitted_contact_v2.png) displays all exact 150 × 52 exports. The [review manifest](review_manifest.json)
records master, prompt, source and output hashes and measured crop rectangles. All 21 outputs are opaque RGBA with
zero near-key magenta pixels. They are review previews, not accepted or installed runtime icons.

The native H-over-U mean luminance differences range from 13.88 to 21.13 in the central panel region. The prior
restored x2 differences ranged from 2.57 to 22.43; the regenerated family ranges from 12.87 to 18.12. Pressed
states are consistently darker than default by 4.42 to 7.24 luminance units. These measures support the visual
comparison but do not approve the letterforms, stone texture or perceived button state. Check U/H/D in the
[HUD browser](../index.html) using the **Button state** selector and the **Regenerated button triplets** filter.
The detail panel links the previous edge-repaired x2 version and both the original and new masters.

To refresh the reference sheets and exact-x2 crops without generating new art:

```sh
python3 level_generation/ui/hud_inventory/hud_context_review/button_triplets/prepare.py
python3 level_generation/ui/hud_inventory/hud_context_review/button_triplets/fit.py
python3 level_generation/ui/hud_inventory/hud_context_review/build.py
python3 level_generation/ui/hud_inventory/hud_context_review/audit_user_flags.py
```

`build.py` accepts an output only when the prior x2, native preview, original candidate, master, prompt, source
manifest and fitted output hashes match. If the parallel second pass changes a source, its button repair stops
appearing until it is regenerated and fitted again.
