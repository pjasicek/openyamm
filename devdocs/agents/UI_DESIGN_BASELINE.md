# UI design baseline (approved designs)

Moved from the root `AGENTS.md` (section "In-game HUD Design Reference") on 2026-11-24, unchanged. It records
which HUD, overlay, menu, journal and Android designs the user approved and which later refinements supersede
earlier studies. Read it before changing the look or layout of any UI screen.

- The latest user-approved in-game HUD design is **Obsidian refinement 04** (2026-09-27). When revisiting HUD design,
  start with the [approved design reference](../../level_generation/ui/hud_concepts_20260927/README.md#latest-approved-design),
  its preserved screenshot and interactive mockup. This remains the selected visual baseline. The user authorized
  wholesale native integration on 2026-09-28; the shared gameplay HUD is now Obsidian on desktop and Android.
  The final native refinements use 10% larger gameplay portraits, a 112-logical-pixel minimap, lower portrait placement
  and separated HP/SP bars. Do not restore names or redundant condition labels beneath gameplay portraits.
  The [2129 native refinement](../../level_generation/ui/obsidian_engine_handoff_20260928/refinement_2129/README.md)
  puts the four icon-only menu actions beside gold/food on one slim top-left bar. The minimap is raised and has no
  location title. Hero/skull panels below the shared bar display ordinary party buffs; the timed-icon/overflow strip
  is retained for future special modifiers only. HP meters use green at 66% and above, yellow above 33%, and red at
  33% or below. Preserve these later user-directed changes when using the earlier browser studies.
  The [2130 correction](../../level_generation/ui/obsidian_engine_handoff_20260928/refinement_2130/README.md) anchors the
  bar at screen (0,0), insets the gold icon and removes the bar/minimap outer shadows. It replaces legacy buff layers
  with true-alpha Obsidian atlases and restores the old desktop skull meanings: Torch Light glow, Feather Fall clouds,
  Stoneskin stone skull, Day of the Gods halo, Wizard Eye near eye and Protection from Magic garland. Do not restore
  the incorrect Android mapping that assigned the Torch Light glow to Fly.
  The [2131–2132 refinement](../../level_generation/ui/obsidian_engine_handoff_20260928/refinement_2132/README.md) reduces
  resistance gems to a shared size budget, adds a three-unit left buff-panel inset, restores subtle minimap shading
  and places live time above it. A reskinned legacy head at the right edge toggles the original followers panel.
  Fly/Levitate and Water Walk use separate animated indicators; never add them to the skull layers or badges.
  The [dynamic party basebar](../../level_generation/ui/obsidian_engine_handoff_20260928/refinement_party_basebar/README.md)
  implements the 2026-09-29 follow-up: one centered Obsidian frame sized to the active party, exterior end ornaments,
  and vertical HP/mana tracks to each portrait's right. Keep the accepted portrait scale, HP colours, recovery and
  selection rules, and omit the mana track when maximum mana is zero. This supersedes floating gameplay portraits
  and horizontal gameplay meters in the earlier studies; the approved refinement below supersedes this first version.
  The user subsequently selected **A, split arcs** from the
  [2133 curved-meter study](../../level_generation/ui/obsidian_curved_portraits_20260929/README.md).
  Its [native integration](../../level_generation/ui/obsidian_curved_portraits_20260929/native/README.md) supersedes the
  vertical gameplay tracks: HP wraps left, mana right, selection stays on the inner rim/top diamond, aggro/recovery
  lower-left and personal buffs lower-right. The dynamic basebar is flush with the screen bottom, with a narrower
  border and compact end ornaments; all portrait elements clear its border/corners. Retain accepted portrait size,
  HP bands, no-mana and nobody-ready rules.
  The user approved the final native appearance on 2026-09-29; this fitted split-arc implementation is the current
  gameplay portrait/basebar baseline, not a pending browser proposal.
  The 2134 follow-up enlarges only the gameplay selection diamond from 16 to 20 logical pixels; keep the portrait
  dimensions and HP/mana arc widths unchanged. See the native reference's `refinement_2134/` captures.
  The 2135 follow-up uses Lucida scale 0.75 for gameplay event/hover status text and anchors its content-sized plate
  six logical pixels above the basebar; longer text grows upward. Fullscreen status/input rail styling is unchanged.
  The [full-screen follow-up](../../level_generation/ui/obsidian_curved_portraits_20260929/native/overlay_arcs/README.md)
  applies the same split arcs, selected rim/diamond and lower indicators to inventory, house dialogue and the other
  shared overlay screens. Keep their existing portrait dimensions, fixed 4:3 frame and clear status/input rail;
  overlay selection continues to identify the inspected member even while the party is recovering.
- For the separate centred 4:3 inventory and house-dialogue screens, the user selected **Carved Obsidian**
  (2026-09-27). Follow the [full-screen design reference](../../level_generation/ui/hud_overlay_study_20260927/README.md)
  for the current refinements. Native fullscreen chrome includes the clear status/input rail from 2116; retain
  the fixed 4:3 media geometry and existing portrait/paperdoll assets.
- **Fondamento** is the user-selected button typeface (2026-09-28). For overlay reading surfaces the user selected
  **dark obsidian, soft ivory and the recreated MM fonts in their original roles**. The
  [extended overlay collection, revision 03](../../level_generation/ui/obsidian_overlays_20260928/README.md) follows
  references 2078–2088: original content layouts, held-RMB inspection, blue whole-row skill upgrades, simple dialogue,
  a bottom-anchored item value, grouped rest controls and clearer section/column divisions.
  The user approved **revision 03 in full on 2026-09-28**, including its semantic colours, shared border and
  glyph-free buff illustrations. Use the [staged integration package](../../level_generation/ui/obsidian_overlays_20260928/staging/README.md)
  for source graphics and design contracts. Current mounted layouts and shared render/input code implement this collection.
- The [Adventurer's Guild replacement](../../level_generation/ui/obsidian_adventurers_guild_20260929/README.md)
  implements the requested Obsidian reskin from 2143: generated carved-stone/brass frame, recessed eight-slot roster,
  ivory SMALLNUM reading text, biography divider, gold selection and Fondamento Hire/Exit buttons. Preserve its
  original portrait geometry, paging, double-click character inspection, paperdoll and hiring behavior. Runtime
  artwork and layout are mounted under the engine-owned icons and `adventurers_inn.yml`; native captures are linked.
- The user approved the [painted Obsidian rest hourglass](../../level_generation/ui/obsidian_rest_hourglass_20260929/README.md)
  and its **2140 conserved-sand correction**, then requested native integration on 2026-09-29. The
  [native implementation](../../level_generation/ui/obsidian_rest_hourglass_20260929/native/README.md) uses one fixed RGBA
  shell and a sand atlas exported from the approved volume model. Preserve the eight-second drain, one-second smooth
  half-turn, both painted orientations and fixed total sand. Do not restore the legacy `hglas` animation. The shared
  rest layout includes the wider date block, fine divider and centred Exit Rest button.
- The user approved **Carved Obsidian journal revision 01** (2026-09-28): map, quests, story and all six
  autonote categories using references 2091–2094, plus the separate 2090 status-strip treatment. Start with the
  [approved journal design](../../level_generation/ui/obsidian_journal_20260928/README.md) and its
  [staged integration package](../../level_generation/ui/obsidian_journal_20260928/staging/README.md).
  It preserves the approved art, native map viewport and reading fonts, Fondamento button states and journal YAML.
  The subsequent text refinement uses justified quest/story/autonote paragraphs with left-aligned final lines;
  native glyph metrics, paragraph endings and pagination remain authoritative in the shared renderer.
  See the [native integration record](../../level_generation/ui/obsidian_engine_handoff_20260928/NATIVE_INTEGRATION.md)
  and its GPU capture gallery for current implementation and checks. Android uses the shared desktop layout plus
  the [remaining-UI follow-up](../../level_generation/ui/obsidian_remaining_20260929/README.md)'s `touch_controls.yml`.
  The user approved this final Android arrangement on 2026-09-29; use its
  [approved captures](../../level_generation/ui/obsidian_remaining_20260929/README.md#latest-approved-android-layout)
  as the current baseline.
  Preserve large thumb controls: Attack/Spell side by side with attached Quick Cast. The lower-left controls are
  one vertical column, bottom to top Turn Mode, Inventory, Inspect, with 80-unit buttons and eight-unit gaps.
  This column stays beside the party at 4:3. Groups lift above the dynamic party frame only when they overlap it;
  do not restore small controls against the screen edges. The Android context popup belongs immediately above
  the right-hand Attack/Spell pair, clears Quick Cast and follows that group's party-frame displacement.
  The right group uses a 1024-wide scale reference (about 6% smaller at 2:1) to stay beside the full party bar;
  wider phones retain full size. The left group retains its 965-wide reference. Flight arrows are visible and
  touchable only outdoors with the Fly party buff active, or while the party is on an indoor ladder.
  This follow-up also installs Obsidian Lloyd's Beacon,
  jewelry/magnifier, context illustrations and teleport Close buttons, and removes the legacy shop frame fallback.
  Spellbook art remains intentional. Preserve the separate menu implementation when revisiting gameplay UI.

- The user approved **Carved Obsidian menus revision 03** (2026-09-28), including main/pause, save/load,
  continent/party creation, Settings, keyboard and credits. Start with the
  [approved menu study](../../level_generation/ui/menu_study_20260928/README.md) and its
  [runtime staging bundle](../../level_generation/ui/menu_study_20260928/runtime_stage/README.md).
  It preserves blank graphics, Fondamento/Arrus/Lucida fonts, layout YAML drafts and integration contracts.
  This is an approved design handoff; native menu activation remains separate work.
- The party creation screen is the user-chosen **C2** layout (2026-11-01): a roster rail, an identity/attributes/race
  strip, the learnable skills in three columns coloured by best mastery (grey Normal, white Expert, turquoise Master,
  gold Grandmaster) and a full-height paperdoll, with portrait/voice/class pickers, a mastery table and a party board;
  no skill planner. Start with the [party creation study](../../level_generation/ui/party_creation_study_20261101/README.md)
  and its native implementation notes.
- Potions and scrolls in play: the [basebar popups](../../level_generation/ui/potion_scroll_popups_20261102/README.md)
  (2026-11-02): the frame's end ornaments carry carved sockets (socket v2), whose scroll (left) and potion (right)
  buttons open paused lists of what the party carries. The per-portrait quick item rings of the earlier radial study
  are a setting, off by default.
