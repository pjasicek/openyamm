# Proposed integration regression (orchestrator only)

Case: **mm6_sorcerer_codex_family**. World **mm6**, map **6d07.blv**.
Summon monster ids **631, 632, 633** (Sorcerer, Magician, Warlock; descriptors Sorcerer A/B/C).

Install only export/mm6_sor1.glb and export/mm6_sor1_staff.glb under assets_dev/worlds/mm6/models/,
then merge the accompanying actors.yml blocks. No installation or runtime execution happened in this batch session.

Checks:
- All three ids bind the same body and staff; skins sor1_a, sor1_b, sor1_c select black/olive, red and purple.
- Standing main-body height **175–185 game units**, tier spread below 1 unit. Expected 179.899.
  Whole actor including the staff top: **185–200 units**. Do not normalize body height against the staff.
- Scale **106.121**; yaw offset **-1.570796327**. Verify facing against each native view.
- Required clips: Standing, Walking, Attack, Cast, Hit, Death, Dead, Fidget. Running intentionally maps to Walking.
  Speeds 200/220/240 are below 2.4*scale = 254.690 game units/s.
- One B_Staff attachment per actor; palm sockets and Socket_Staff_Head exist; no duplicate embedded staff.
- Ranged Attack: **Socket_Staff_Head at 1.220833 seconds** during the two-handed forward thrust (clip 2.5 s).
  Cast: **Socket_Staff_Head at 0.7375 seconds** during the one-handed staff cast (clip 2.05 s).
  Melee alias uses Attack with impact 1.220833 s and no launch socket. Verify event timing/blending against gameplay;
  retain original Air/Air/Energy attacks and Lightning Bolt skills.
- Walking stride_length 1.25 follows the closest caster integration; check actual ground speed and foot sliding.
- Exercise damage interruption, death-to-held-corpse transition, all four colour/shadow LODs, turning/looking,
  indoor lighting and an outdoor daylight placement. Capture both native sprite and model at matched size.
- Run the affected MM6 actor regression and the shared MM6/MM7/MM8 actor paths after integration.
- Inspect body/head atlas seams and the staff specular mask in the real renderer. Browser and Blender checks
  do not establish bgfx appearance or native GPU performance.

Art review still required: the death is an adapted backward fall into an extended supine corpse, with the staff
retained and angled beside the body. The native corpse is more tightly curled on its side with the staff lower.

Review round 3: inspect both wrists at 0.5333/0.6667 s and the two-handed forward drive at 0.9667–1.5667 s.
The front foot steps 280 mm with 50 mm lift; the rear foot remains planted. Check release and recovery blending.
Cast remains accepted and unchanged. Exercise the rebaked lower LODs at 550/220/88 px, including Death/Dead trousers.
Body triangle counts are 7753/4085/1852/907; staff 1674/720/340/148. Inspect the four independent normal-map atlases.
