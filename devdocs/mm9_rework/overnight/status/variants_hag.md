# Variant hag (owner variants-c), 2026-11-02

- 10:20 lease claimed (mm9:hag). Reading brief and the body project; comparing MM9 meshes.
- 10:45 MM9 comparison: hag.abc = Yrsa.abc skeleton/bind (except braid binds) and byte-identical clips (walk, stand, fidget1, Wince3, Die3;
  extra static `hag1`); NPC132.scr plays only `die` (OnDamage) and DoRude, so Yrsa's 7 roles cover it. Mesh differences: bell sleeves
  (forearm cuff hangs up to 9.7 cm), no forehead bead band, braid binds moved (bone-local braid within 1.6-3.5 cm: same posed braid),
  temple hair 3-4 cm. Skin: ginger hair/braids, golden swirl damask bodice/overskirt, navy sleeves and lower skirt, olive hood, other face.
- Baseline: Yrsa rebuilt from a copy of its approved blend in this project = byte-identical to the installed mm9_yrsa.glb.
- Geometry `scripts/hag_geo.py`: bead band deleted (8 parts), bell flare on both sleeves (+lining, max 9.7/8.9 cm). Texture-pass UVs
  laid (body atlas 62 %, head 63 %). Codex HD masters (body 4 + head 4) running.
- 12:xx Meshy 20 credits (body + head retexture 4K, backup 3225 -> 3205). Built, gates: arm/hand 0 frames > 1 cm, jitter 0 fails, detached 0,
  flat 0.00, winding 0, sleeve gate = Yrsa's, see-through = Yrsa's approved baseline (inherited holes at hood/torso), floor ok.
  Installed `mm9_hag.glb`, bound `MM9 245 Old Hag` (row 245 in mm9_npc_actor_rows.tsv, fallback 307), tables regenerated,
  binding regression PASS (194 descriptors on 84 models). Viewer r2. Yrsa files unchanged (sha256 proof in README).
- FINAL: installed `mm9_hag.glb` (r2: hands toned x1.35/1.43/1.29 to her face), binding PASS 198/86, viewer r2 check 0 errors.
  20 credits (backup 3225 -> 3205 across my two jobs; 3085 at the end with other agents). Yrsa sha256 + project files unchanged.
  Open: see-through holes = Yrsa's approved baseline (not lined); hood lump beside the right jaw is Yrsa's geometry. README has it all.
  Lease released.
