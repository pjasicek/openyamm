# Proposed orchestrator checks — review round 2

Not run by this batch session. Resolve/review the strict LOD3 silhouette limitation in HANDOFF before claiming full
batch completion, then install both final GLBs and merge all three blocks in actors.yml.

- Case: `MM6JackalmanCodexRound2`; monster ids **562, 563, 564**, Jackalman A/B/C.
- Indoor: MM6 `pyramid.blv` (Tomb of VARN), valid entry-room floor and clear corridor.
- Outdoor: MM6 `oute3.odm`, level open ground. Capture front, side and three-quarter views.
- Expected posed body height **205.799 world units**, allow 185–230; Standing horizontal span 55–180.
  Scale 109.233628; stride 1.253289580; yaw −1.570796327. All tiers share geometry and scale.
- Registry must accept distinct `Cast`, with melee/ranged both `Attack`. Melee and unused ranged alias impact
  0.989583333 s, no launch socket. Psychic Shock impact 0.927083333 s from `StaffTip`.
- Exercise Standing, Walking/run alias, two-handed Attack, Cast, Hit, Fidget, Death and Dead. Inspect palms,
  heel/toe planting, gait loop, shoulder twist, release timing, shaft contact and corpse/staff floor contact.
- Inspect the brightened skin under native indoor/outdoor lighting, gold/collar details, blue/purple/red tiers,
  dull grey hook, LOD switches, shadows and look-bone clearance. LOD3 counts: 595 body + 472 staff.
- Save/load must preserve model/skin/attachment bindings. Keep unrelated MM6/MM7/MM8 actors active; one rejected
  GLB or binding can disable the complete MM6 registry.

No game, regression suite, native capture, CMake or Vulkan build was launched by this session. No runtime file was copied.
