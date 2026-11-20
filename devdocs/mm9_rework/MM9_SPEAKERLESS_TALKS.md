# MM9 talks opened without a speaker (audit 2026-11-08)

`MM9.openRude(id)` without an actor index gives the talk a speaker only from the hook context: the clicked actor
(use event 53000–55999 = 53000 + DAT object, so 54xxx handlers are clicks too), the found-player actor (56000–58999)
or the actor whose exit is running (50000–52999). Opened from anything else (a timer, a cinematic step, a face or
trigger event) the talk has no speaker and its close skips the speaker's exit (`executeMm9RudeExitCallback`).

Scope: all 254 speakerless `MM9.openRude` calls in `assets_dev/worlds/mm9/events/maps/*.lua`. 235 sit in a click or
found-player handler of the actor whose RUDE they open (scene `mm9_source_object_index` + `mm9_rude_id` checked).
The approach talks of Thorolf (NPC378, every city) and Forad (Frosgard) are not in the list: their `talk`
functions already pass the actor. The rest:

| Map:line | RUDE | Opened from | Speaker (map actor) | Exit handler | Verdict | Fix / verified |
|---|---|---|---|---|---|---|
| thronheimcity:146 | 1 | timer 36040 (ARG_Yrsa.scr :OnAppear after the council) | 42 Yrsa the Troll (src 230) | 50230: quest done, key 185, she vanishes | **BUG** | `mm9r_thronheimcity/council.py` `extra_lua()`: `MM9.openRude(1, {yrsa})`. Scenario `tests/scenarios/mm9/speaker_timer_talk_runs_exit.yml` (fails before, passes after) |
| frosgardcity:55 | 206 | `bankDialogue()` from event 231 (Bankdoor hatch OpenTrigger, NPC206.scr/BankOrb.inc) | 7 the banker (src 553) | 50553: shuts the hatch, takes key 330, with 333 installs the Orb of Linking (item 252, key 327, six orbs: 337 + reward) | **BUG** | `mm9r_frosgardcity/citylua.py`: `MM9.openRude(206, {a['Banker']})`. Scratch scenario (event 231, cancel, key 330 taken, BankOpen 0): fails before, passes after |
| drangheimcity:122,127; frosgardcity:234,239,244; guberlandcity:193,198; sturmfordcity:181,186; thjorgardcity:199,204; thronheimcity:242,247 | 378 | Thorolf's own exit (NPC378.scr: with 83/106 the talk reopens) | the same Thorolf (hook) | his exit again | HARMLESS | — (intended: the talk cannot be skipped) |
| drangheimprison:142 | 90 | Ivsar's exit 50068 (reopens while 194 without 242) | 41 Ivsar (hook) | 50068 again | HARMLESS | — |
| afterworld:131 | 432 | `skraelosExit()` in 50094 (:Questioner) | Skraelos (hook); the Questioner has no actor | 50094: "Questioned" reset, next fire | HARMLESS | — (by design: the Questioner's close re-runs Skraelos' exit) |
| drangheim:57 | 90 | `ivsarUse()` from 53024/56024, 53114/56114 | 33 / 38 Ivsar (hook) | 50024 / 50114 | HARMLESS | — |
| yanmirsfort:315 | 433 | `rescue()` from clicks 53618–53624 | 64–70 children (hook) | none | HARMLESS | — |

Candidates named in the request that turned out to be clicks of their own speaker (HARMLESS): drangheimprison 155/162/169
(431, prisoners 64–66, 54067–54069, no exit), sturmfordcity 155 (425, guard 43, 54323; exit 51323 checked headless:
key 5008 taken), thjoradmine 830–833 (54396–54399, actors 42–45), thjorgardcity 95/142/160 (54048/54098/54077,
actors 3/50/32), frosgardcity 133/145/207, afterworld 99/104 (53094/56094).

Totals: 2 BUG (fixed), 17 HARMLESS outside click handlers (+235 in click/found handlers), 0 UNCLEAR.
