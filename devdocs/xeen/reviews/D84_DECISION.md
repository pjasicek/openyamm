# D-84: MAW in Xeen, lane MX's design questions MX-1, 3, 4, 6, 7, 8 (2026-11-21, fourth orchestrator's decider)

Source: `devdocs/maw/XEEN_SUPPORT.md` §9 (MX's D-1..D-8 = MX-1..MX-8). MX-2 (save version 200) and MX-5 (Supreme from
any four of five) change MAW for MM6–MM9 players and went to the user; the decider recommends accepting both.

- **MX-1 Bank:** keep one MAW bank for both faces (continents 6 and 7 share the fifth). A bank per face would scale
  Darkside by the party's own Cloudside levels, which bolster exists to prevent. Nobody acts. Reversible (a sixth saved
  value and another save version).
- **MX-3 D–G picture tiers:** keep each D–G row its own family at tier B; no fourth tier (would touch boss, HP and summon
  code for MM6–MM9). MX adds a `--review` list of D–G rows placed where their stem family is native, with both resolved
  levels; if play shows it matters, a per-world alias in `balance.yml`, not a fourth tier.
- **MX-4 Dungeon density:** MM9's pack reserve for Xeen's 69 dungeons. Now: generalise `mm9_pack_reserve.py` world-neutral
  (MM9's output byte-identical, `mm9_balance.py --check` passes) and add MM9's `density` block to Xeen's balance.yml
  (1.0 / 1.2 / 1.4 / 1.6 / 1.8 / 2.0). Reserves installed in phase 7 or per map once final (a rebuild stales a reserve;
  the game skips a stale one and the check fails). Reserves live in `rulesets/maw/maps/`. *(Orchestrator, 2026-11-21:
  all 82 maps are installed; at the user's question about Beyond Madness the reserves are built now, rerun after any
  map rebuild.)*
- **MX-6 Gem gear:** change: Xeen's own tiers as rungs — Ruby Broadsword 4, Emerald Leather 5, Sapphire Staff 5, Diamond
  Plate 6 (`source/items.yml` `crafted.*.tier`); strength 1.10 for tiers 4–5, 1.15 for the Diamond Plate (MM9's
  figures). MX changes `GEM_GEAR` in `xeen_balance.py`, regenerates `item_bases.yml`.
- **MX-7 MAW's people:** a Seer per face (skill reset, Dimensional Maps): an existing talking NPC at Castle Burlock (X4 or
  XD-07's court; Artemus the Royal Advisor fits) and one in Castleview (D1; Madame Oorla fits): present at every story
  stage, reachable by Town Portal, at most 5 topics after the two MAW topics; not Newcastle, not Psychic Sally, no new
  NPCs. Bounties: nothing new — Vertigo Town Hall (X1) and Castleview Town Hall (D1) are ordinary town halls and already
  offer Bounty Hunt. MX builds the MAW-only `world: xeen` topic patch (events 10010, 10011, 10040) and a MAW scenario
  (both Seers, a bounty at Vertigo and Castleview: spawn, the clear-the-map refusal, the reward). A return pedestal in
  Vertigo is a separate request.
- **MX-8 Bands:** keep MM9's curve, fix two oddities now: (1) one-native maps read 15–20 % low (MAW pins a single native
  to the band's low; the draft put the curve at mid): with one native the band's low equals the curve value, with two
  the mean of low and high does (fixes Castle Xeen 44 < X9/X7 51, DD-14 34 → D5 45 jump, DD-17 51 → D7 67, FD-01 61 <
  planes 70, Dragon Cave 67); (2) X7's `natives` = its three north families (the south orcs pulled halfway, ~25); the
  MAW guide says X7 is an Act V map under MAW. Add a route check to `--review` (story map below the map before it).
  Publish balance.yml v2, rerun `ruleset maplevels`. Aside: MM9's balance.yml probably has the same single-native
  under-read (MM9 balance owner's).
