# D-165 to D-169: GitHub issue #45 (decider, 2026-11-25)

A player's issue (https://github.com/pjasicek/openyamm/issues/45) was investigated by agents; the design calls below went
to a read-only decider. Findings that were plain bugs (Xeen exits hidden behind rock in v3.0/v3.1, fixed in v3.2; the
recruit portrait off-by-one in `tools/xeen/gen_towns.py`) needed no ruling.

## D-165 Xeen house greeting voices (Q3)

DECISION: replace the single voice per kind in `gen_towns.py` KINDS with a male and a female stock MM6–MM8 voice per kind.
A voice's sex is read from the proprietor portrait the engine's `assets_dev/engine/data_tables/house_animations.txt`
pairs with that sound base (the person speaking it). The owner's sex comes from the roster `face` where there is one,
otherwise from a new `sex:` field on the owner row in the town YAML. Where a kind has no voice of the owner's sex, write
0 (silent). WHY: a male greeting from a female proprietor is plainly broken; D-38's stock greetings are kept; the
portrait pairing settles what a pitch test could not. WHO ACTS: towns lane (`gen_towns.py` ~40 lines, `sex:` on owners,
rebuild). REVERSIBLE: yes. CONFIDENCE: medium (some kinds may end up silent).

## D-166 DD-01's sluice is hinted and visible (Q4)

DECISION: (1) the flooded water's click names the sluice house as a status line (D-90): "The culvert to the Rat Queen's
den is flooded. Its sluice is worked from the sluice house, at the far north-west of the upper level." (2) Valio's
Rats topic says the same; Felix's greeting stays. (3) The 8×8×32 post becomes a lit sluice wheel or lever about twice the
standard size against the sluice house wall, a lamp near it, titled "Sluice". (4) A `pose()` + `interact()` playtest
step: from the sluice house door the wheel is pickable within 512, the culvert drains, the den is reachable. Felix gets
a body if an existing peaceful indoor body fits (dd06/dd14/xd22 pattern). No grate or water front on the culvert mouth.
WHY: the no-riddles rule needs the answer stated plainly; naming the place twice and a visible control is the simple
MM fix. WHO ACTS: DD-01 lane (`dd01/gen.py`, `dress.py`), quests (Valio). REVERSIBLE: yes. CONFIDENCE: high.

## D-167 Q-C17 wand and Q-C20 whistle made findable (Q5)

DECISION: the wand sits in a large, clear sprite-nest prop (woven twigs with a glint) at the centre of the sprites'
woods, replacing the small "Sprite eggs" mushroom; still a cursor find (D-93). The whistle lies as a visible ground item
in Pitchfork Creek's shallows upstream of the bridge, west of town (D-93: items in the open are ground items; give an
`in_the_open:` reason if `quests.py`'s 0.6-cell check refuses it). Danulf, Orothin and the journal name each spot. A test
picks each from standing eye height within 512 (D-153) from at least two directions. No Sprite Queen row. WHY: quest
items must be findable (a chest, a visible item, a named boss), never hidden. WHO ACTS: X2 lane (`x2/gen.py:1473`), X1
lane (`x1/gen.py:1621-1625`), quests (q-c17, q-c20 lines and journal). REVERSIBLE: yes. CONFIDENCE: high.

## D-168 Vertigo's "pests" (Q6)

DECISION: no hostiles in Vertigo's streets (D-1.3's town buffer, the arrival rules D-133/D-136, MM6–MM8 safe towns,
D-96's villagers). Gunther's line in `source/quests/m1.yml:35` points at the source, e.g. "Pests are pouring out of
Joe's warehouse and into my streets. Clear it out." (D-78 makes M1 the warehouse cleanup). WHO ACTS: quests (m1.yml and
its translations). REVERSIBLE: yes. CONFIDENCE: medium (rules against the player's request on convention; the
alternative would be a few melee pests at the warehouse door under D-136, not in the streets).

## D-169 Darkside sky colour (Q7)

DECISION: keep amber days and day/night (STORY_AND_ATMOSPHERE F1) and the three-stage failing sun; push the `_fading`
and `_failing` presets toward ember red-orange so the sky reddens as the sun fails. `xeen_darkside_day` stays (also used
by DD-22, D-67, and DD-23, D-45). WHO ACTS: sky lane (two presets, a capture of each stage on D1). REVERSIBLE: yes.
CONFIDENCE: medium (WORLD_DESIGN §1.2 keeps this an assumption the owner may change).
