#!/usr/bin/env python3
"""The phase 3 review board of D2 Sprite Forest and Ogre Pass (A6): one HTML page with the MU-3 plan, the two MU-4
concepts, the counts against MAPS, A3's hooks, A4's houses and the open questions; rendered to one PNG with headless
Chrome (its own profile under d2/.chrome, removed after the run).

    board_d2.py         -> d2/board_d2.html, d2/board_d2.png   (run d2_render.py and d2_counts.py first)
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True   # nothing written into phase2/ (shared)
sys.path.insert(0, str(HERE.parent / 'phase2'))
import board as base  # noqa: E402

OUT = HERE / 'd2'
PROFILE = OUT / '.chrome'
EXTRA_CSS = """
.q li { margin: 6px 0; } .q b { color: #5a2a08; }
td.c { white-space: nowrap; }
"""


def page(counts, arrival, signature):
    ff = counts['first_fight']
    west = ff['entrance:west_road'][0][0]
    east = ff['entrance:east_road'][0][0]
    quiet = round(counts['quiet_share'] * 100)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>D2 Sprite Forest: mock-ups</title>
<style>{base.CSS}{EXTRA_CSS}</style></head><body><main>
<h1>D2 Sprite Forest and Ogre Pass: MU-3 plan and MU-4 concepts</h1>
<div class="sub">Phase 3 review (A6, 2026-11-20), for a decider before any geometry. Darkside's south centre, Act III
(party 21-25): the Gemstone Range walls the north; a spur of it crosses the middle, and the caravan road from Castleview
to Sandcaster climbs over it at <b>Ogre Pass</b> between Graalg's two timber forts. South of the road the
<b>Sprite Forest</b> runs to the world's rim: glowing caps, the <b>great tree of Bark</b> (DD-09) at its heart with
Nibbler's hollow at its roots, Sharla's treehouse village beside it, troll country with three holes (DD-11A-C), and the
Glimmerbrook falling off the edge into the stars. East of the spur, the <b>Southern Tower</b> (DD-06) stands in darker
woods. Source: <code>devdocs/xeen/briefs/d2/L1/</code> (project, plan, sketch: Map Studio's schema,
<code>oymap validate</code> and <code>oymap call check.validate</code> clean).</div>
<div class="grid">
<div>
 <div class="card plan"><img src="plan_d2.svg"></div>
 <div class="card" style="margin-top:12px">{base.LEGEND}
 <div style="margin-top:6px;color:#5d5a55;font-size:13px">128 x 128 cells of 512 units, north up; the dashed white
 square is the playable area (cells 19-109). South the land ends in a cliff above the stars at y 106; north the range
 closes the map (D5's desert beyond, no edge). <b>Shared edges:</b> the Castleview road crosses x 0 at <b>y 60</b> (fixed
 with D1); the caravan road crosses x 127 at <b>y 44</b> (proposed to A5 for D3). Violet: wild sprites; red: wolves,
 trolls; dashed orange: the ogres' placed area.</div></div>
 <div class="two" style="margin-top:12px">
 <div class="card inset"><h2 style="margin-top:0">Sharla's village and the great tree (3x)</h2>
  <img src="plan_d2.svg#svgView(viewBox(130,530,260,270))">
  <p style="font-size:13px;color:#5d5a55">A4's d2.yml: Sharla's Treehouse 4553 (q-d10's chest on her platform),
  the Light Guild of the Treetops 4552, Dewdrop Potions 4551, Mossbell's Bower 4554, Thistledown's Bower 4555, doors
  at the trunks' feet round a mossy green, 3-5 cells apart; 8 peaceful sprites. Bark Glade: the temple door in the
  trunk (q-d9.bark_door), Nibbler's Hollow 4556 under a root 4 cells away ("Nibbler sits nearby").</p></div>
 <div class="card inset"><h2 style="margin-top:0">Ogre Pass (2x)</h2>
  <img src="plan_d2.svg#svgView(viewBox(440,200,400,250))">
  <p style="font-size:13px;color:#5d5a55">The road climbs from 1,100 to the saddle at 2,050 between spur crests of
  3,100. West fort on its knoll north of the road at the west mouth, east fort south of it beyond the saddle (DD-13's
  two entrances). Graalg (5108) at the parley fire with two Brutes, peaceful; 22 ogres placed in the yards and two road
  groups. Kramer's burned wagon below the west fort.</p></div>
 </div>
</div>
<div>
 <div class="card concept"><h2 style="margin-top:0">MU-4 arrival view (from D1)</h2>
  <img src="{arrival}">
  <p>Camera at cell (21, 60), 180 above the road, looking east-south-east. The Castleview road reaches Forest Fork:
  the caravan road climbs left toward the foothills, the forest track bends right into the Sprite Forest under old
  dark trees and glowing caps; the great tree of Bark rises far over the canopy. Codex, from the plan's blockout
  (<code>blockout_arrival.png</code>).</p></div>
 <div class="card concept"><h2>MU-4 signature view: Ogre Pass</h2>
  <img src="{signature}">
  <p>Camera at cell (60, 44) on the caravan road below the pass, looking east up to the saddle: the west fort on its
  knoll, Graalg's fire in the saddle, the east fort beyond, the crystal-veined Gemstone Range behind. <b>Why this
  view:</b> the painting softens the spur's shoulders and brings the east fort level with the saddle; the plan's 3,100 crests and the fort beyond the saddle stand. The arrival already shows the forest and the great tree; the pass is the map's second biome, its
  gauntlet (both routes of Q-D11 are on screen) and the only view that shows the range that closes the map. The
  village's form waits on the treehouse question below, so painting it now would fix a form not yet chosen.</p></div>
 <div class="card"><h2 style="margin-top:0">Against MAPS (D2 sheet) and ROADMAP 5.1</h2>
 <table>
 <tr><th>Figure</th><th class="n">Plan</th><th>Target</th><th></th></tr>
 <tr><td>Hostiles at load</td><td class="n">135</td><td>135</td><td class="ok">ok</td></tr>
 <tr><td>Encounter areas</td><td class="n">5</td><td>3-8</td><td class="ok">ok</td></tr>
 <tr><td>Spawn markers (+ placed hostiles)</td><td class="n">{counts['markers']} (+{counts['placed_hostile']})</td><td>45-70</td><td class="ok">ok</td></tr>
 <tr><td>Quiet land (outside encounter areas)</td><td class="n">{quiet} %</td><td>at least a third</td><td class="ok">ok</td></tr>
 <tr><td>Points of interest (chained merge within 400, D-15)</td><td class="n">{counts['poi_spots']}</td><td>forest band 22-30</td><td class="warn">top</td></tr>
 <tr><td>Named / generic</td><td class="n">20 / 10</td><td>16 named + 6-14</td><td class="ok">ok</td></tr>
 <tr><td>Outdoor chests, each with a reason</td><td class="n">6</td><td>4-10</td><td class="ok">ok</td></tr>
 <tr><td>Dungeon entrances</td><td class="n">8 (5 dungeons)</td><td>MAPS: 5 dungeons</td><td class="ok">ok</td></tr>
 <tr><td>Relief</td><td class="n">900-3,400 in the square, range 4,400</td><td>at least 2,500</td><td class="ok">ok</td></tr>
 <tr><td>First fight from the D1 arrival</td><td class="n">{west:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>First fight from the D3 arrival</td><td class="n">{east:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>Houses drawn / d2.yml</td><td class="n">6 / 6</td><td>4551-4556</td><td class="ok">ok</td></tr>
 <tr><td>Obelisk; permanent-effect devices</td><td class="n">1; Shrine of the Elements, Forbidden Fruit</td><td>1; at least 1</td><td class="ok">ok</td></tr>
 </table></div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">Encounter areas</h2>
 <table>
 <tr><th>Area</th><th>Monsters (A2's rows)</th><th class="n">At load</th></tr>
 <tr><td>E1 Gemstone foothills</td><td>Dark Wolves 16, Sabertooths 22; Snow Beasts 28 only on the upper slopes</td><td class="n">30</td></tr>
 <tr><td>E2 sprites (west glades, Whispering Glades)</td><td>Medusa Sprites 10, Killer Sprites 14, a Sprite Queen 18 (wild)</td><td class="n">24</td></tr>
 <tr><td>E3 Troll country</td><td>Trolls 18, Troll Guards 28, Ice Trolls 38 only by the third hole</td><td class="n">30</td></tr>
 <tr><td>E4 Ogre Pass (placed)</td><td>Ogres 18, Brutes 22, two Chiefs 30; peaceful once q-d11.friends</td><td class="n">22</td></tr>
 <tr><td>E5 Southern Woods</td><td>Dark Wolves 16, Sabertooths 22</td><td class="n">29</td></tr>
 <tr><td colspan="2">Peaceful at load: 8 village sprites (hostile on q-d10.robbery); Graalg 36 and two Brutes</td><td class="n">(11)</td></tr>
 </table></div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">A3's hooks on D2</h2>
 <table>
 <tr><th>Hook</th><th>Where</th><th>State</th></tr>
 <tr><td class="c">obelisks.d2</td><td>Obelisk on the foothill knoll (36, 51): BENEATH</td><td class="ok">placed</td></tr>
 <tr><td class="c">q-d9.bark_door</td><td>Door in the great tree's trunk (42, 76), needs bark_key 12342; Nibbler's Hollow 4 cells off</td><td class="ok">placed</td></tr>
 <tr><td class="c">q-d10.sprites_hostile</td><td>The village's 8 sprites, peaceful; hostile on robbery 113203</td><td class="ok">placed</td></tr>
 <tr><td class="c">q-d10.sprites_slain</td><td>The same group: the map sets 113208 when the last dies (an L4 event)</td><td class="ok">placed</td></tr>
 <tr><td class="c">q-d10.treehouse</td><td>The chest on Sharla's platform (26, 85)</td><td class="ok">placed</td></tr>
 <tr><td class="c">q-d11.pass_ogres</td><td>Graalg 5108 at the parley fire (79, 36), 22 placed ogres; reads hostile, west_burned, east_burned</td><td class="warn">placed; hostility at load: question 2</td></tr>
 <tr><td class="c">q-d13.troll_holes</td><td>Three pits: DD-11A (60, 76), B (70, 84), C (67, 98)</td><td class="ok">placed</td></tr>
 <tr><td class="c">q-d19.tower_door</td><td>The Southern Tower's door (95, 80), needs south_tower_key 12339</td><td class="ok">placed</td></tr>
 <tr><td class="c">(DD-13, DD-10B)</td><td>Fort gates (72, 36) and (87, 43); the mines' east adit (34, 31)</td><td class="ok">placed</td></tr>
 </table></div>
 <div class="card q" style="margin-top:12px"><h2 style="margin-top:0">Open questions</h2>
 <ol>
 <li><b>How are the treehouses and the great tree built?</b> (a) giant hollow trunks as round BModel parts (bark
 texture), doors at their feet, decks, stairs and rope walkways from the studio's structures, crowns of shipped tree
 models on top; the great tree the same at 3 cells across with a new crown model; (b) new giant-tree GLBs (S lane)
 with BModel door facades; (c) doors up on platforms reached by stairs. Proposed: (a), doors at the foot (nothing
 to climb to a shop), Sharla's stair only to the chest.</li>
 <li><b>Graalg's ogres at load.</b> (a) hostile, as MAPS ("peaceful if Q-D11"), counted in the 135, Graalg and his
 guards peaceful at the parley ground; (b) neutral until attacked (then 22 short: 9 more markers elsewhere).
 Proposed: (a).</li>
 <li><b>Sprites below the band.</b> The sprite family is 10/14/18, D2's band A 16-22: (a) keep (24 of 135, the
 forest's colour); (b) A2 adds a D2 tier (16/22); (c) swap the wild sprites for an in-band family. Proposed: (a).</li>
 <li><b>Monga melons.</b> MAPS lists them on D2; q-d9 puts all four on D1 (the source's A4/B4). Plan: none on D2,
 Nibbler's own patch as dressing after q-d9.done.</li>
 <li><b>The river.</b> MU-1 paints a river through D1, D2 and D3; the D1 sketch has one on D1's south. D2's
 Glimmerbrook rises inside and falls off the rim; if D1 runs its river to its east edge, D2 takes it in at y 96-100.</li>
 <li><b>Burned forts outside.</b> Show the forts as charred ruins after q-d11's burned bits (a model swap by qbit),
 or leave them unchanged outside?</li>
 </ol></div>
</div></div></main></body></html>"""


def main():
    counts = json.loads((OUT / 'counts.json').read_text())
    raws = sorted((OUT / 'raw').glob('d2_*_v*.png'))
    pick = {}
    for path in raws:
        view = path.stem.split('_')[1]
        pick[view] = f'raw/{path.name}'      # the highest version wins
    html = page(counts, pick.get('arrival', 'blockout_arrival.png'), pick.get('pass', 'blockout_pass.png'))
    (OUT / 'board_d2.html').write_text(html)
    try:
        subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox',
                        f'--user-data-dir={PROFILE}', '--hide-scrollbars', '--window-size=1800,3820',
                        '--virtual-time-budget=6000', f'--screenshot={OUT / "board_d2.png"}',
                        (OUT / 'board_d2.html').as_uri()], check=True, capture_output=True, timeout=180)
    finally:
        shutil.rmtree(PROFILE, ignore_errors=True)
    print(OUT / 'board_d2.png')


if __name__ == '__main__':
    main()
