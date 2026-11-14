# Xeen review: story, atmosphere and the original's touches

Review of 2026-11-13 of the Xeen design (`devdocs/xeen/*.md`) and the six built maps (XD-01 to XD-05, X1; their
`L4` briefs and the installed `output/studio_play/xeen_root/worlds/mm7/events/maps/xeen_*.lua`) against the original
game data in `reference/mm4_5_world_of_xeen/unpacked/` (text: `text/{xeen,dark}/*.txt.json`; a flat dump with one line
per string is in `output/xeen_review/story/alltext.txt`, cited below as `xeen/aaze0028:26` = Clouds map 28, string 26).
Map numbers: Clouds 28 Vertigo, 29 Nightshadow, 30 Rivercity, 31 Asp, 32 Winterkill, 33–41 dwarf mines, 49 Shangri-La,
50 Dragon Cave, 51–54 Witch Tower, 64–66 Castle Burlock; Darkside 29 Castleview, 31 Sandcaster, 33 Lakeside,
35 Necropolis, 37 Olympus, 44 Kalindra dungeon, 49/52 Castle Alamar, 86–88 Pyramid and pods, x129 Clouds of the
Ancients, 2121 Eeried's travel guide.

Only decoded text was searched. Words painted into wall or sign graphics would not show up in it.

## 0. The goblin rules table: not in the original

The user remembered "the table they had in the witch's hut with the three rules for goblins". **It is not in the
original.** The slate in XD-04 reads:

> HOW TO BE A PROPER GOBLIN. 1. Never say please. 2. Never wash. 3. Forget your name. -- In the corner, small and half
> rubbed out, a child has scratched her own name: Rosebud. She has not forgotten it.

It was written for XD-04 L4 (`briefs/xd04/L4/wiring.yml`, the generated texture `xwslate`, NOTES row 2). None of the
85 Clouds or 129 Darkside text files has a goblin rule list or any "rules" sign. What the original does have around
witches and goblins:

| Original text | Where |
| --- | --- |
| "Goblins back to work!" the skull shouts. | Witch Tower 1–4 (`xeen/aaze0051:21`) |
| "You are the fairest one of all," the skull says. / "You are the most beautiful creature in all the land," the skull says. | Witch Tower (`:18`, `:19`): the witches' vanity mirror-skulls |
| "Feed me!" the skull demands. Toss gem? | Witch Tower (`:7`), then skulls selling spells for 5–10 gems (`:8`–`:13`) |
| "Don't forget to use the levitate spell before you enter the cloud world!" the skull says. | Witch Tower (`:20`): the hint that the roof leads up to the clouds |
| A boy crawls out of the cage. "Thanks for getting me out of there," he says. "I thought the witches were going to turn me into a goblin for sure. I want to go home." | Witch Tower (`:3`) |
| "...one of the doors needs a password ..." He lowers his voice and whispers "It's Rosebud!" | Witch Tower (`:4`) |
| "The witches only turn CHILDREN into goblins. As long as you leave the kids behind, you'll have no problem at all with these charming and fun-loving ladies." | Eeried's guide, about Lakeside (`dark/aaze2121:5`) |
| "Oh, thank you for rescuing me! The witches were going to use me for spare parts in their potions." | Lakeside prisoner (`dark/aaze0033:27`) |

Proposal: keep the slate (it is in the original's spirit and the user liked it), but record in XD-04 NOTES that it
is ours, and add the real lines next to it. The "Goblins back to work!" skull belongs over the goblin pens. The vanity
skulls belong in the coven's bedchamber. The levitate skull goes on the roof stair, where it now hints at X8.

## 1. Ranked findings

### F1. "Perpetual dusk" on Darkside contradicts the original (high)

WORLD_DESIGN §4 and PRODUCTION E8 make the Darkside a world where "the sun never rises above the rim". The source has
day and night there, and the story depends on them:

- Blackfang dungeon diary: "we must remain inside the castle 'til nightfall or she would surely die once we brought her
  into the light" (`dark/aaze0045:4`). The vampire Queen's rescue only works with daylight.
- "I haven't seen the sun in days!" (rescued sprite, `dark/aaze0073:5`); "Get yer sun dried iguana innards"
  (`dark/aaze0019:3`); a navigator teaches "how to read the sun and the stars" (`dark/aaze0031:7`).
- The Pharaoh: "The Sun grows more distant by the day, and our lives grow shorter" (`dark/aaze0086:12`); "Already the
  Sun diminishes in strength as Alamar directs Xeen to the stars" (`:34`).
- The graphics have a Darkside day sky (`sprites/dark/sky.sky`: amber/orange cloud band, where Clouds' `sky.sky` is
  blue) and a separate `night.sky`.

What made Darkside feel different was an amber sky in daytime and a world whose sun is visibly failing. It was never
endless dusk. Proposed text for WORLD_DESIGN §4, Light row, Darkside column:

> **Amber days and a failing sun.** Darkside keeps day and night (its story needs them: the vampire Queen can only be
> carried out after nightfall). By day the sky is a low amber-gold cloud band under a pale, small sun; nights are dark
> with many stars. Through Acts III–V the sun weakens as Alamar steers Xeen away: three data presets
> (`xeen_darkside_day`, `_fading`, `_failing`) are chosen by main-quest qbits (M17, M27), and the sky returns to full
> strength after M33 (Sheltem defeated). Lamps and windows burn all day only in the last stage.

Replace E8's `xeen_darkside_dusk` with these presets. Choosing a sky preset by qbit at map load is a small engine
question, and it belongs with E6 (staged maps).

### F2. The Lord Xeen twist is told before it is earned (high)

The plan changes who suspects whom:

- M6 says Crodo "vanished the night he quarrelled with Roland", and M7 has Artemus send the party to find "who came
  back" from the pyramids. In the source, Artemus suspects **Darzog**, out of jealousy: "Baron Darzog ... became very
  jealous of this friendship ... Perhaps Darzog has imprisoned him in his tower" (`xeen/aaze0064:2`). The source reveals
  Roland only through Crodo (M21).
- With Darkside open from level 12, Olympus's "Prince Roland is held by Alamar in the bottom level of the Castle"
  (`dark/aaze0037:27`) and Castleview gossip could spoil the reveal well before Darzog's Tower.

Proposed text for QUESTS M6/M7:

> M6 | Artemus, privately: Crodo, the kindly old sorcerer, was the King's friend, and Baron Darzog, the King's master
> sorcerer, was jealous of him. Both have vanished; Darzog's island tower has been sealed since. "If the King were not
> so obsessed with the Sixth Mirror, he would send you there himself."
> M7 | Artemus: the old pyramids are said to lead to "the land below the land", where Roland went before he came home.
> The King will not hear of it, so he gives the party the Pyramid Sigil quietly. (No word that Roland is false.)

Add a rule to QUESTS §1: "Topics and signs that say the court's Roland is false, or that the real Roland is Alamar's
prisoner (Olympus, Castleview, Drusilla), show only after M21." Drusilla's "I sense Alamar is an assumed name"
(`dark/aaze0031:27`) is fine before it, because it is about Alamar.

### F3. Crodo's dreams are missing, and they are why the party matters (medium-high)

In the source's backstory, Crodo sends dreams to the scientists of Newcastle telling them to build a weapon that can kill
Xeen, and a bolt from the sky destroys Newcastle after the last dream (`research/MM4_CLOUDS_CONTENT.md` §1). Freed, he
says "I didn't know that someone else had received my message" (`xeen/aaze0061:0`). That is why the Slayer Sword is
under Newcastle. X1's opening keeps the bolt and drops the dreams. Proposed text for M1 and X1's opening message:

> Vertigo. For weeks you dreamt of an old man in a dark tower who begged you to finish "the sword". Then a bolt from the
> sky destroyed Newcastle, and you woke here among its survivors. Mayor Gunther asks your help: slimes and doom bugs
> plague the town ...

Also put the bottle message "Help! I'm in Darzog's tower!--Crodo" (`xeen/aaze0019:2`, `xeen/aaze0023:19`) in two
places, a creek in X1 and the lakeshore in X2. It is the source's own early hook and it points at Darzog (F2).

### F4. The Clouds ending line goes stale once the faces are interleaved (medium)

M35 keeps King Burlock's "Your destiny lies on the darkside of Xeen" (`xeen/aaze0064:14`). By then the party has been on
Darkside since level 12. Proposed: Burlock's two original lines in M35 become

> "Thank you for rescuing Xeen from that foul spirit. It is a pity about the mirror, though." (`:15`) ... "And my
> brother? If he lives, he is on the other side. Go to him."

and, if Darkside is still unvisited (possible only in the lean order), use the original line.

### F5. How Xeen sits beside MM6–MM8 is not written down (medium)

None of README, WORLD_DESIGN or QUESTS says where Xeen stands relative to the mounted Enroth, Antagarich, Jadame and
Chedian. The source has firm lore here. Corak and Sheltem are Ancient guardian units (S.H.E.L.T.E.M.). The logs name
Terra, VARN and CRON (`dark/aaze0087`, `0088`), and the MM3 heroes are beamed down from a burning ship. MM8's
elemental planes share the names of Xeen's P1–P4. Proposed new section in WORLD_DESIGN (§1.1):

> **Xeen and the other worlds.** Xeen is a separate world, an Ancient nacelle with its own sun. It is reached only from
> its new-game card and has no ship, portal or Town Portal link to the MM6–MM9 continents. The logs keep the source's
> names (Terra, VARN, CRON, the Ancients, Corak, Sheltem). Nothing ties Xeen's events to Enroth's dates, and no NPC
> mentions the Kreegan. The ending is Xeen's own: Corak and Sheltem destroy each other in Castle Alamar (M33), the halves
> unite, and Roland marries Kalindra. Xeen's elemental planes are "the Plane of Fire of Xeen" etc., with their own map
> stems and names, never MM8's planes.
>
> The party is native to Xeen. They are the Newcastle survivors who received Crodo's dreams (F3), not the Terran
> crew of MM5's backstory. Darkside lines that assume strangers from the sky are reworded to "strangers from the other
> side".

### F6. The text policy works against the user's wish (medium; a decision for the user)

PRODUCTION §3 says the world ships "rewritten text", and QUESTS' rules say "Dialogue is rewritten in MM6–MM8
house-dialogue form". The source's charm is its short, deadpan lines. Rewritten, they turn into the earnest generic
prose seen in XD-02/03/05 (F8). Proposal for the user: allow **quoting or close paraphrase of short lines** (signs,
plaques, street lines, one-line jokes) and rewrite only the long dialogues, where house dialogue needs a different
shape. Whether verbatim quotes may ship is the user's call, like the portraits (README open question 7). Add it there
as question 11.

### F7. Riddles under the 2026-11-13 rule: what the source already answers (medium)

Several of the source's puzzles already meet the user's rule, because the game says the answer plainly, and the plan
should not cut them:

| Puzzle | Answer given in the source | Verdict |
| --- | --- | --- |
| Alamar's true name (Castle Alamar L2) | Olympus NPC: "All beings have a true name. Alamar's true name, for instance, is Sheltem." (`dark/aaze0037:4`). The statue that should say it crackles: "It is: kdkiendlshj**:and dugli (crackle)" (`dark/aaze0049:5`) | Keep; both lines are touches |
| Newcastle vault "laboratory" | Shangri-La: "I hear the secret password for Newcastle dungeon is 'laboratory'. Not much of a secret if you ask me." (`xeen/aaze0049:20`) | Keep; the quote is the joke |
| The Voweless Knights | Olympus: "Their questions never change from year to year, so here is a compilation of the answers" (`dark/aaze0037:5`) | Keep, but give the compilation earlier (Castleview library) |
| Enchanted boulders (PALADIN) | Sandcaster: "A dying paladin gave all his magical armor to the enchanted boulders" (`dark/aaze0031:21`) | Keep |
| Rosebud (Witch Tower) | The boy whispers it (`xeen/aaze0051:4`) | Allowed by the rule. XD-04 replaced it with a key after the user's playtest; leave it so |
| Corak's pod | The console shows the phrase ("where no man has gone before", `dark/aaze0087:15`) | Keep if the screen shows it in plain words |
| Nightshadow sundials ("nine") | Cloudside gives no number; "Nine is the time" is a Darkside plaque (`dark/aaze0052:12`) and the "birth number nine" line is in Olympus | Add a Nightshadow sign or NPC: "The Count wakes at nine and sleeps at nine." |
| Sphinx (GOLUX) | Only the five letter clues (`xeen/aaze0084:2`–`:6`) | Fails the rule: let Arie or a Basenji prisoner say "Its name is Golux", or make it a fight |
| Lakeside guild riddle (WITCH) | Only the letter clues (`dark/aaze0033:4`) | Fails: sell membership, or Naomi says the word |
| Eye of the Dragon (INFINITY) | Not given | Fails: a dead adventurer's note, as for Alister |

### F8. Built maps: tone check (medium)

| Map | Verdict | What to add (original text) |
| --- | --- | --- |
| XD-01 Joe's Warehouse | Best voice of the six. The invented gags (warehouse rules "4. See rule 1", "Pests gone or your money back! (Money not back.)", Mr & Mrs Wobbles, Pest of the Month) are in Xeen's spirit | Use the invoice with the source's arithmetic: "Breeder Slimes, 1 mated pair 287 / 5 Doom Bugs at 145 each 725 / Total: 1012 gold" (`xeen/aaze0028:16`); the built "Doom Bugs, 5 (assorted)" loses it. After M2, Joe's desk sign: "Out of Business" (`:49`) |
| XD-02 Red Dwarf Mines | Functional and earnest; the rune colour hint is good design but not Xeen | One or two dwarf notes: "1 bottle orc's milk, 2 boxes of Dwarf biscuits, 1 can of split toadsoup, and one everlasting stick of troll jerky" (`xeen/aaze0033:9`); "There are many DEEP mines." (`xeen/aaze0034:14`) as the hint to the Deep Line |
| XD-03 Deep Mine | Epic inscription ("HERE BRAKKA THE FIRST ... KEEP FAITH") is generic fantasy, more Tolkien than Xeen | "Robbers and thieves take a good look at your fate, should you decide to steal from these mines!" and "Dead men tell no tales." (`xeen/aaze0035:11`, `:10`) by the bones near the hoard. Keep Brakka if wanted, shorter |
| XD-04 Witch Tower | Good: the skull's "One gem. A shiny one. And do something about that face." / "Cheapskate" turns the source's vanity skulls around nicely. The slate is ours (§0) | "Feed me!", "Goblins back to work!", the two vanity skulls, the levitate skull at the roof (§0); one freed child says the original "I want to go home" line |
| XD-05 Orc caves | Invented quest (war drums, Tam son of Oslo); tone neutral | The source's orc content is burnable outposts ("You have found an observation post for the Orcs! Destroy?" `xeen/aaze0019:6`; "The outpost collapses in a heap of ashes, smoke, and smoldering timber." `:7`). Use that wording for the drums |
| X1 Vertigo Meadows | The notice and opening are clear; Valia, Orothin ("The world has an edge. Mind it.") and the rain-barrel key are good. The town has no voice yet: no street lines, cult or drunk | See §3, Vertigo rows: the Plague Cult's four lines, the hiccuping drunk who gives M2's clue (QUESTS M2 already says "a drunk patron's rumour"; X1 uses the barrel only), "This space for rent", "Please help clean up our beautiful town.", Vern's guild dues. Gunther's original welcome (`xeen/aaze0028:1`) can be used almost as it is |

Proposed rule for every brief's L4 (add to PLAN_YAML_NEEDS or the brief template): **"Each map carries at least three
short original lines (signs, plaques, notes, street lines) from its source map, quoted or closely paraphrased, listed
in NOTES with their `aaze` reference."**

### F9. The Witch Tower is now built on the Moon Temple kit (low-medium)

XD-04 uses MM7's Temple of the Moon dressing for the coven floor (NOTES table). Xeen's witches are a cottage-industry
coven of toads, vats, cages and vanity: "Nothing but rags", "Vat", "Cage", "Alcove" (`xeen/aaze0051:22`–`:26`). Keep
the toad lids, vats and cages in front, and keep the Moon frieze in the background.

### F10. Quests that need engine features the plan has not listed (medium)

Missing from PRODUCTION §2:

| Need | Quest | Note |
| --- | --- | --- |
| Damage only from one weapon (Lord Xeen and the Slayer Sword); no damage from area spells | M35 | Per-actor Lua behaviour (`devdocs/ACTOR_SCRIPTING_INVESTIGATION.md`); name it |
| Time-of-day gates (coffin opens only at night; carry the Queen only after nightfall) | Q-C7, M27 | Probably plain Lua over the clock; depends on F1 |
| A companion that travels with the party (Corak in the Soul Box; Celia/Derek reappear; Valio and Guido follow) | M32–M33 | A quest item suffices if Corak never speaks on the road; say so |
| Sky preset by qbit (failing sun) | F1 | With E6 |
| Gem payment | skulls, dragon tax, Slick | O3 should become required: the skulls and the Dragon Tax are core touches |
| Jail for theft ("You were caught stealing! ... one year in jail", `xeen/aaze0028:56`) | towns | MM6–MM8 have no jail; drop it, or make it a fine plus aging. Decide |

### F11. Smaller story points

- M14: a Castleview NPC says passes are sold "just outside the city for cheap" (`dark/aaze0029:14`). The plan keeps
  Justine. Good.
- Joe recurs on Darkside with fake treasure maps ("Don't trust Joe. He has some sort of scheme to sell fake treasure
  maps", `dark/aaze0029:10`). Q-C24/Q-D2 keep him. Make sure his Darkside board copies his Vertigo slogan, so players
  recognise him.
- Two Flints (Rivercity Armsmaster, Sandcaster Treasure Hunter) and Ligono (spirit in the Clouds surf, then waiting in
  Olympus: "I'm waiting for my friend Ligono", `dark/aaze0037:35`) are cross-face callbacks. Keep both.
- M42: the Pharaoh's shrine "checks for the Scepter, the Cube and all four sleeper awards" but not the Reflectors
  (`research/MM5` §2). The plan's M37 makes the Reflectors required; that is a fair tightening, but say it is ours.
- QUESTS Rules: "Every quest has a journal line". The source's terse quest log is part of its voice. Journal lines
  should be one sentence, in the style of "The dwarf mines are still being over-run. Please help them."

## 2. Atmosphere: what made Clouds and Darkside feel as they did

| Element | The original | The plan | Where it went generic / proposal |
| --- | --- | --- | --- |
| **Tone** | Deadpan, cheerful, slightly absurd; danger played straight but the world winks (plaques, ads, guidebook). Darkside is snarkier and more satirical (Alamar's propaganda statues, the palm reader, Vulture Repellant) | Faithful in quests; tone not specified anywhere | Add a "Voice" paragraph to WORLD_DESIGN §1 (below) |
| **Signs and ads** | Rivercity's ads: "If you can read this ad, so can your customers." / "Pray, pay, and be healed today." / "What did you expect, money?" / "REAL adventurers try Deep Mine Alpha!" (`xeen/aaze0030`) | Not planned | Each town gets 4–8 street signs from its source map (§3) |
| **Recurring gags** | The drunk: "Get Lost! Can't you see I'm drinkin'?" in Vertigo, Rivercity and Sandcaster; "There is nothing on, in, or under the bed."; "The water is cool and refreshing." on every well | Not planned | Keep all three as world-wide stock lines (bed and well as default hover/messages) |
| **Cursed towns** | Each has a one-joke hook in its guildmaster: Asp's Sarah Slither "I'll ssslip your name into the guild rollsss"; Winterkill's Casper "I may fall asleep with the roll book open. (wink, wink)"; Nightshadow's Count Du Monay "Because you are still alive, I will have to charge you 250 gold"; Adam and Eve in Asp | D8 keeps the towns and quests | Keep these guildmasters with their lines as the only open house in each cursed town |
| **Sky castles** | Clouds: rhyming walkthrough statues; Slick's carnival ("Step right up and ring the bell with the hammer!" / "You win a prize. Now get lost and don't come back."); the cupie doll gate. Darkside: the Rest Stop signs naming NWC games, Sky Bandits' toll | Kept in MAPS (X9, D7) | Keep Slick's exact patter; Rest Stop signs: see §3 |
| **Colour** | Clouds: blue sky, bright greens; Darkside: amber sky band (F1); the void "space" at the edge | Clouds ok; Darkside wrong (F1) | F1 |
| **Music** | Each town and region has its own tune; Darkside's score is different from Clouds' | "reuse MM6–MM8 tracks" (user decision) | If tracks are reused: one fixed track per town, Cloudside from MM6 (lighter), Darkside from MM7/MM8 darker sets, sky maps one airy track; never the same track for both faces' hubs |
| **NPC voice** | One or two lines, first person, often a joke or a complaint ("I can't believe the cost of healing these days!") | "MM5's one-line joke NPCs become rumour topics" | Good; make sure the line text itself survives (F6) |
| **Mirrors** | "If you say the name of a town to a mirror, it will take you there." / "If you like to fight, say 'Warzone' to a mirror." | Mirrors as transport houses | Keep both lines as Rivercity street lines; let the mirror list a "Warzone" entry |
| **The edge of the world** | The "space" void beyond the rim | D9; X1 built it ("Beyond the meadows the world simply ends, and the stars shine under it.") | Kept well |

Proposed WORLD_DESIGN §1 paragraph:

> **Voice.** Xeen talks in short lines. Signs, plaques and townsfolk are deadpan and often funny: the con man's slogan,
> the drunk who will not be disturbed, a plaque that says "Don't worry, be happy" in a royal castle. Danger is played
> straight; the world winks around it. Cloudside is cheerful and a little silly. Darkside is drier and satirical
> (a tyrant's propaganda statues, a palm reader, Vulture Repellant that does not work). Quest text is one or two
> sentences. No epic inscriptions, no lore dumps outside the Ancient logs and the Bark scriptures.

## 3. Catalogue of the original's touches

Status: **Kept** (plan or built map has it), **Partly**, **Missing**. "Where" is the proposed place.

### 3.1 Cloudside

| Touch (original text) | Source | Status | Where |
| --- | --- | --- | --- |
| Gunther: "Welcome to Vertigo. Sadly, most of the population has left because the town is infested with pests. A couple years ago I hired Joe the exterminator..." | `xeen/aaze0028:1` | Partly (X1 opening paraphrase) | X1 town hall topic |
| Joe: "Two years ago, I came to this town on contract to control the vermin infestation. ... I've just about got the situation under control." | `:7` | Missing | X1, Joe's shop before M2 |
| Plague Cult members: "Sinners must repent." / "The end is near." / "The plague is upon us." / "Slime lords shall rule" | `:17`–`:21` | Missing | X1 street peasants (3–4 "Plague Cult member"), and one painted on Joe's warehouse wall in XD-01 |
| "This space for rent" / "Pest control by Joe" | `:20`, `:22` | Missing | X1 sign boards |
| Drunk: "He...he (hic) breeeds (hicup) Breeeeeds them in the (hic) warehouse (hicup)" | `:27` | Missing (QUESTS M2 names it) | X1 tavern patron: the M2 clue |
| "That Gunther, what a dunce! He paid that con man Joe a fortune..." / "This place is deserted. You should go to Rivercity--Now there's a town full of action!" | `:26`, `:25` | Missing | X1 street |
| Money tree: "Some fool said money's now growing on trees. Ha!" / "You found some money growing on this tree!" | `:24`, `:46` | Partly (tree built) | X1 square; add the sceptic's line |
| Vern the Guildman: "I'll put anyone on the guild roll for free. Dues will cost 25 gold, though." | `:13` | Missing | X1 guild |
| "Please help clean up our beautiful town." | `:63` | Missing | X1 gate sign; after M2 it can read "Thank you" |
| Invoice: "Breeder Slimes, 1 mated pair 287 / 5 Doom Bugs at 145 each 725 / Total: 1012 gold" | `:16` | Partly (XD-01 paraphrase) | XD-01 crate, verbatim |
| "Out of Business" sign on Joe's desk | `:49` | Partly (QUESTS "his shop closes") | X1 Joe's shop after M2 |
| Old Valia and Falista: "when I was still a young maiden, I fell asleep in Toad Meadow. When I awoke I found a unicorn laying down beside me. Her name was Falista..." | `xeen/aaze0024:5` | Partly | X1 Valia's topic, the story told in full |
| Myra: "The witches of the meadow have been turning everyone they find into toads" | `xeen/aaze0023:0` | Kept (Q-C21) | X1 |
| Witch Tower skulls (fairest, Feed me, Goblins back to work, levitate hint) | `xeen/aaze0051` | Missing (XD-04 has its own skull) | XD-04 (§0) |
| Rosebud boy | `xeen/aaze0051:3–4` | Partly (password removed by user decision; the name kept) | XD-04 |
| Crodo's bottle: "Help! I'm in Darzog's tower!--Crodo" | `xeen/aaze0019:2` | Missing | X1 creek, X2 lake (F3) |
| Spring Druid: "As I renew the year, so will I renew you." | `xeen/aaze0019:15` | Kept (Q-C1) | X1 |
| Dwarf mine notes (shopping list, "many DEEP mines", "Dead men tell no tales") | `xeen/aaze0033–0035` | Missing | XD-02, XD-03 |
| Rivercity's teachers: Flint "Fighting is simple. I'll teach you to be an Armsmaster in one easy lesson for 300 gold."; "I see that you are pale and weak ... put some meat on your bones." | `xeen/aaze0030:3`, `:5` | Partly (skill row) | X2 teacher topics |
| Rivercity ads and mirror tips (§2) | `xeen/aaze0030:27–33`, `:67–69` | Missing | X2 |
| Barok: "If Barok ever got his pendant back, this place might charge me for drinks." / "The tavern hired the sorceresses to run Barok out of town." | `:19`, `:21` | Missing (Q-C2 kept) | X2 tavern rumours |
| Asp: Adam and Eve; Sarah Slither's lisp; the pedestal rhymes "The southwest corner is where to start / Begin with red to tell them apart" | `xeen/aaze0031` | Partly (Q-C5 names Adam and Eve) | X4 Asp |
| Winterkill: Casper's bribe; "Acme Ghost Visualization System"; gong rhyme "Bang twice on each northern gong is all you have to do"; the numbered list "1) Destroy all ghosts. 2) Bang southern gong. 3) Re-visit Randon. 4) Repeat as necessary."; title "Ghostslayers Extraordinaire" | `xeen/aaze0032` | Partly (Q-C6) | X5 Winterkill |
| Nightshadow: Count Du Monay's fee for the living; rhymes "Only at night can you put up a fight." / "If the Dials are properly set, The count will definitely be upset." | `xeen/aaze0029:5–8` | Partly | X3 (add "nine", F7) |
| Castle Burlock plaques: "Don't worry, be happy." / "Peasant's choice award--Best Ruler of the Year (597)" / "Have a nice day." / "Speak softly, but carry a large magic sword." / "Remember, eat less and think thin." / "Remember, today is the first day of the rest of your life." | `xeen/aaze0064–0066` | Missing | XD-07 Castle Burlock corridors |
| Burlock: "NO MIRROR?!? Get out of my sight!" | `xeen/aaze0064:13` | Missing | XD-07 King's repeat topic |
| Roxanne: "Don't look so disappointed. I'm not a damsel in distress, but there is a quest you could perform for me." | `xeen/aaze0066:0` | Missing (Q-C3 kept) | XD-07 |
| Shangri-La: "Smile. The intent expression you are wearing is being broadcast to millions from the hidden camera in your monitor." / "Try peanut butter and honey on your morning toast." / "Lord Xeen already has the Sixth Mirror." / "The moons will align when you are able to visit the Darkside." | `xeen/aaze0049` | Missing | Shangri-La hint NPCs (the camera joke may need softening for a 3D game: "...from the hidden crystal in the wall") |
| Dragon Tax urn: "2000 gold pieces and 20 gems fly from your packs and into the urn"; Loremaster titles up to "Taxman Emeritus" | `xeen/aaze0050` | Kept (Q-C25), titles only in research | Dragon Cave; keep "Taxman Emeritus" |
| Rhyming statues ("Advisor will a dig permit five coins more you must submit.") | `xeen/aaze0025–0027` | Kept | X8, X9 |
| Golem Dungeon plaque: "Solve the wood, it's like a tree / Cut the branches and return to me ..." | `xeen/aaze0081:0` | Kept (set pieces) | XD-09 entrance |
| Tomb: "Welcome to the Tomb of a Thousand Terrors. Insanity is our fame, undead is our game." | `xeen/aaze0080:0` | Missing | XD-08 entrance |
| Slick the Gamemaster's patter and "No one may enter Castle Xeen without a cupie doll!" | `xeen/aaze0027:10–31` | Kept | X9 |
| Warzone arena master (from Eeried's guide): "Congratulations on your awesome victory! ... I'll send you to Vertigo, now!" "Uh, don't I get a reward or something?" "No. Goodbye..." | `dark/aaze2121:5` | Missing | Warzone master's line (rewards are given, but keep the joke for the lowest tier) |

### 3.2 Darkside

| Touch (original text) | Source | Status | Where |
| --- | --- | --- | --- |
| "This bench reserved for Lyle the Pigeon Feeder" | `dark/aaze0029:6` | Missing | D1 Castleview square bench |
| "Ellinger has a great fondness for boots." | `:7` | Missing | D1 street line (and DD-02 dressing) |
| "The Gremlins sure have ruined this city. Mayor Snarfblad is too nice. He should have executed those little creeps long ago." | `:11` | Kept (names) | D1 |
| Gettlewaithe: "I am Gettlewaithe, Imperator Primus of the Gremlins! Give me one good reason why I should not ..." and the three answers incl. "Silence, insect! We are in charge now!" | `:83–84` | Kept (Q-D1) | DD-04; keep the choice wording |
| Valio's diploma: "Valio Magnus, graduated 787 cum laude, School of Evil Wizardry." / "Hey, that's MY chest. Leave it alone!" | `dark/aaze0030:12`, `:22` | Partly (Q-D5) | DD-01 |
| Guido the convict: "You didn't make a mistake, TRUST me. Try 10,11,12 on the tougher safes. See ya." and his sentence book | `dark/aaze0044:6`, `:47` | Kept (names) | DD-03 dungeon |
| "Beware of Scraps!" / "Don't feed Scraps." / "Don't let Scraps out!" | `dark/aaze0044:49–51` | Kept (Scraps) | DD-03 dungeon notes |
| Sandcaster market: "Special today! Vulture Repellant, only 25,000 gold!" ... "Vulture Repellant doesn't work." | `dark/aaze0031:19`, `:25` | Partly (MAPS mentions vultures) | D3 Crossroads stall + street line |
| Aladdin the Lamp Cleaner: "Never take all of a genie's money. It's greedy." | `:41` | Missing | D3; links Q-D27 |
| Madame Gloriana the Palm Reader: "I predict ... you will die young...and then be ressurected...and then die again...over and over" | `:49` | Missing | D3 |
| "The wizards in this town are sensitive to insults. Watch what you say!" / "Begone, children, lest I blast you to ash ..." | `:29`, `:37` | Missing | D3 wizard quarter |
| "The three most important things in archery are accuracy, accuracy, and accuracy." | `:39` | Missing | D3 bow teacher |
| Lakeside: "These stairs once led to a tavern, but it was destroyed long ago."; "This boat under repair."; potion-recipe skulls ("the blood of a monkeydog sacrificed 'neath the bl...") | `dark/aaze0033:1`, `:18`, `:12–14` | Missing | D4 Lakeside before liberation |
| The five prisoners' lines, last one "(yawn) Thank you for saving me from my hideous fate. ... I'll be going now. See you." | `dark/aaze0033:24–28` | Kept (Q-D22) | D4 Lakeside sewer |
| Necropolis: the aging books ("The experience aged you. +25 years ..."); "Food for the dead, keep warm." barrel; skull's story of the two necromancers' five-day battle | `dark/aaze0035`, `dark/aaze0036:5` | Partly | D6 Necropolis |
| Sandro: "Do not come to me without my heart." / "Don't even THINK about taking my statuette!" | `dark/aaze0035:27`, `:29` | Kept (Q-D23) | D6 |
| Alamar's propaganda statues: "...crime has decreased and production increased. Further, social deviance has virtually disappeared while complete obedience ..." and the crackling true-name statue | `dark/aaze0049:2–5`, `dark/aaze0052:13` | Missing | DD-17 Castle Alamar, one per floor |
| Olympus: "Ever lie down on your belly and look over the edge of the cloud? The people are so small they look like ants"; "Pears just about everywhere cost but 1 gold."; Ligono waiting | `dark/aaze0037` | Partly | D7 Olympus |
| Gurodel: "Greetings, little ones." and the tax-collector answer "Our records indicate that you are WAY behind in your taxes to the Pharoah" / "What a coincidence! The Ogres said the same thing." | `dark/aaze0013:19–32` | Kept (Q-D16) | D5; keep the reply choices verbatim |
| Bosco: "I dub thee royal taste tester" | `dark/aaze0013:16` | Kept (research) | D5 Bosco's Hall |
| Sharla's three replies incl. "This is a stick up! Give us all your gold, gems, and energy disks and no one will get hurt!" | `dark/aaze0012:24` | Kept (Q-D10 routes) | D2 |
| "Forbidden Fruit" huts: "You realize that you shouldn't have eaten the coconut of confusion." / "Yuk! The plum of unconsciousness." | `dark/aaze0012:3–21` | Kept (MAPS D2) | D2 |
| Thieves' letterhead: "To all members: The Trolls have stolen our gold. Get it back no matter the cost!" | `dark/aaze0040:5` | Kept (Q-D13) | Troll Holes |
| Statuette ledger: "One (1) Griffin Statuette, sold to Sandro of Necropolis for 350,000 gold ..." | `dark/aaze0062:1` | Kept (Q-D19) | Southern Tower |
| Dungeon of Lost Souls: "Welcome to the Dungeon of Lost Souls. Never underestimate the power of positive thinking." | `dark/aaze0078:12` | Kept ("think positive" gates) | DD-12 entrance plaque |
| Genie: "What took you so long? I've been stuck in that little lamp for 2000 years. ... Two thousand years is simply unacceptable." | `dark/aaze0099:2` | Partly (Q-D27) | One evil-genie lamp |
| Messages in bottles: "Evil Genies NEVER let their victims off the hook"; "Help! I'm stranded on an air island ..." | `dark/aazex103`, `x107` | Partly | D7 |
| Sky Bandits: "This is a robbery. Everyone stay calm and no one will get hurt." and reply "There's always a first time." | `dark/aazex105`, `x108` | Kept (D7 toll) | D7 |
| Rest Stop signs: "Might and Magic", "King's Bounty", "Empire Deluxe", "Spaceward Ho!", "Vegas Games", "Inherit the Earth", "New World Computing", "Tunnels and Trolls", "Nuclear War", "Planets Edge"; "The observatory is closed." | `dark/aazex129:1–11` | Kept (MAPS mentions Rest Stop) | P5 Clouds of the Ancients walk |
| Pharaoh: "It's a long road ahead so rest where you can. But don't forget to recast your spells." | `dark/aazex129:15` | Missing | P5, by the last rest stop |
| Prime Directive book: "Prime Directive: Obey the Ancients, Secondary Directive: Protect Xeen, Tertiary Directive: Complete the Destiny of Xeen." | `dark/aaze0086:30` | Missing | DD-15 Great Pyramid top |
| Pod logs (Corak's and Sheltem's) incl. "Corak's escape pod landed in lava and is stuck there. How sad." | `dark/aaze0087–0088` | Kept (M29) | DD-16, and Sheltem's pod in D6 |
| Tribbles: "You know TRIBBLES are great companions but you'll be surprised what doors they can open for you!" | `dark/aaze0038:15` | Kept (Q-D28) | Olympus sewer |
| Eeried's guidebook "The World of Xeen on 30 gold a day by Eeried the Cartographer" (Necropolis "the undead are people too", Lakeside goblins, Sandcaster "like fleas on a dog", the Arena, octopus soup "the arachnoid garnish tasted like chicken") | `dark/aaze2121:5` | Missing | A readable book sold in Castleview and Vertigo, in chapters by face. The best single touch for atmosphere, and it gives hints in character |

## 4. Proposed changes in short

1. WORLD_DESIGN §4 / PRODUCTION E8: Darkside keeps day and night with an amber day sky and a sun that fails by stage
   (F1).
2. QUESTS M6/M7: Artemus suspects Darzog; no early Roland reveal; Darkside Roland hints wait for M21 (F2).
3. QUESTS M1 and X1: Crodo's dreams; two Crodo bottles (F3).
4. QUESTS M35: Burlock's line for the interleaved order (F4).
5. WORLD_DESIGN §1.1: Xeen and the other worlds; the party is native; Xeen's own planes (F5).
6. README question 11: may short original lines be quoted (F6).
7. README riddle section: the table in F7 (which source puzzles already comply, which need an answer-giver).
8. Brief rule: three original lines per map, with references (F8); retrofit the six built maps from §3.
9. PRODUCTION §2: the engine needs in F10; O3 (gem payment) becomes required.
10. WORLD_DESIGN §1: the Voice paragraph (§2).
