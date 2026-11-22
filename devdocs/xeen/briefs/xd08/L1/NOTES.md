# XD-08 Tomb of a Thousand Terrors: handover notes (no level written yet)

**Superseded 2026-11-20: the map is built to L4; see `../L4/NOTES.md`.** The facts below were the starting point.

`agent:xeen-a7-xd08` (lane A7), 2026-11-20. Stopped on the lane lead's handover order **before any project file was
written**: no L1-L4 project, no `output/studio_cal/xd08/` folder, no scratch root, nothing built or installed. This
file is the only output. A fresh session starts the route from L1.

## Where it stands

The reading is done (common brief `output/studio_cal/a7/phase2_common.md`, lanes README, ROADMAP §5.1-5.2, the graph
and its section, D-4, DECISIONS D-7.x, DRESSING.md, ACT2_BUILD, XD-07's generator and NOTES, XD-04's cage and hoist
movers). The findings below save the next session that reading.

## Next steps for a fresh session

1. Copy the route of XD-07: `output/studio_cal/xd07/tools/gen.py` (one script writes L1-L4: ROOMS, THEMES, OPENINGS,
   WALLS, PILLARS, PLATFORMS, objects, wiring, project, plan, diagram), `cycle.sh`, `play.sh`, `four.sh`, `tour.sh`,
   `tools/sheet.py`. Make `output/studio_cal/xd08/tools/gen.py` with key `xd08`, stem `xeen_xd08`, map_stats 9124,
   music 20, `world: xeen`, profile dungeon, treasure 2.
2. Scratch root as the common brief says (`cp -al assets_dev output/studio_cal/xd08/root`, real copies of
   `worlds/xeen/maps` and `worlds/xeen/events/maps`), plus REAL copies (not hard links) of
   `worlds/xeen/data_tables/map_stats.txt` and `bolster_maps.txt` with a test row 9124 (as XD-07/XD-25 did).
3. L1/L2 (plan), L3 (rooms), L4 (objects, wiring, playtest.yml, playtest_hostility.yml, NOTES.md), then cycle
   (fmt, validate, build, install into the scratch root, `audit --reach --solve`), playtests 4 of 4, a tour, fix,
   texture budget (`tools/xeen/texture_budget.py --root <root> --map xeen_xd08.blv`), report.

## Facts gathered

**Ids.** Map qbits 110760-110799 (e.g. `manacles_pulled` 110760). Player bits 11270-11276, one per juice colour
(red, blue, orange, green, yellow, purple, white), once per character. A3's bit `tomb_credits` 111201 is set by the hook.

**Hooks (A3, `source/quests/m10.yml`).** `m10.tomb_welcome` (statue plaque, text "A plaque at the base of the statue
reads: Welcome ... undead is our game."); `m10.tomb_vault` (once; sets 111201, 2,500 xp, text "King's Megacredit! ...",
else "The coffin is empty."; `map_gives: {megacredit: 5}`, so **the map puts five 12192 in the coffin**, as XD-06's
`chest:treasury` does: a chest with `items: [megacredit x5]` and `project.yml items: {megacredit: 12192}`, its event
the `chest` preset with `effects: [{lua: 'XeenQuests.hook("m10.tomb_vault")'}]`). `m10.tomb_door` is X3's, not ours.

**Might check (D-4.5).** Condition `stat: {name: ActualMight, at_least: 30}` (ActualMight counts potions and spells;
selectors listed by `oymap script-reference --assets assets_dev --world xeen`). The great coffin's event: condition the
stat, else "You are not strong enough to open the coffin." (aaze0080:10). Barracks chest: two fixed **Might Boost**
(engine item 240; XD-10 plans the same item), `random_items` as T2. A "potion" here is an existing engine row, not a
new item (U-1). Open: what potency a chest's fixed potion gets, and whether +3x potency reaches 30 for a level-15
non-knight; the playtest can `console` the stat or drink the potion. If the coffin is a chest, check whether a chest
event's condition can gate opening (XD-07's `chest:roxanne` does exactly that with a qbit).

**Monsters (A2, `source/monsters.yml`), band 15-30.** Slot `Xeen Zombie` (Rotting dead: C Grave Ghoul 18);
`Xeen Spirit` (Spirits: A Polter-Fool 18, B Tomb Guard 26; C Tomb Terror 40 left out, D-4.1); `Xeen Skeleton`
(C Skeleton Lord 16) fits the ossuary's "bone piles that rise". Spawn markers carry fixed tiers (`tier: a/b/c`).
Slot lines for A2 in the `map_rows.yml` form `{family: rotting_dead, tier: N, count: [2, 3], weight: W}`.
50 monsters in 22 rooms per the graph's populations; Hall of a Thousand Terrors: Tomb Guards.

**Cage lift (D-4.4).** XD-04's `mover:hoist` (objects.yml `movers`, `parts` ride with it, `state: end` starts at the
top, `toggles`/`opens`/`closes` move it, door_state "open" = at the end) and its cages (`xwcage` see-through bar panels
8 thick as parts, `xwiron` lid and an 8x8 chain part). Plan: a shaft room (cage size, so no gap) from the cage pit's
floor -640 up past the cage room's floor 0, an opening to the cage room at the top and one to the cage pit at the
bottom on the opposite wall, the mover's floor filling the shaft, bars as parts on the two closed sides, the chain
as a part (click the mover: ride), call buttons at both ends. The shaft is one more sector (23 with the graph's 22).

**Other set pieces.** Manacles: a `switch` (lever kind) on the chain room's wall that `opens` the portcullis door
640 below (`slide_up`, `xkportc` as XD-07), text "Far below, iron grinds upward."; the portcullis's own event refuses
until the qbit. Iron maiden: a secret door (`secret: true`, XD-04's loose panel) on the niche's back wall in `xwiron`,
its plaque (a `sign128` panel) naming it; behind it the maiden's stair (a sloped room, 20 risers of 32, XD-07's
stair rooms). Stocks: wooden platform blocks with skeleton decorations, a T2 chest under the last. Coffins and biers:
platform blocks; the west hall's coffins say "The coffin is empty." (aaze0080:1). Juices: seven basin platforms with a
liquid top, each event `condition: {not: {player_bit: 1127N}}`, effects `player_bit`, `add BaseX 2`, message "Red Tomb
Juice. +2 Might (permanent)." etc. (aaze0080:2-8), else "The liquid is powerless." (aaze0080:9). Exit to X3 at the
tomb door: sealed with a message ("Leave the Tomb of a Thousand Terrors?" is aaze0080:24), start inside it.

**Decorations that fit** (engine `decoration_data.txt`): `torskul0` skull torch, `sklabra0` candelabra of skulls,
`sklspear` skulls on spears, `sklplrev` skull pile, `7dec18`/`dec19` bones, `7dec20` skull, `dec05` skeleton,
`Corpse*`, `noose`, `Bonecage`, `hngncge2` hanging cage, `sta1a`/`7dec54`/`7dec55` statues, `urn`/`tcurn`,
`brazir2f`/`brzier00`, `torch01`. Containers (barracks clump, a storeroom of 8+): `bigbarel`, `smlbarel`, `7dec32`,
`bag01`, `floursac`, `7dec21`.

**Textures (cap M 45 distinct, at most 8 new).** XD-06's crypt family is the nearest shipped kit: MM7 Barrow I (mdt03)
`t5bs` walls, `t2bs` floor, `t4bs` ceiling, `hwp1b` dressed crypt wall, `t5d1` iron doors; MM7 Temple of Baa (d04)
`t6s1bs`, `t6s1fl`, `t6s1c`, `t6s1b` skull frieze, `t4s1fl` green-black slabs for the tomb proper; cave rock for the
deep (`gcav1flr`/`gcav2flr` or `t5bs`); A6's `xwcage`, `xwiron`, `xkportc`, `sign128`. One family per area: tomb
(Baa set + skull frieze), torture rooms (iron and `t5d1`), crypts (Barrow), the deep (rock).

## DECIDE (none raised yet)

## Open issues

- See-through door leaves show pink speckles in the current game build (known, reported to A1).
