# Enemy effect icons (2026-11-13)

Icons for the effects on a monster, drawn under its enemy health bar (`EnemyHealthBarRenderer`, setting
Interface > Enemy health bars > Effect icons). Each icon sits on a dark tile with a rim, red for crowd control and gold
for the monster's own buffs. The time already spent is swept clockwise from twelve o'clock as a dark shade, from an
atlas the renderer builds once per session (64 frames). The runtime does not store an effect's full duration, so the
bar runtime (`CombatActorHealthBarRuntime::effectElapsed`) takes the longest time left it has seen since the effect
began, and a recast that adds time starts it again.

`make_icons.py` writes the art. Like the Obsidian party buff icons (`obsidian_overlays_20260928`), each icon is a
glyph-free clip of the restored spellbook art: a polygon keeps the spell's runes out, and the clip is fitted into
128×128. The output goes to `assets_source/engine/icons_x2`. Cook it with `tools/cook_ui_textures.py` (and
`--profile android`). `preview.png` shows each icon at full size, 32 px and 16 px.

| Effect | Icon | Source |
|---|---|---|
| Stunned | `obsidian_debuff_stun` | Stun `sbe01a` |
| Paralyzed | `obsidian_debuff_paralyze` | Paralyze `sbl04a` |
| Charmed / berserk / enslaved / controlled undead | `obsidian_debuff_charm`, `_berserk`, `_enslave`, `_control_undead` | `sbm05a`, `sbm07a`, `sbm11a`, `sbdk06a` |
| Afraid | `obsidian_debuff_fear` | Mass Fear `sbm08a` |
| Slowed | `obsidian_debuff_slow` | Slow `sbe02a` |
| Shrunk | `obsidian_debuff_shrink` | Shrinking Ray `sbdk04a` |
| Dark Grasp | `obsidian_debuff_dark_grasp` | `sbdk08a` |
| Haste, Shield, Stoneskin, Heroism | the existing party buff icons | |
| Bless, Fate, Day of Protection, Hour of Power, Hammerhands, Pain Reflection | `obsidian_buff_sbs02a`, `sbs03a`, `sbl08a`, `sbl09a`, `sbb07a`, `sbdk07a` | the same spells |

Blindness and Armor Halved have no icon: the actor inspect state does not carry them.

To put effects on a monster for a capture, use the debug console: `actor cast <index|last> <spell-id> [skill]
[mastery]`. It goes through the ruleset's crowd control.
