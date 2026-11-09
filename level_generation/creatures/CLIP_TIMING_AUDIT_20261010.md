# MM6 3D creature clip timing audit (2026-10-10)

Context: the engine's `animation.events` (actors.yml) let a marked attack/ranged/cast clip run its wind-up
`[0, impact]` over the native action and play the rest as follow-through. Unmarked attack clips play in real time
and are cut when the native action ends. An unmarked cast clip is stretched or squeezed whole over the cast action.
Hit is cut at the native length. A death clip longer than the native death plays to its end, and (since this audit)
so does a longer fidget while the actor stands (`WorldFxSystem`, regression
`mm6_skeleton_actor_fidget_clip_plays_past_the_native_fidget`).

## Outcome (2026-10-10, same day)

| model | clips now | markers (actors.yml) | wind-up vs native 0.75 s |
|---|---|---|---|
| gob | Attack 1.58 s: 0.3 s ready pause + slash at source speed; Death 1.83 s at source speed | melee 0.729 | 1.03x slower |
| wdm | Attack 1.08 s, Cast 1.29 s (0.15 s pause) at source speed | melee 0.646, ranged 0.646 from the right palm, cast 0.75 | 1.16x slower / 1.0x |
| ttn | Attack 1.33 s (0.35 s guard pause), Ranged 1.46 s (0.2 s pause), Cast 2.25 s (source from frame 18, no idle opening) | melee 0.604, ranged 0.729 from the right palm, cast 0.771 | 1.24x / 1.03x slower, 0.97x |
| pmn2 | Attack = Cast 1.21 s: draw-up at a uniform ~1.3x (was up to 3.3x in the strike) | melee/ranged/cast 0.979, ranged and cast from the staff head | 1.31x faster |
| demon | unchanged authored cast | cast 0.92 | 1.23x faster |

pmn2 cannot reach source speed without cutting the reviewed draw-up behind the head (the source draw-up alone lasts
0.97 s); its timing is now uniform instead. Checks: each project's own audits (pose/stretch/wing/continuity) against
the previous build, contact sheets of every changed clip, MM6 actor regressions 28/28.

Follow-up (user, same day): every death at source speed (presentation only: the AI switches to the corpse at the
native length; the corpse sink starts when the death clip has finished): gua 1.67 s, thf 2.21 s, ttn 2.21 s, wwf
2.88 s, pmn2 1.42 s (clip 9..40; the 0.4 s standing opening stays dropped), ske 2.83 s (2.3 s fall + skull roll),
gob 1.83 s (above). Fidgets at source length now that they play out: bar1 back to its Armed boost 1 (1.0 s), ske
1.21 s. Each project's audits match or beat the previous build.

The tables below are the audit as found.

Speed factor = source seconds / seconds on screen (1.0 = the source's own speed). Native action lengths come from
`sprite_frame_data_common.yml` (`animation_length_raw` x 8 / 128 s); every audited attack is 0.75 s apart from the
werewolf (0.5625) and the sea serpent (1.125).

## Already handled

| model | change | wind-up stretch |
|---|---|---|
| bar1 | 0.4 s ready pause + source attack, `impact 0.683` | 1.10x |
| ske | source speed + 0.2 s ready pause, `impact 0.771` (was 1.7x) | 0.97x |
| cle | other session: 1.42 s clip, `impact 0.75`, `launch_socket Socket_Staff_Head` | 1.0x |

## Sped-up attacks and casts (candidates for an impact marker)

| model | clip | source | factor now | fix |
|---|---|---|---|---|
| ttn | Cast | Mixamo Two Hand Spell Casting, 2.6 s, shipped 2.0 s, squeezed into the 0.75 s cast | **~3.5x** | rebuild at source speed, `cast: {impact, launch_socket: Socket_Palm_Right}` |
| ttn | Ranged | Mixamo 1H Magic Attack, 1.27 s into 0.75 s | **1.69x** | same, `attack_ranged` with palm socket |
| ttn | Attack | Meshy Right Upper Hook, 1.0 s into 0.75 s | 1.33x | source speed + `impact` |
| pmn2 | Attack (Cast is a copy) | Mixamo great_sword_casting strike, about 3.3x inside a 0.75 s clip | **~3.3x in the strike** | rebuild at source speed; `cast`/`attack_ranged` with `launch_socket: Socket_Staff_Head` (as the cleric) |
| wdm | Cast | Mixamo wide_arm_spell_casting, 1.15 s into 0.75 s | 1.53x | source speed, `cast: {impact, launch_socket: Socket_Palm_Right}` |
| wdm | Attack | Mixamo zombie_swipe_attack, 1.10 s into 0.75 s | 1.47x | source speed + `impact` |
| gob | Attack | Meshy SwordSlash, 1.29 s into 0.875 s (cut at 0.75) | 1.48x | source speed + `impact` |
| demon | Cast_FireBolt | procedural, authored 1.0 s, squeezed into 0.75 s | 1.33x | marker only (`cast: {impact, launch_socket: Socket_Palm_Right}`); no rebuild |

The replaced flying-demon v2 (3.2x attack) is no longer installed.

## Fine as they are

- Procedural clips authored at the native length: rat, spi1, bh, bat, bld, cob, rob1, seas, hyd, ooz, ckt, pfem,
  pman, gua attack/hit, thf attack, wwf attack, demon attack/hit/fidget/death. They have no source speed.
- Death clips run faster than their sources: gob 1.5x, gua 1.67x, thf 1.49x, ttn 1.49x, wwf 1.91x, pmn2 1.48x.
  Deaths now play past the native length, so each can return to source speed with a rebuild and no engine change.
  This is optional polish.
- Hit clips run faster than their sources: wwf 1.78x, gob 1.4x, wdm 1.33x. The engine cuts hits at native length,
  so these must stay short.

## Clips cut by the native length

| model | clip | clip s | native s | note |
|---|---|---|---|---|
| wdm | fidget = Flight loop | 3.0 | 0.75 | loop, cut is invisible |
| pmn2 / gua | fidget = Standing | 2.0 / 1.0 | 0.75 | idle loop, cut is invisible |
| rob1, ckt | Fidget | 1.5 | 0.75 | second half never plays; check the cut pose |
| spi1, bld, ske | Fidget | 1.0 | 0.75 | last 0.25 s never plays |
| gob | Attack / Hit | 0.875 / 0.833 | 0.75 | last ~0.1 s cut; the attack rebuild above resolves Attack |

Sockets usable as `launch_socket`: demon, wdm, ttn, gob, pfem and pman palms; pmn2 staff head; rob1 lens; ooz spit;
ckt head. Only the cleric uses one today.
