# Screenshots to recapture

The old guide's screenshots (2026-10-25) that no longer match the game were left out of `img/`. Capture these with the
engine-native screenshot (`./tools/run_game.sh --isolated <name> ... --set debug.screenshot_path=...`) on a MAW save
with a five-member party, 1600×900 or larger, then add them to the fragment named.

| Want | Why the old one is stale | Fragment | Suggestion |
| --- | --- | --- | --- |
| Gameplay HUD: split arcs, reserved hatching, Assassin rubies, Elementalist gems, map progress bar, potion and scroll sockets on the basebar ornaments | Old `hud_gameplay.jpg`, `arcs.jpg`, `combo.jpg` show the per-portrait potion-ring buttons (now off by default) and the plain end ornaments | tips (Portraits, Potions and scrolls) | Ravenshore (out02.odm) outdoors, a party with an Assassin and an Elementalist mid-fight, two auras held; crop the basebar for a second image |
| Map progress bar with the red 65 % mark | Old `progress.jpg` shows the ring buttons | tips (Map progress bar) | Nightmare save in a dungeon (e.g. Goblinwatch 6d01.blv) at ~30 % cleared |
| Potion popup open | Old `potion.jpg` shows the potion ring | tips (Potions and scrolls) | Any outdoor map, V pressed, hover a Cure Wounds row |
| Stats page with coloured stat names, Power/Vitality rows and resistance cuts | Old `stats.jpg`, `stats_page_newclass.jpg` predate the coloured stats and the armour/resistance divisors of MAW 8fbb48d1 (the percentages changed) | tips (Character screen), combat | A level-100 Champion and a new-class member |
| Journal Notes › Trainers finder with a trainer's map open | Did not exist | tips (Journal), teachers page | Any MAW save with the Ledger of Teachers bought |
| Party creation class grid and class description | Old `party_creation_classes.jpg`, `class_description.jpg`, `classes.jpg` show the pre-C2 party creation screen | classes | New Game → MAW → party creation, one of the new classes selected |
| Skills page with "N pts" costs and the Cover/Mana Shield toggles | Old `skills_page.jpg` not checked against the current skills page | tips or classes | A Knight with Cover and a caster with Mana Shield |
