# XD-04 Witch Tower, L4: wiring.yml (first written by this script). Run: python3 gen_wiring.py <L4 folder>.
import sys
import yaml

L4 = sys.argv[1]
E = []


def ev(**kw):
    E.append(kw)


GEMS = '{177, 178, 179, 180, 181, 182, 183, 184, 185, 186}'


def skull_lua(scroll, name):
    return ("local paid = false\n"
            f"for _, g in ipairs({GEMS}) do\n"
            "    if not paid and HasItem(g) then\n"
            "        RemoveItem(g)\n"
            "        paid = true\n"
            "    end\n"
            "end\n"
            "if paid then\n"
            f"    GiveItem({scroll})\n"
            f"    evt.StatusText(\"The skull spits out a scroll of {name}. 'Pleasure doing business. Your nose is crooked.'\")\n"
            "else\n"
            "    evt.StatusText(\"'No gems, no scroll,' clacks the skull. 'Come back richer and prettier.'\")\n"
            "end")


ev(id='evt:arrive', preset='text', trigger='load', once=True,
   text="Green light flickers on black timber, and somewhere above, a cauldron bubbles.")

# Doors of the tower (Clanker's Laboratory's folding plank leaves): click to open and close.
for d, title in [('warden', "Warden's door"), ('larder', 'Larder door'), ('pens', 'Pen door'),
                 ('dormitory', 'Dormitory door'), ('mistress', "The mistress's door"),
                 ('schoolroom', 'Schoolroom doors')]:
    ev(id=f'evt:door_{d}', preset='door', source=f'door:{d}', title=title)
ev(id='evt:door_bedchamber', preset='door', source='door:bedchamber', title='Bedchamber door')
ev(id='evt:hatch', preset='door', source='door:hatch', title='Roof hatch')
ev(id='evt:cupboard', preset='door', source='door:cupboard', title='Wainscot', action='open',
   text="A panel of the wainscot is loose: behind it, a goblin's hoard in a cupboard.",
   notes="The secret cupboard (treasure: secret_container): a secret leaf that slides up on a click.")
ev(id='evt:bookcase', preset='door', source='door:bookcase', title='Bookcase', action='open',
   text="The bookcase rises into the wall with a groan. Behind it, a cage, and a sobbing child.",
   notes="link:vat_hall_hidden_cage: the secret bookcase door.")
ev(id='evt:crying', preset='text', source='plate:crying', trigger='step', once=True,
   text="Somewhere behind the bookcase, a child is crying.",
   notes="The clue to the hidden cage (a placed crying sound in the brief; MM7 projects take no sounds).")

for c, title in [('warden', 'Chest'), ('loft', 'Chest'), ('coven', 'Cabinet'), ('hoard', 'Cabinet')]:
    ev(id=f'evt:chest_{c}', preset='chest', source=f'chest:{c}', title=title)

# The Rosebud door (set:rosebud_door).
ev(id='evt:rosebud', preset='door', source='door:rosebud', title='The sleeping face', action='open',
   condition={'not': {'map_var': 'rosebud_open'}},
   else_effects=[{'text': 'The face sleeps; the way stands open.'}],
   question={'message': "A face carved in the door opens its stone eyes and smiles with too many teeth. "
                        "'The word, dearies. What is the word?'",
             'ask': 'Speak the word:', 'answers': ['Rosebud'],
             'wrong_text': "The face shuts its eyes and says nothing more. Your skin prickles."},
   sets={'map_var': 'rosebud_open'},
   text="'Rosebud,' sighs the face, and the door parts down the middle.",
   notes="set:rosebud_door / link:rosebud_door: the typed answer 'Rosebud' opens it for good. The brief's jinx on "
         "a wrong answer has no word (gap): a wrong answer only shows its line.")

# The ward (link:sanctum_roof_stair).
ev(id='evt:ward', preset='door', source='door:ward', title='A shimmering ward', action='open',
   condition={'qbit': 'm4_crusaders'},
   locked_text="The ward hums. It is keyed to an oath you have not sworn.",
   text="The ward knows the Crusaders' oath. It sinks hissing into the floor.",
   notes="Sealed until Valia names the party Crusaders (qbit m4_crusaders, set on X1).")
ev(id='evt:roof', preset='text', source='room:roof', trigger='step', once=True,
   text="Wind, and the whole of Toad Meadow below. Beyond the meadows the world simply ends, and the stars "
        "shine under it. Above you, a stair of cloud climbs into the sky.")
ev(id='evt:exit_door', preset='exit', source='exit:tower_door', title='The tower door: out to Toad Meadow',
   text='You push the tower door open into the meadow air.')
ev(id='evt:cloud_stair', preset='exit', source='exit:cloud_stair', title='The cloud stair',
   condition={'qbit': 'm4_crusaders'}, locked_text='The clouds will not bear your weight. Not yet.',
   text='You climb the stair of cloud into the sky.')

# The hoist (link:hoist, key:hoist_brake).
ev(id='evt:brake', preset='switch', source='switch:brake', title='Hoist brake', once=True,
   closes=['mover:hoist', 'door:gate_top'], opens=['door:gate_bottom'], sets={'map_var': 'hoist_released'},
   text="The brake comes off with a bang: the cage rattles away down the slot to the cauldron floor.",
   notes="poi:hoist_brake: the first pull sends the cage down and sets hoist_released; then it rides and is called "
         "from either end.")
ev(id='evt:hoist', preset='switch', source='mover:hoist', title='Hoist cage',
   condition={'map_var': 'hoist_released'}, locked_text='The cage is held fast by its brake.',
   toggles=['mover:hoist', 'door:gate_top', 'door:gate_bottom'],
   text='The winch creaks and the cage moves.')
ev(id='evt:call_top', preset='switch', source='switch:call_top', title='Call the hoist',
   condition={'map_var': 'hoist_released'}, locked_text='The cage is here, held fast by its brake.',
   opens=['mover:hoist', 'door:gate_top'], closes=['door:gate_bottom'], text='The cage comes up the slot.')
ev(id='evt:call_bottom', preset='switch', source='switch:call_bottom', title='Call the hoist',
   condition={'map_var': 'hoist_released'}, locked_text='Far above, the cage does not stir: its brake holds it.',
   closes=['mover:hoist', 'door:gate_top'], opens=['door:gate_bottom'], text='The cage comes down the slot.')

ev(id='evt:winch', preset='text', source='platform:winch', title='Winch drum',
   text="The hoist's rope is wound on this drum. The brake lever is on the north wall.")

# Cages (poi:cages): the warden's ring opens each; children run home.
ev(id='evt:cage_1', preset='script', source='deco:cage_1', title='Cage',
   condition={'item': 'warden_ring'},
   locked_text="The cage is locked. A boy with pointed ears looks at you: 'The warden has the ring!'",
   effects=[{'lua': (
       "if IsAtLeast(MapVar(boy_state), 2) then\n"
       "    evt.StatusText('The cage stands open and empty.')\n"
       "elseif IsAtLeast(MapVar(boy_state), 1) then\n"
       "    if HasItem(214) then\n"
       "        SetValue(MapVar(boy_state), 2)\n"
       "        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1)\n"
       "        SetQBit(QBit(110040))\n"
       "        AddValue(Experience, 500)\n"
       "        evt.StatusText('You touch the Alacorn to his ears: they shrink back, pink and round. He whoops and runs for home.')\n"
       "    else\n"
       "        evt.StatusText(\"'I'm not going home with goblin ears!' The boy will not budge.\")\n"
       "    end\n"
       "else\n"
       "    SetValue(MapVar(boy_state), 1)\n"
       "    evt.StatusText(\"The ring turns the lock. The boy steps out and stops: 'Not with these ears. Mum would die.'\")\n"
       "end")}],
   notes="set:cure_the_boy: open the cage (warden's ring), then use the Alacorn on the boy (click the cage again "
         "holding it): cured, he runs home (child_rescued_1). boy_state 0 caged, 1 out but waiting, 2 gone.")
for n, (grp, text, extra) in {
        2: (12, "The ring turns the lock. A girl with a green tinge to her skin tumbles out.", True),
        3: (13, "The ring turns the lock. The sobbing child wipes his nose, grins and runs.", False),
        4: (14, "The ring turns the lock. The child in the witches' bedchamber slips out and is gone down the stair.",
            False)}.items():
    eff = [{'lua': f"evt.SetMonGroupBit({grp}, MonsterBits.Invisible, 1)\nAddValue(Experience, 500)"},
           {'qbit': f'child_rescued_{n}'}]
    if extra:
        eff.append({'qbit': 'rosebud_heard'})
        eff.append({'message': "Before she runs she pulls you down and whispers in your ear: 'The door at the top "
                               "has a face. It wants a word. The word is Rosebud. Don't tell them I told you.' "
                               "Then she is gone, running for Toad Meadow."})
    ev(id=f'evt:cage_{n}', preset='script', source=f'deco:cage_{n}', title='Cage',
       condition={'all': [{'item': 'warden_ring'}, {'not': {'qbit': f'child_rescued_{n}'}}]},
       effects=eff, text=text + ' (Valia will hear of it.)',
       else_effects=[{'lua': f"if IsQBitSet(QBit({110039 + n})) then evt.StatusText('The cage stands open and empty.') "
                             "else evt.StatusText(\"The cage is locked. 'The warden has the ring,' whispers the child.\") end"}],
       notes=f"poi:cages: child {n}" + (" whispers the password (rosebud_heard)." if extra else '.'))

# The vats (set:vats): per character (player bits, no word: Lua).
ev(id='evt:vat_toad', preset='script', source='deco:vat_toad', title='Vat with a toad on its lid',
   condition={'lua': 'not IsPlayerBitSet(PlayerBit(11041))'},
   effects=[{'lua': ("local r = evt.RandomBetween(1, 7)\n"
                     "if r == 1 then AddValue(BaseMight, 2)\n"
                     "elseif r == 2 then AddValue(BaseIntellect, 2)\n"
                     "elseif r == 3 then AddValue(BasePersonality, 2)\n"
                     "elseif r == 4 then AddValue(BaseEndurance, 2)\n"
                     "elseif r == 5 then AddValue(BaseAccuracy, 2)\n"
                     "elseif r == 6 then AddValue(BaseSpeed, 2)\n"
                     "else AddValue(BaseLuck, 2) end\n"
                     "SetPlayerBit(PlayerBit(11041))")}],
   else_effects=[{'text': 'The brew tastes of mud and does nothing more for you.'}],
   text="It tastes of mud and nettles, and something in you grows stronger. (+2 to one stat, permanent)",
   notes="poi:vats, the good vat: +2 to a stat drawn at random, once per character (player bit 11041, provisional).")
ev(id='evt:vat_bubbling', preset='script', source='deco:vat_bubbling', title='Bubbling vat',
   effects=[{'set': {'var': 'PoisonedGreen', 'value': 1}}, {'damage': {'amount': 5, 'kind': 'poison',
                                                                       'who': 'current'}}],
   text="Agnes's brew burns all the way down. You are poisoned.", notes='poi:vats: the bubbling vat poisons.')
ev(id='evt:vat_green', preset='script', source='deco:vat_green', title='Green vat',
   effects=[{'set': {'var': 'Weak', 'value': 1}}],
   text='Your skin turns green, and your knees turn to water. (Weak)',
   notes="poi:vats: the green vat turns the drinker green: Weak until cured or rested.")

# Readables.
ev(id='evt:slate', preset='script', source='panel:slate', title='The slate',
   effects=[{'message': "HOW TO BE A PROPER GOBLIN.  1. Never say please.  2. Never wash.  3. Forget your name.  "
                        "--  In the corner, small and half rubbed out, a child has scratched: Rosebud."}],
   notes='poi:slate_board: the lesson, and the password half rubbed out.')
ev(id='evt:recipe', preset='script', source='panel:recipe', title='A recipe card',
   effects=[{'message': "Strength brew - the vat with the TOAD on its lid. NOT the bubbling one (Agnes). NOT the "
                        "green one, unless you want to be green."}],
   notes='poi:recipe_card: names the good vat.')

# The talking skulls (poi:talking_skulls): a scroll for a gem.
for n, (scroll, name, school) in {1: (358, 'Mind Blast', 'Mind'), 2: (367, 'Heal', 'Body'),
                                  3: (314, 'Sparks', 'Air')}.items():
    ev(id=f'evt:skull_{n}', preset='script', source=f'deco:skull_{n}', title=f'Talking skull ({school})',
       question={'message': f"The skull clacks its jaw. 'A scroll of {name}, dearie? One gem. A shiny one. "
                            "And do something about that face.'",
                 'ask': 'Pay a gem (Yes/No)?', 'answers': ['Yes', 'Y'], 'wrong_text': "'Cheapskate,' says the skull."},
       effects=[{'lua': skull_lua(scroll, name)}],
       notes=f"poi:talking_skulls: sells {name} scrolls ({school}) for one gem of any kind (the brief: 5 to 10).")

# The cauldron (harmful liquid) and the boil-over (set:boil_over).
ev(id='evt:cauldron', preset='script', source='platform:cauldron', trigger='step',
   effects=[{'damage': {'amount': 15, 'kind': 'body'}}, {'set': {'var': {'map_var': 'on_pier'}, 'value': 0}}],
   text="The brew scalds and stings: you flounder out of the cauldron.",
   notes="The cauldron's top as a harmful floor (Body damage each time the party lands in it).")
ev(id='evt:pier_on', preset='script', source='room:shaft_bridge', trigger='step',
   sources=['platform:bridge', 'platform:landing'],
   effects=[{'set': {'var': {'map_var': 'on_pier'}, 'value': 1}}])
ev(id='evt:pier_off', preset='script', source='room:coven_sanctum', trigger='step', sources=['room:cauldron_chamber'],
   effects=[{'set': {'var': {'map_var': 'on_pier'}, 'value': 0}}])
ev(id='evt:alacorn_taken', preset='script', trigger='timer', every=1, once=True, condition={'item': 'alacorn'},
   effects=[{'qbit': 'alacorn_taken'}, {'set': {'var': {'map_var': 'boil'}, 'value': 1}},
            {'lights_on': ['light:boil', 'light:boil_pier']}, {'lights_off': 'light:alacorn'},
            {'summon': {'slot': 1, 'at': [-3072, 1300, 1920], 'count': 2, 'tier': 'b'}},
            {'lua': 'evt.CameraShake(1.0, 2.0)'}],
   text="The cauldron roars and boils over: green steam boils up the shaft! Get off the bridge!",
   notes="goal:alacorn / set:boil_over: taking the Alacorn sets alacorn_taken, the shaft fills with green steam that "
         "burns on the pier and the bridge for about a minute, and goblins come up behind (two Hobgoblins at the "
         "Rosebud landing).")
ev(id='evt:boil_count', preset='script', trigger='timer', every=2,
   condition={'map_var': {'name': 'boil', 'at_least': 1, 'below': 31}},
   effects=[{'add': {'var': {'map_var': 'boil'}, 'value': 1}}], notes='About a minute of boiling over.')
ev(id='evt:steam', preset='script', trigger='timer', every=2,
   condition={'all': [{'map_var': {'name': 'boil', 'at_least': 1, 'below': 31}}, {'map_var': 'on_pier'}]},
   effects=[{'damage': {'amount': 6, 'kind': 'body'}}], text='The steam scalds you!')
ev(id='evt:boil_end', preset='script', trigger='timer', every=2, once=True,
   condition={'map_var': {'name': 'boil', 'at_least': 31}},
   effects=[{'lights_off': ['light:boil', 'light:boil_pier']}], text='Far below, the cauldron settles to a simmer.')

# The Head Witch (set:head_witch).
ev(id='evt:circle', preset='script', source='platform:circle_ne', trigger='step',
   sources=['platform:circle_nw', 'platform:circle_se', 'platform:circle_sw'], once=True,
   effects=[{'set': {'var': {'map_var': 'circle_trod'}, 'value': 1}}])
ev(id='evt:familiars', preset='script', trigger='timer', every=2, once=True,
   condition={'any': [{'kills': {'group': 6}}, {'map_var': 'circle_trod'}]},
   effects=[{'show_actors': 5}],
   text="The Head Witch shrieks a word: the witch-marks split, and her familiars crawl out of the floor!",
   notes="The brief's 'at half health' cannot be tested (gap): her familiars come when her two sisters have fallen "
         "or the party treads on the witch-mark circle.")
ev(id='evt:head_witch_dead', preset='script', trigger='timer', every=2, once=True,
   condition={'kills': {'monster': 'monster:head_witch'}}, effects=[{'qbit': 'head_witch_slain'}],
   text='The Head Witch shrieks, shrivels and is still.', notes='goal:head_witch.')

out = {'format': 0,
       'variables': ['boy_state', 'rosebud_open', 'hoist_released', 'boil', 'on_pier', 'circle_trod'],
       'events': E,
       'notes': "Every mechanism is a preset with conditions and effects. Lua only where no word fits: the cages' "
                "branches and experience, the vats' per-character bits and random stat, the skulls' gem payment, "
                "the camera shake."}
yaml.safe_dump(out, open(L4 + '/wiring.yml', 'w'), sort_keys=False, width=1000, allow_unicode=True)
