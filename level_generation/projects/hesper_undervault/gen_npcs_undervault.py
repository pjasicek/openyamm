"""Writes level_generation/projects/hesper_stage/npcs_undervault.yml (the Undervault's people). Texts: P4's
design/kreegan_world/quests/dialogue/UNDERVAULT.md, NPCS.md, LANDFALL.md (news), READABLES.md (Pell's lines)."""
import json
from pathlib import Path

import yaml

ROOT = Path('/home/pjasicek/github/OpenYAMM')
OUT = ROOT / 'level_generation/projects/hesper_stage/npcs_undervault.yml'
P = 'design/kreegan_world/art/portraits/x2/'
L = json.dumps


class Lit(str):
    pass


yaml.SafeDumper.add_representer(Lit, lambda d, v: d.represent_scalar('tag:yaml.org,2002:str', v, style='|'))


def msg(text):
    return f'evt.SetMessage({L(text)})'


npcs, topics = [], []


def npc(nid, name, portrait, greeting, tops, house=None):
    entry = {'id': nid, 'name': name, 'portrait': P + portrait + '.png',
             'greeting': greeting if isinstance(greeting, list) else [greeting, greeting], 'topics': tops}
    if house:
        entry['house'] = house
    npcs.append(entry)


def topic(tid, title, lua, after=None, until=None):
    entry = {'id': tid, 'title': title}
    if after:
        entry['show_after'] = after
    if until:
        entry['show_until'] = until
    entry['lua'] = Lit(lua.strip('\n') + '\n')
    topics.append(entry)


REP = 'AddValue(ReputationInCurrentLocation, -1)'      # REPUTATION.md: a Hesperian hand-in, once (its done bit)

# --- Elder Maren, the Council Hall (9454) ---------------------------------------------------------------------------
npc(9501, 'Elder Maren', 'hes_elder_maren',
    ["So these are the Guardian's travelers. Sit. I am Maren; I speak for the Council, which means I count what we have left and decide what to spend. You may be the first thing in years worth spending it on.",
     "Travelers. The Council listens."], [9660, 9661, 9662], house=9454)
topic(9660, 'The Council', msg("Seven families sit on the Council, as the founders' seven crews did. We keep the water, the light, the Archive and the peace. Landfall keeps the walls. The Guardian keeps us. It has been enough to live on. It has not been enough to win."))
topic(9661, 'Borrowed Shields', f'''
-- M5: given here (100205), Krav killed in D3 (P1's 100024), done here (100005).
if IsQBitSet(QBit(100024)) then
  ClearQBit(QBit(100205))
  SetQBit(QBit(100005))
  AddValue(InventoryItem(11332), 11332)
  AddValue(Experience, 20000)
  {REP}
  {msg("Krav is dead. The crews went out this morning; two of them sang. Keep the bucklers, and take this: a training core from the founders' academy, the Council's to give.")}
  return
end
if IsQBitSet(QBit(100205)) then
  {msg("Krav still holds the Quarry. The Scour, east of the Reach, on the mesa.")}
  return
end
SetQBit(QBit(100205))
{msg("Our salvage crews go out to the old colony sites for alloy and cells; it is how we eat. For a year the devils of the Quarry Outpost, on the Scour east of the Reach, have taken them: the crews, their gear, their bucklers. Their Overseer is called Krav. Kill him, and the crews go out again. Whatever shields you find in his stores, keep them. Consider them borrowed.")}
''', until=100005)
topic(9662, 'The Kept', f'''
-- M6: given here (100206), Tamsin (100025) and Ilse (100026) freed in D4 (P1's events 72, 73), done here (100006).
local tamsin, ilse = IsQBitSet(QBit(100025)), IsQBitSet(QBit(100026))
if tamsin and ilse then
  ClearQBit(QBit(100206))
  SetQBit(QBit(100006))
  AddValue(InventoryItem(11332), 11332)
  AddValue(Experience, 20000)
  {REP}
  SetAutonote(10405)
  {msg("They are home, both of them, and thin as wire. Tamsin is already arguing with the Refuge's pumps; Ilse has taken the Clinic. The Council owes you this: the founders' last training core.")}
  return
end
if not IsQBitSet(QBit(100206)) then
  SetQBit(QBit(100206))
  {msg("The devils keep our taken in the Labor Pens, a pit on the Scour with cages round it. They call them the Kept. Two of them we need above all: Tamsin, who could mend anything the founders built, and Doctor Ilse, who could mend us. Bring them home. Free whoever else you can; the collars are worked from a control room inside.")}
elseif tamsin then
  {msg("Tamsin is home. Ilse is still in that place.")}
elseif ilse then
  {msg("Ilse is home. Tamsin is still in that place.")}
else
  {msg("The Labor Pens, on the Scour. Tamsin and Ilse.")}
end
''', after=100003, until=100006)

# --- Tamsin, the Kept Refuge (9457, open from M6) --------------------------------------------------------------------
COUNT = '{[0] = "None", "One", "Two", "Three", "Four", "Five"}'
npc(9502, 'Tamsin', 'hes_tamsin',
    ["You found me work almost as soon as you opened my cage. Tamsin, in case we weren't properly introduced. What needs fixing?",
     "Back? Good. I've had ideas."], [9670, 9671, 9672, 9673], house=9457)
topic(9670, 'The Pens', msg("Four years of cutting resin for the black ones. They kept me because I could make their stolen machines run. I made them run badly, quietly, when I could. The collars sing to the Lattice. Break the song and the collar is just a ring of metal."))
topic(9671, 'Collars Off', f'''
-- S6: given here (100226), the five camps freed on the Scour (P1's 100115-100119, all five 100106), the reward 100120.
if IsQBitSet(QBit(100120)) then
  {msg("Five free camps. The Refuge is full of names again.")}
  return
end
if IsQBitSet(QBit(100106)) then
  ClearQBit(QBit(100226))
  SetQBit(QBit(100120))
  AddValue(InventoryItem(11332), 11332)
  -- Not staged yet (hesper_stage/items.yml): the Combat Reflex II (11211), an implant: AddValue(InventoryItem(11211), 11211)
  AddValue(Experience, 20000)
  {msg("All five camps free. Here, take this training core the devils were keeping, and a reflex graft I took off an Overseer's bench. And Ansel at the pit-fighters' camp says he will teach you the blade, the way he learned it. He means it kindly.")}
  return
end
if IsQBitSet(QBit(100226)) then
  local free = 0
  for _, bit in ipairs({{100115, 100116, 100117, 100118, 100119}}) do
    if IsQBitSet(QBit(bit)) then
      free = free + 1
    end
  end
  evt.SetMessage(({COUNT})[free] .. " of the five camps free.")
  return
end
SetQBit(QBit(100226))
SetAutonote(10406)
{msg("There are five work camps on the Scour, full of people like me. Every camp has a collar node, a post the collars listen to. Open it with a hacker's hands and every collar in that camp falls off. Or kill the camp's Overseer: the collars die with him. Do it for all five.")}
''')
topic(9672, 'The Lattice', f'''
-- The nodes' hearts (P3's 100009 East, 100010 West, 100014 North); the three node quests as Aster's 9633 gives them.
local down = 0
for _, bit in ipairs({{100009, 100010, 100014}}) do
  if IsQBitSet(QBit(bit)) then
    down = down + 1
  end
end
if down == 3 then
  {msg("The Lattice is dead. I watched the collar-light in the Refuge go out in every scar at once.")}
elseif down > 0 then
  evt.SetMessage(({COUNT})[down] .. " down. Same trick for the rest.")
else
  if not IsQBitSet(QBit(100209)) and not IsQBitSet(QBit(100210)) and not IsQBitSet(QBit(100214)) then
    SetQBit(QBit(100209))
    SetQBit(QBit(100210))
    SetQBit(QBit(100214))
    SetAutonote(10410)
  end
  {msg("I grafted resin onto Node North for a year; I know how they're built. Each heart hangs on three couplings. A master hacker shuts them at their terminals and nothing knows you were there. Without one, a Breach Charge on each coupling: loud, and it wrecks the vault, but the heart dies the same.")}
end
''', after=100006)
topic(9673, 'Node North', f'''
AddValue(InventoryItem(11332), 11332)
SetQBit(QBit(100051))
{msg("You took Node North. I fused cells into that thing with a collar on my neck. Here. A training core I stole off their bench the week before you came. I was saving it for something good.")}
''', after=100014, until=100051)

# --- The Clinic (9452): Neve from M3, Doctor Ilse from M6 ------------------------------------------------------------
npc(9503, 'Doctor Ilse', 'hes_doctor_ilse',
    ["Sit down and let me see that wound. I'm Doctor Ilse; Neve and I keep the Clinic now. We fit what the devils grow and what the Ancients built, and we do not ask which.",
     "Sit. Where does it hurt?"], [9680, 9681, 9227])     # 9227: Grandmaster Cybernetics (hesper_stage/skills.yml)
topic(9680, 'Implants', msg("Four sockets in the body, if you let me cut. The Ancients made the ports; the devils grow parts that fit them, because they took the patterns from us. Two of the same family do not add up; the better one counts. I will name what you bring me, and mend it if it is cracked."))
topic(9681, 'Glass Hunt', f'''
-- S4: given here (100224), three Glassback Hearts (11485, the Glassfields' drops) handed in at once (100104).
local hearts = 0
for _, member in ipairs(PartyMembers()) do
  hearts = hearts + PlayerItemCount(member, 11485)
end
if hearts >= 3 then
  RemoveItem(11485)
  RemoveItem(11485)
  RemoveItem(11485)
  ClearQBit(QBit(100224))
  SetQBit(QBit(100104))
  -- Not staged yet (hesper_stage/items.yml): the Ablative Lattice II (11205), an implant: AddValue(InventoryItem(11205), 11205)
  -- An Engram Core (11332; an Engram until CR-INT-1's larger supply).
  AddValue(InventoryItem(11332), 11332)
  AddValue(Experience, 10000)
  {REP}
  {msg("These hearts are sound. I can use them. Take this ablative lattice and an engram core I took off a Kreegan surgeon's tray.")}
  return
end
if IsQBitSet(QBit(100224)) then
  evt.SetMessage(({COUNT})[hearts] .. " of three hearts.")
  return
end
SetQBit(QBit(100224))
{msg("The glassbacks in the Glassfields grow a crystal heart that takes an energy hit and spreads it thin. Three of those and I can grow you an ablative lattice: energy runs off you like rain. They shrug off your guns; take blades.")}
''', after=100006, until=100104)
npc(9512, 'Neve', 'hes_neve',
    ["Welcome to the Clinic. I'm Neve. I can fit what you bring me, as long as we know what it is.",
     "Back for a fitting?"], [9734, 9735], house=9452)
topic(9734, 'The bay', msg("The Ancients built this bay to fit implants. I can sell them and set them in. I cannot tell you what an unknown one does, or mend a broken one. There was a surgeon who could. The devils took her to the Pens."), until=100006)
topic(9735, 'Doctor Ilse', msg("She is back, and she has taken over, and I have never been so glad to be ordered about."), after=100006)

# --- Brannoc, the Sim Hall (9204, hesper_stage/skills.yml) ------------------------------------------------------------
npc(9504, 'Brannoc', 'hes_brannoc',
    ["The training rigs are ready. You can practice here, or try the ring if you want a prize. Ask for Brannoc when you're ready.",
     "Back. Good. Warm up."], [9685, 9686], house=9204)
topic(9685, 'The Sim Hall', msg("The hall makes enemies out of light: they hit like the real ones and die like them, and nobody stays dead. I train your levels here, the old way. And for anyone who joins you late, the rigs teach the first steps of the four disciplines, free."))
topic(9686, 'The Ranks', f'''
-- S8: given here (100228); the ranks won in the arena (100121 Bronze, 100122 Silver, 100123 Gold): the arena's waves
-- are not built yet (hesper_undervault README).
if IsQBitSet(QBit(100123)) then
  {msg("Gold. I've seen it done twice. You're the second.")}
elseif IsQBitSet(QBit(100122)) then
  {msg("Silver. The masters up top will hear of it.")}
elseif IsQBitSet(QBit(100121)) then
  {msg("Bronze. Not bad.")}
else
  if not IsQBitSet(QBit(100228)) then
    SetQBit(QBit(100228))
    SetAutonote(10416)
  end
  {msg("Three ranks in the ring. Bronze pits you against the Reach's creatures, Silver against the Scour's, and Gold against what waits in the Crown. Each has a prize. Win Silver and the masters up top give you half-price lessons; they owe me.")}
end
''')

# --- Pell, the Archive (9455) ---------------------------------------------------------------------------------------
PELL = ["The Starport, busy! I have never seen a green board in my life.", "She knew. Or the other one did.",
        "The Glassfields. I always thought they were older than that.", "The Kept began on the second day. Two days.",
        "Ilka Mar, of Sesha's line. Her name is in our families' book.",
        "The collars, on the sixth day. Tamsin should read this.",
        "The Brood Spires were a marsh. A marsh! With birds, the old books say.",
        "The ninth day. Aster remembers the ninth day.", "The going below. My family's book starts here.",
        "So that is what the Crown is. It was our core. It was ours.",
        "The Old Line! Here it is, in his own words.",
        "Sel Ek, of Torvan Ek's line, kept this Archive before me. I know his name. Now I know what he saw."]
npc(9505, 'Pell', 'hes_pell',
    ["Visitors! From outside! Sit, sit; mind the stacks. Pell, the Archive's keeper. Have you seen anything written, out there? Anything at all?",
     "Ah, you. Brought me anything to read?"], [9690, 9691, 9692, 9694, 9695], house=9455)
topic(9690, 'The Archive', msg("The founders' records, the colony's laws, a thousand years of the Hesperians' births and deaths: all here, or most. The oldest records are in the founders' dome on the surface, sealed since the fall. And the colony's log tablets lie all over the four lands, where the colonists set them; I would give a great deal for every one."))
topic(9691, 'The Old Line', f'''
if IsQBitSet(QBit(100217)) then
  {msg("The Deep Stair, behind the Lift Gate. A Grandmaster's hands.")}
  return
end
SetQBit(QBit(100217))
SetAutonote(10411)
{msg("The founders' record names it: the Old Line, the freight line the Ancients ran under the planet, from our Deep Stair to the core of what is now the Crownspire. It is sealed with a root lock, the deepest kind. A Grandmaster's hands would open it; Iver teaches that, if the Guardian has given him the codes. At its far end, Grid Control could kill the cannons from inside.")}
''', after=100050, until=100017)
topic(9692, 'After the line', msg("You rode the Old Line. The Ancients built it and we forgot it was there for a thousand years. Write it all down for me, every station."), after=100017)
pell_lines = ',\n  '.join(L(line) for line in PELL)
topic(9694, 'Dead Letters', f'''
-- S9: given here (100229); every tablet carried (11360-11371) taken at once, each its bit (100124-100135) and Pell's
-- line (READABLES); the twelfth closes it (100109, the Old Line known 100050).
local lines = {{
  {pell_lines}
}}
local text, taken, held = "", 0, 0
for k = 1, 12 do
  if not IsQBitSet(QBit(100123 + k)) and HasItem(11359 + k) then
    RemoveItem(11359 + k)
    SetQBit(QBit(100123 + k))
    text = text .. lines[k] .. " "
    taken = taken + 1
  end
  if IsQBitSet(QBit(100123 + k)) then
    held = held + 1
  end
end
if held == 12 then
  ClearQBit(QBit(100229))
  SetQBit(QBit(100109))
  SetQBit(QBit(100050))
  -- Not staged yet (hesper_stage/items.yml): the Last Light of Hesper (11428): AddValue(InventoryItem(11428), 11428)
  AddValue(InventoryItem(11332), 11332)
  SetAutonote(10417)
  AddValue(Experience, 40000)
  {REP}
  evt.SetMessage(text .. "All twelve. Now we know how it ended, and where the Old Line goes. Take the Last Light of Hesper from our vault, and a training core. You've brought our history home.")
  return
end
if not IsQBitSet(QBit(100229)) then
  SetQBit(QBit(100229))
  if taken == 0 then
    {msg("The colony set log tablets on plinths across the four lands: twelve, the old inventory says. Each is a page of the colony's last year. Bring them to me as you find them; read them first, if you like. Together they tell how we fell.")}
    return
  end
end
evt.SetMessage(text .. held .. " of twelve.")
''', until=100109)
topic(9695, "The founder's head", msg("You set the founder's head back on the statue. A thousand years a trophy in their palace, and now the founder looks at the Starport again. I'll put it in the record."), after=100301)

# --- Orrin, the Workshop (9453) -------------------------------------------------------------------------------------
npc(9511, 'Orrin', 'hes_engineer',
    ["Stand behind the line while the fabricator runs. I'm Orrin. What have you brought me?", "Bring me something to fit?"],
    [9731, 9732, 9733, 9757, 9758, 9759], house=9453)
topic(9731, 'The Workshop', msg("The Ancients' fabricator still runs, if you feed it. I fit one mod to a weapon, a body piece, a helm, a cloak or an emitter: two kinds from the start, two more once the devils start losing. Gold and salvage, and you know what you get before I start. And I buy alloy and cells at full weight; no one up top pays you better."))
# The four mods (ITEMS "Workshop mods"; the world's workshop_mods table, ids 1-4) and the salvage he buys at full
# value: HesperWorkshop in hesper_stage/common/workshop.lua.
for tid, title, mod in (
        (9732, 'Shieldbreaker (15 000)', '{id = 1, name = "Shieldbreaker", gold = 15000, salvage = 11351, count = 2, '
                                         'salvageName = "Ion Cells", objectives = 0, what = "a weapon"}'),
        (9733, 'Insulation (10 000)', '{id = 2, name = "Insulation", gold = 10000, salvage = 11350, count = 2, '
                                      'salvageName = "Kreegan Alloy", objectives = 0, '
                                      'what = "body armour, a helm or a cloak"}'),
        (9757, 'Swift Coupling (25 000)', '{id = 3, name = "Swift Coupling", gold = 25000, salvage = 11351, count = 2, '
                                          'salvageName = "Ion Cells", objectives = 3, what = "a weapon"}'),
        (9758, 'Capacitor Link (20 000)', '{id = 4, name = "Capacitor Link", gold = 20000, salvage = 11351, count = 3, '
                                          'salvageName = "Ion Cells", objectives = 3, '
                                          'what = "body armour or an emitter"}')):
    topic(tid, title, f'HesperWorkshop.fit({mod})')
topic(9759, 'Sell salvage', 'HesperWorkshop.buySalvage()')

# --- Odo, by the Water Works arch (a villager actor, from M2) ---------------------------------------------------------
npc(9506, 'Odo', 'hes_odo', ["That puddle wasn't there this morning. I'm Odo, and keeping the pipes working is supposed to be my trade.",
                              "Dry feet? Lucky you."], [9700])
topic(9700, 'Pressure', f'''
-- S2: given here (100222), done in D2 (its filter console, 100102), Odo's thanks (100114).
if IsQBitSet(QBit(100102)) then
  ClearQBit(QBit(100222))
  SetQBit(QBit(100114))
  AddValue(InventoryItem(11332), 11332)          -- an Engram Core (an Engram until CR-INT-1)
  AddValue(Experience, 10000)
  {REP}
  {msg("Water's running! Clean as the founders drank it. Here: a training engram core my grandfather found in the pipes. Never knew what to do with it.")}
  return
end
if IsQBitSet(QBit(100222)) then
  {msg("Three valves, one big glassy beast, one console. The canyon south-east of your crater.")}
  return
end
SetQBit(QBit(100222))
{msg("The Pumping Station in the canyon feeds us and Landfall both, and it's choked: glass growing in the filters, the cistern flooded, and something big nesting in the beds. Drain it, clear the beds, run the filter console. You'll find the old door through the Water Works opens from the far side.")}
''', until=100114)

# --- Pim and Sabra, gallery homes (events 18, 19) --------------------------------------------------------------------
npc(9551, 'Pim', 'hes_pim', "If a turret starts clicking, send for me. Pim. Don't try to open it yourself.", [9766])
topic(9766, 'The walls', msg("Four bastions on the gates, seven wards on the wall. Old guns, kept up. They don't like seekers and they don't like anything bigger either."))
npc(9552, 'Sabra', 'hes_sabra', "Sabra. Yes, the wire in my hair is Ashrunner. My mother was. I married down.", [9767])
topic(9767, 'Ashrunners', f'''
if IsQBitSet(QBit(100101)) then
  {msg("You brought the crawler home? Then you have a camp of friends who shoot straight. Treasure that.")}
  return
end
{msg("The camp north-west of Landfall lost a crawler to the scrapyard east of the apron. Bring it home and Garrow will call you friend. He means it, too.")}
''')

# --- The Kept Refuge's freed Kept (from M6; the camps' four from their camps' bits) -----------------------------------
KEPT = [(9574, 'Hob', 'hes_kept_1', "Free. I keep saying it.", 9830, 'The Pens', "They fed us once a day and the collar did the rest. If you go back there, burn it."),
        (9575, 'Dree', 'hes_kept_2', "You opened the cages. I saw you.", 9831, 'Work', "I can carry, dig and shoot straight. Pay me and I will walk behind you anywhere but back."),
        (9576, 'Cale', 'hes_cale', "Camp one. Cutters' camp. Not any more.", 9832, 'The wreck', "We cut plate off the dead ship by the road. Old bones, gray. The black ones were afraid of it."),
        (9577, 'Senna', 'hes_senna', "I walked down from the stacks. All the way.", 9833, 'The Foundry', "Every load we cut went north to the Foundry. Every gun that came back pointed at us."),
        (9578, 'Rook', 'hes_rook', "Don't look at my neck.", 9834, 'The pit', "The Harvester ate the ground and we ate dust. When it stopped grinding I slept a whole night."),
        (9579, 'Tibb', 'hes_tibb', "Old Tibb. Older than the collar. Ha.", 9835, 'Overseers', "They fly, they shout, they never get tired. But they bleed like anyone. Kill the one on the perch first.")]
for nid, name, face, greeting, tid, title, text in KEPT:
    # Hob and Dree live in the Refuge (it opens at M6); the camps' four are moved in by its door (event 14).
    npc(nid, name, face, greeting, [tid], house=9457 if nid in (9574, 9575) else None)
    topic(tid, title, msg(text))

# --- The street people (the hall, villager actors) and the gallery residents (events 20-25): two News each ----------
STREET = [(9553, 'Ressa', 'hes_townsfolk_1'), (9554, 'Talen', 'hes_townsfolk_2'), (9555, 'Ulla', 'hes_townsfolk_3'),
          (9556, 'Varek', 'hes_townsfolk_4'), (9557, 'Wyn', 'hes_townsfolk_5'), (9558, 'Yorra', 'hes_townsfolk_6'),
          (9559, 'Zeph', 'hes_townsfolk_7'), (9560, 'Bettan', 'hes_townsfolk_8'), (9561, 'Corvin', 'hes_street_09'),
          (9562, 'Delra', 'hes_street_04'), (9563, 'Fiora', 'hes_street_06'), (9564, 'Gell', 'hes_street_07'),
          (9565, 'Hanno', 'hes_street_01'), (9566, 'Iola', 'hes_street_10'), (9567, 'Jessa', 'hes_street_04'),
          (9568, 'Kobb', 'hes_street_01'), (9569, 'Lissa', 'hes_street_06'), (9570, 'Mott', 'hes_street_07'),
          (9571, 'Nara', 'hes_street_10'), (9572, 'Oswin', 'hes_street_09'), (9573, 'Rhosa', 'hes_street_06')]
# One greeting each, the same at first and later (P4, UNDERVAULT.md "Street people and home residents: greetings").
STREET_GREETINGS = {
    9553: "Come down from the surface? Let your eyes settle before you take the steps.",
    9554: "The traders are busy today. If you need salvage, try Orrin's Workshop on the south wall.",
    9555: "Looking for the Guardian? Follow the steps to the blue light.",
    9556: "I'm cleaning the fountain. You can still drink from the far side.",
    9557: "I know every face in this hall except yours. Stay a while; tell us about yourselves.",
    9558: "My grandfather was born behind that door. I was born there too. Have you come far?",
    9559: "Can it wait? No? Then tell me on the way.",
    9560: "You've brought half the surface down on your coats. There's water at the fountain if you need it.",
    9561: "Council business goes through me. Corvin. Give me your names and I'll see who has time.",
    9562: "The people in the Refuge need a little quiet. Some of them only arrived today.",
    9563: "Are you lost? The shops are below. These galleries are where we live.",
    9564: "Another lamp gone over the arch. I'll get to it when I've finished this one.",
    9565: "Sit with me a moment. I've lived under this roof eighty years, and I still like hearing the lift arrive.",
    9566: "Has the Guardian spoken to you? I light a lamp for her, but I've never heard her voice.",
    9567: "Welcome below. The lift leaves your knees shaking the first few times.",
    9568: "Come round to my right. I can't hear you in that ear.",
    9569: "Come in if you have time. The children have been waiting to meet the people from the sky.",
    9570: "One mark for every drum. Help me count these, would you? I keep losing my place.",
    9571: "There's room for another lamp in the Chapel tonight, if you'd like to leave one.",
    9572: "I've never been past the Lift Head. Is the surface as bad as the guards say?",
    9573: "Tea? It's made from the pale fungus. Let it cool a little; it tastes better.",
}
for k, (nid, name, face) in enumerate(STREET):
    # The opening item in turn (9771-9774), the later item in turn (9775-9790): neighbours always differ.
    npc(nid, name, face, STREET_GREETINGS[nid], [9771 + k % 4, 9775 + k % 16])

houses = [
    # The Clinic sells Cybernetics' Novice (CR-INT-1; skills_stage.offered keeps it out until the engine has the skill).
    {'id': 9452, 'name': 'The Clinic', 'map': 'hes_undervault.blv', 'hours': [8, 20], 'teaches': ['Cybernetics'],
     'skill_price': 2},
    {'id': 9453, 'name': 'The Workshop', 'map': 'hes_undervault.blv', 'hours': [8, 20]},
    {'id': 9454, 'name': 'The Council Hall', 'map': 'hes_undervault.blv', 'hours': [8, 20]},
    {'id': 9455, 'name': 'The Archive', 'map': 'hes_undervault.blv', 'hours': [8, 20]},
    {'id': 9456, 'name': "The Guardian's Chapel", 'map': 'hes_undervault.blv', 'type': 'Temple', 'price': 10},
    {'id': 9457, 'name': 'The Kept Refuge', 'map': 'hes_undervault.blv'},
]

HEADER = """\
# The Undervault's people (hesper_stage/stage.py merges npcs_*.yml with npcs.yml; written by
# level_generation/projects/hesper_undervault/gen_npcs_undervault.py, edit that script): the Council's houses and their
# people (P4's design/kreegan_world/quests/dialogue/UNDERVAULT.md, the integrator's follow-ups 42, 43 and 36), the hall's
# street people and the gallery residents with the shared news (npcs.yml, 9771-9790), the Refuge's freed Kept.
# Aster (9500, npcs.yml) and Iver (9223, skills.yml) live in the Chapel (9456); Brannoc in the Sim Hall (9204,
# skills.yml). `house`: npc.txt's 2D location; the people who come later (Ilse at M6, the camps' Kept) are moved in by
# their doors' events (evt.MoveNPC in hesper_undervault/source/hes_undervault.handlers.lua). The street people and
# gallery residents have one short greeting each (UNDERVAULT.md). Items not staged yet are commented in their topics.
"""
OUT.write_text(HEADER + yaml.safe_dump({'npcs': npcs, 'topics': topics, 'houses': houses}, sort_keys=False,
                                       width=120, allow_unicode=False))
print(len(npcs), 'npcs', len(topics), 'topics', len(houses), 'houses')
