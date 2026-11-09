# Proposed integration regression: mm6_mep_codex

Orchestrator-owned checks; none were run by the asset worker.

- World/map: MM6 `oute3.odm`, plus an MM6 indoor fixture such as `d05.blv`.
- Summon merged monster IDs **613 / 614 / 615**, descriptors **PeasantM3 A / B / C**.
- Standing height target **175 world units**, accepted bounds **160–190**; feet meet the map floor.
- Merge the three exact blocks in `actors.yml`; install only the two final GLBs listed in HANDOFF.md.
- Check all three palettes outdoors and indoors, ordinary town behaviour, Walking and forced Running.
  Walking stride is 0.618182 m; Running is 0.958182 m, matching the runtime 1.55 multiplier.
- Force every bound role. Mystic of Baa must use distinct **Cast** for Mind Blast; verify the staff-head launch
  socket at 0.843750 s and confirm Cast is the exact Attack motion (both 1.433333 s). Physical staff contact is one-handed, following the native frames.
- Check eye/palm sockets, look turns, projected shadows and the transitions at 500 / 200 / 80 actor pixels
  (asset review uses 550 / 220 / 88 with hysteresis margin).
- Death falls backward, opens the right hand and releases the staff at 0.075 s (Death duration 1.816667 s after the requested 2x speed change); Dead holds the final pose.
  Check sloped floors and blended transitions, which the isolated Blender/viewer checks do not simulate.
- Run the existing MM6 actor suite after merging and smoke-check MM7/MM8 actor loading and shared registry
  behaviour. No gameplay tables, native monster IDs or engine behaviour changes are proposed.
- Capture matching sprite/model views indoors and outdoors, then collect artistic approval.
