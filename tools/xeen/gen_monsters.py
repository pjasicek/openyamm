"""Xeen monster rows: monster_data.txt, monster_descriptors.txt, bolster_monsters.txt (the NoArena kind),
english/place_mon.txt (placed monsters' names), relations.yml and modifiers.yml from source/monsters.yml
(MONSTERS_AND_ITEMS.md section 1 for the formulas; the file's header for its fields).

Each row borrows from its family's `stand_in` or `sprites` descriptor family (an installed one; `sprites` once S has
bound the family to its own model): the descriptor's sprites, sounds, size and hit material, and that family's
monster row's speed, flight, movement, AI and blood. Everything that decides a fight (level, HP, AC, damage, recovery,
resistances, conditions, spells, treasure) comes from the formulas. `skin` and `model` are records for S; no table
has a column for them.
"""

from __future__ import annotations

import copy
import math

import xeenlib
from xeenlib import BuildError

SOURCE = 'monsters.yml'
SCHOOLS = ['fire', 'air', 'water', 'earth', 'mind', 'spirit', 'body', 'light', 'dark', 'phys']
MASTERIES = {'N', 'E', 'M', 'G'}
BONUSES = {'poison1', 'poison2', 'poison3', 'disease1', 'disease2', 'disease3', 'curse', 'weak', 'asleep', 'afraid',
           'drunk', 'insane', 'paralyze', 'uncon', 'dead', 'stone', 'errad', 'brkitem', 'brkarmor', 'brkweapon',
           'steal', 'age', 'drainsp'}
LETHAL_BONUSES = {'stone', 'dead', 'errad'}
LETHAL_BONUS_MIN_LEVEL = 27
DAMAGE_TYPES = {'Phys', 'Fire', 'Air', 'Water', 'Earth', 'Mind', 'Spirit', 'Body', 'Light', 'Dark', 'Ener'}
RELATIONS = {'friendly', 'close', 'short', 'medium', 'long'}
TIER_LETTERS = 'ABCDEFGHIJ'
# D-39: XD-20's arena draws from 11010-11699; rows taller than this never enter it (the descriptor's height).
ARENA_MAX_HEIGHT = 1000
# The engine's monster kinds (MonsterTable parseMonsterKindToken) a family or tier may name as `kind`; NoArena is
# given by the rules above.
MONSTER_KINDS = {'Undead', 'Dragon', 'Demon', 'Ogre', 'Elemental', 'Titan', 'Elf', 'Swimmer', 'Immobile', 'Peasant',
                 'NoCorpse'}


def curve_at(points, level):
    """Straight lines between (level, value) points; flat beyond the ends."""
    if level <= points[0][0]:
        return float(points[0][1])
    for (left_level, left_value), (right_level, right_value) in zip(points, points[1:]):
        if level <= right_level:
            share = (level - left_level) / (right_level - left_level)
            return left_value + share * (right_value - left_value)
    return float(points[-1][1])


def band_at(bands, level):
    """The value of the first band whose upper level is at least `level`."""
    for upper, value in bands:
        if level <= upper:
            return value
    return bands[-1][1]


def dice_for(average):
    """A dice expression whose average is about `average`: a few dice for spread, the rest as a bonus."""
    average = max(1.0, average)
    count = max(1, round(average / 7))
    sides = max(2, min(20, round(average * 1.2 / count - 1)))
    bonus = round(average - count * (sides + 1) / 2)
    return f'{count}D{sides}' + (f'+{bonus}' if bonus > 0 else '')


def gold_dice(average):
    if average < 1:
        return ''
    sides = 4 if average < 40 else 8 if average < 200 else 10 if average < 800 else 20
    count = max(1, round(average / ((sides + 1) / 2)))
    return f'{count}D{sides}'


class Monsters:
    def __init__(self, ctx, source):
        self.ctx = ctx
        self.curves = source.get('curves') or {}
        self.defaults = source.get('defaults') or {}
        self.themes = source.get('themes') or {}
        self.families = source.get('families') or {}
        self.stand_in_rows = self._stand_in_rows()
        self.stand_in_descriptors = self._stand_in_descriptors()
        self.known_spells = self._known_spells()
        self.sound_ids = self._world_sounds()

    # Engine data the rows borrow --------------------------------------------------------------------------------

    def _world_sounds(self):
        """Sound name -> id from the world's audio/sounds.txt (lane AU's table; devdocs/xeen/AUDIO.md)."""
        path = xeenlib.WORLD / 'audio' / 'sounds.txt'
        sounds = {}
        if not path.exists():
            return sounds
        for line in path.read_text(encoding='utf-8').splitlines():
            cells = line.split('\t')
            if len(cells) >= 2 and not line.startswith('/') and cells[1].strip().isdigit():
                sounds[cells[0].strip()] = int(cells[1])
        return sounds

    def _stand_in_rows(self):
        rows = {}
        tables = [xeenlib.engine_table('monster_data.txt')]
        mm9 = xeenlib.WORLDS / 'mm9' / 'data_tables' / 'monster_data.txt'
        if mm9.exists():
            tables.append(xeenlib.read_tsv(mm9))
        for table in tables:
            for row in table:
                if xeenlib.parse_int(xeenlib.cell(row, 0)) is not None:
                    rows.setdefault(xeenlib.cell(row, 2), row)
        return rows

    def _stand_in_descriptors(self):
        rows = {}
        tables = [xeenlib.engine_table('monster_descriptors.txt')]
        mm9 = xeenlib.WORLDS / 'mm9' / 'data_tables' / 'monster_descriptors.txt'
        if mm9.exists():
            tables.append(xeenlib.read_tsv(mm9))
        for table in tables:
            for row in table:
                if xeenlib.parse_int(xeenlib.cell(row, 0)) is not None:
                    rows.setdefault(xeenlib.cell(row, 1), row)
        return rows

    def _known_spells(self):
        names = set()
        for row in self.stand_in_rows.values():
            for column in (25, 27):
                text = xeenlib.cell(row, column).strip('"')
                if text and text != '0':
                    names.add(text.split(',')[0].strip())
        return names

    # Numbers ------------------------------------------------------------------------------------------------------

    def hit_points(self, level):
        return round(level * level / 10 + 3 * level)

    def experience(self, level):
        return level * (level + 10)

    def resist_base(self, level):
        return band_at(self.curves['resist_base'], level)

    def resist_value(self, value, base, where):
        text = str(value).strip()
        if text == 'imm':
            return 'Imm'
        if text == 'base':
            return base
        if text == '2x+20':
            return 2 * base + 20
        if text.startswith('+'):
            return base + int(text[1:])
        if text.lstrip('-').isdigit():
            return int(text)
        raise BuildError(f'{where}: resistance {value!r} is not imm, base, +N, 2x+20 or a number')

    def treasure(self, level, experience, boss, loot_kind, where, item_chance_x=1):
        treasure_level = band_at(self.curves['treasure_level'], level)
        gold = experience * band_at(self.curves['gold_per_1000_xp'], level) / 1000
        chance = round(experience * band_at(self.curves['items_per_million_xp'], level) / 1_000_000 * 100
                       * item_chance_x)
        if boss:
            settings = self.curves.get('boss') or {}
            gold *= settings.get('gold_x', 3)
            chance = settings.get('item_chance', 100)
            treasure_level = min(6, treasure_level + settings.get('treasure_step', 1))
        dice = gold_dice(gold)
        kind = loot_kind or ''
        if chance <= 0:
            return dice or '0'
        item = f'L{treasure_level}{kind}'
        prefix = '' if chance >= 100 else f'{min(chance, 75)}%'
        return f'{prefix}{dice}+{item}' if dice else f'{prefix}{item}'

    # Rows ---------------------------------------------------------------------------------------------------------

    def merged(self, family, tier):
        """The family's settings with the tier's over them; resistances merged school by school."""
        merged = dict(self.defaults)
        merged.update({key: value for key, value in family.items() if key not in ('tiers', 'bosses', 'resist')})
        merged.update({key: value for key, value in tier.items() if key != 'resist'})
        resist = {}
        theme = merged.get('theme')
        if theme:
            if theme not in self.themes:
                raise BuildError(f"{SOURCE}: unknown theme {theme!r}")
            resist.update(self.themes[theme])
        resist.update(family.get('resist') or {})
        resist.update(tier.get('resist') or {})
        merged['resist'] = resist
        return merged

    def spell_cells(self, spell, where):
        if not spell:
            return [0, 0]
        if len(spell) != 4:
            raise BuildError(f'{where}: a spell is [name, mastery, skill, chance %]')
        name, mastery, skill, chance = spell
        if name not in self.known_spells:
            raise BuildError(f'{where}: spell {name!r} is not one the monster table knows')
        if str(mastery) not in MASTERIES:
            raise BuildError(f'{where}: mastery {mastery!r} is not N, E, M or G')
        return [chance, xeenlib.quote_text(f'{name},{mastery},{skill}')]

    def monster_row(self, row_id, name, picture, level, settings, stand_in_picture, boss, where):
        stand_in = self.stand_in_rows.get(stand_in_picture)
        if stand_in is None:
            raise BuildError(f'{where}: no monster row wears the stand-in {stand_in_picture!r}')
        hp_x = settings.get('hp_x', (self.curves.get('boss') or {}).get('hp_x', 3) if boss else 1)
        experience = self.experience(level)
        hit_points = round(self.hit_points(level) * hp_x)
        armour = round(curve_at(self.curves['ac'], level) * settings.get('ac_x', 1))
        damage = settings.get('damage') or dice_for(curve_at(self.curves['damage'], level))
        recovery = settings.get('recovery') or band_at(self.curves['recovery'], level)

        bonus = settings.get('bonus') or 0
        if bonus and str(bonus).lower().rsplit('x', 1)[0] not in BONUSES:
            raise BuildError(f'{where}: unknown bonus {bonus!r}')
        # D-119 (F54, 2026-11-24): a touch that petrifies, kills or eradicates ends a solo run; MM6-MM8 give one to no
        # monster below level 27 (the Basilisk). The Gorgon Sprite (16) and the Medusa Sprite (10) had Stone.
        if bonus and str(bonus).lower().rsplit('x', 1)[0] in LETHAL_BONUSES and level < LETHAL_BONUS_MIN_LEVEL:
            raise BuildError(f'{where}: bonus {bonus!r} at level {level}: Stone, Dead and Errad need level '
                             f'{LETHAL_BONUS_MIN_LEVEL} or more (MM6-MM8 have none below it); give a lesser bonus '
                             '(Weak, Curse, Paralyze ...)')
        attack_type = settings.get('type') or xeenlib.cell(stand_in, 17) or 'Phys'
        if attack_type not in DAMAGE_TYPES:
            raise BuildError(f'{where}: unknown damage type {attack_type!r}')
        missile = settings.get('missile', xeenlib.cell(stand_in, 19) or 0)

        attack2 = settings.get('attack2')
        attack2_cells = [0, 0, 0, 0]
        if attack2:
            kind, dice, missile2, chance = attack2
            if dice == 'curve':
                dice = dice_for(curve_at(self.curves['damage'], level) * 0.7)
            attack2_cells = [chance, kind, dice, missile2]

        base = self.resist_base(level)
        resist = settings['resist']
        unknown = set(resist) - set(SCHOOLS)
        if unknown:
            raise BuildError(f'{where}: unknown resistance schools {sorted(unknown)}')
        resist_cells = []
        for school in SCHOOLS:
            default = 0 if school == 'phys' else base
            resist_cells.append(self.resist_value(resist[school], base, where) if school in resist else default)

        boss_loot = boss and settings.get('boss_loot', True)
        treasure = self.treasure(level, experience, boss_loot, settings.get('loot_kind'), where,
                                 settings.get('item_chance_x', 1))
        if settings.get('fly') not in (None, 'Y', 'N'):
            raise BuildError(f"{where}: fly {settings['fly']!r} is not Y or N")
        fly = settings.get('fly') or xeenlib.cell(stand_in, 9) or 'N'
        # A ranged flyer (X2 p8, a player, 2026-11-24: "the sprites are always in the air"). A flying row with a
        # missile is MM6-MM8's ranged flyer: outdoors it hovers its radius + 512 above the party and circles it at
        # range (AI_Pursue's WantedZ; OutdoorWorldRuntime's flying ranged pursuit height), never in melee reach; a
        # melee flyer comes down to the party (MM's harpies, gargoyles, bats, wyverns). The Sprites took the Will o'
        # Wisp's Light missile (and their own Air) and stayed out of reach, where the source's sprites have no ranged
        # attack. Such a row says `ranged_flyer: "<why>"` (family or tier: the source's R or A flag, or MM's
        # ranged-flyer kinds: wisps, eyes, elementals, dragons, constructs), else the build stops.
        missiles = [missile] + ([attack2[2]] if attack2 else [])
        if fly == 'Y' and any(str(value) not in ('0', '', 'None') for value in missiles) \
                and not settings.get('ranged_flyer'):
            raise BuildError(f'{where}: a flyer with a missile ({", ".join(str(value) for value in missiles)}) hovers '
                             'out of melee reach (MM6-MM8\'s ranged flyer); give it `missile: 0` (a melee flyer that '
                             'comes down to the party) or say `ranged_flyer: "<why>"`')
        cells = [
            row_id, name, picture, level, hit_points, armour, experience, treasure,
            settings.get('blood', xeenlib.cell(stand_in, 8) or 1), fly,
            settings.get('move') or xeenlib.cell(stand_in, 10) or 'Med',
            settings.get('ai') or xeenlib.cell(stand_in, 11) or 'Aggress',
            xeenlib.cell(stand_in, 12) or 4,
            settings.get('speed') or xeenlib.cell(stand_in, 13) or 200,
            recovery, 0, bonus, attack_type, damage, missile,
        ] + attack2_cells + self.spell_cells(settings.get('spell'), where) \
            + self.spell_cells(settings.get('spell2'), where) + resist_cells \
            + [xeenlib.quote_text(str(settings['special'])) if settings.get('special') else 0]
        return cells, {'id': row_id, 'name': name, 'level': level, 'hp': hit_points, 'xp': experience,
                       'treasure': treasure}

    def descriptor_row(self, row_id, picture, stand_in_descriptor, settings, where):
        source = self.stand_in_descriptors.get(stand_in_descriptor)
        if source is None:
            raise BuildError(f'{where}: no descriptor {stand_in_descriptor!r} to borrow from')
        row = list(source)
        row[0] = str(row_id)
        row[1] = picture
        # A sound set (`sounds: xeen_toad`, AUDIO.md table (a)): <set>_attack, _death, _wince, _fidget into the
        # AttackSoundId, DeathSoundId, WinceSoundId and AwareSoundId columns (Aware plays as the idle fidget).
        if settings.get('sounds'):
            for column, part in ((7, 'attack'), (8, 'death'), (9, 'wince'), (10, 'fidget')):
                name = f"{settings['sounds']}_{part}"
                if name not in self.sound_ids:
                    raise BuildError(f'{where}: sound {name!r} is not in worlds/xeen/audio/sounds.txt')
                sound_id = self.sound_ids[name]
                if not 0 < sound_id < 65536:
                    raise BuildError(f'{where}: sound {name} has id {sound_id}; the descriptor columns are 16-bit')
                row[column] = str(sound_id)
        # The body's own collision size where it differs from the borrowed sprites' (the mole on the rat's sprites).
        for column, field in ((2, 'height'), (3, 'radius')):
            if field in settings:
                value = settings[field]
                if not isinstance(value, int) or value <= 0:
                    raise BuildError(f'{where}: {field} {value!r} is not a positive whole number')
                row[column] = str(value)
        # A borrowed ToHitRadius (projectiles; 0 means the body's radius) follows a new radius: the Behemoth's 160
        # would let bolts strike the sand worm's 130 mound from 30 units off.
        if 'radius' in settings and int(row[5] or 0) > 0:
            row[5] = str(settings['radius'])
        # The corpse (feedback F54, 2026-11-24): a descriptor without a dead sprite (SpriteDead null: MM's wisps,
        # elementals and robots) leaves no body when the monster dies, and the game then drops none of its table
        # loot (gold and item: MM6-MM8's rule). Such a row must say which it is: `corpse: dying` keeps a body (the
        # dying sprite stands for the dead one; the model ends in its death pose), `corpse: none` vanishes as in
        # MM6-MM8 and loses its loot. The Xeen sprites wore the Will o' Wisp's descriptor and dropped nothing.
        corpse = settings.get('corpse')
        if corpse not in (None, 'dying', 'none'):
            raise BuildError(f'{where}: corpse {corpse!r} is not dying or none')
        if row[17].strip().lower() == 'null':
            if corpse is None:
                raise BuildError(f'{where}: {stand_in_descriptor!r} has no dead sprite, so the monster leaves no '
                                 f'corpse and drops no loot; set `corpse: dying` (a body) or `corpse: none` (vanishes)')
            if corpse == 'dying':
                row[17] = row[16]
        # The struck body's material where the borrowed sprites' is wrong (the sprites are fey, not wisps of light).
        if settings.get('hit_material'):
            row[-1] = str(settings['hit_material'])
        return row


def tier_entries(family_key, family):
    """(letter, tier dict) in order; A-C are the family's spawnable tiers, later letters extra rows."""
    tiers = family.get('tiers') or {}
    for letter in 'ABC':
        if letter not in tiers:
            raise BuildError(f'{SOURCE}: family {family_key} has no tier {letter} (a spawn slot may pick any of A-C)')
    return [(letter, tiers[letter]) for letter in TIER_LETTERS if letter in tiers]


def borrowed_family(family_key, family):
    """The descriptor family the rows copy: `stand_in` (no model of its own yet) or `sprites` (bound by S)."""
    names = [key for key in ('stand_in', 'sprites') if family.get(key)]
    if len(names) != 1:
        raise BuildError(f'{SOURCE} {family_key}: a family needs exactly one of stand_in or sprites, not {names}')
    return family[names[0]]


def check_records(family_key, family):
    """`skin` and `model` are strings where given (family model; tier and boss skin and model)."""
    entries = [('', family)] + [(f' {letter}', tier) for letter, tier in (family.get('tiers') or {}).items()] \
        + [(f" boss {boss.get('key')}", boss) for boss in family.get('bosses') or []]
    for suffix, entry in entries:
        for field in ('skin', 'model'):
            if field in entry and not (isinstance(entry[field], str) and entry[field]):
                raise BuildError(f'{SOURCE} {family_key}{suffix}: {field} {entry[field]!r} is not a name')
        if suffix == '' and 'skin' in entry:
            raise BuildError(f'{SOURCE} {family_key}: skin belongs on each tier and boss, not the family')


def own_faction(factions, party_relations, family_key, name, row_id, party, where):
    """Adds a row to the faction <family>_<name> (or <other family>_<name> for `other/name`: the Kennel Sabertooth in
    the pass ogres' faction; or another family's own faction for `other/`: the Lesser Air Elemental 11624 with the air
    elementals, D-58) with its relation to the party; rows of one faction agree on it."""
    text = str(name)
    key = text.rstrip('/') if text.endswith('/') else text.replace('/', '_') if '/' in text else f'{family_key}_{name}'
    factions.setdefault(key, []).append(row_id)
    if party is None:
        if key not in party_relations:
            raise BuildError(f'{where}: faction {name!r} has no `party` relation on its first row')
        return
    relation = relation_name(party, where)
    if party_relations.setdefault(key, relation) != relation:
        raise BuildError(f'{where}: faction {name!r} has two relations to the party')


def monster_kinds(settings, where):
    """A family's or tier's `kind` (one name or a list): the engine's monster kinds, the first the Type column."""
    value = settings.get('kind')
    row_kinds = value if isinstance(value, list) else [value] if value else []
    for kind in row_kinds:
        if kind not in MONSTER_KINDS:
            raise BuildError(f'{where}: kind {kind!r} is not one of {sorted(MONSTER_KINDS)}')
    return row_kinds


def relation_name(value, where):
    text = str(value).lower()
    if text not in RELATIONS:
        raise BuildError(f'{where}: relation {value!r} is not one of {sorted(RELATIONS)}')
    return text


def build(ctx):
    source = ctx.load_source(SOURCE)
    monsters = Monsters(ctx, source)
    data = ctx.table('monster_data.txt', sources=[f'source/{SOURCE}'], domain='monsters',
                     engine='monster_data.txt', header_rows=4)
    descriptors = ctx.table('monster_descriptors.txt', sources=[f'source/{SOURCE}'], domain='monsters',
                            engine='monster_descriptors.txt', header_rows=3)

    row_ids: dict[str, int] = {}
    families_shared: dict[str, dict] = {}
    pictures: set[str] = set()
    factions: dict[str, list[int]] = {}
    party_relations: dict[str, str] = {}
    modifiers: dict[int, list] = {}
    no_arena: dict[int, str] = {}   # row id -> name, for bolster_monsters.txt's NoArena kind (D-39)
    kinds: dict[int, list[str]] = {}  # row id -> monster kinds (`kind`: Demon, Undead, ...; bolster_monsters Type)
    report = []

    for family_key, family in monsters.families.items():
        where = f'{SOURCE} {family_key}'
        block = family.get('block')
        picture = family.get('picture')
        if not isinstance(block, int) or not picture:
            raise BuildError(f'{where}: a family needs block and picture')
        stand_in = borrowed_family(family_key, family)
        check_records(family_key, family)
        if picture in pictures:
            raise BuildError(f'{where}: picture {picture!r} is used twice')
        pictures.add(picture)
        ids = []
        faction_ids = []
        for index, (letter, tier) in enumerate(tier_entries(family_key, family)):
            row_id = tier.get('id', block + index)
            # Tiers A-C sit at block+0..2 unless they name their ids (a second family in a block: the Darkside
            # sprites at 11534-11536, D-23); every id stays inside the block.
            if letter in 'ABC' and 'id' not in tier and row_id != block + index:
                raise BuildError(f'{where} {letter}: tiers A-C sit at block+0..2')
            if not block <= row_id <= block + 9:
                raise BuildError(f'{where} {letter}: id {row_id} is outside its family block {block}-{block + 9}')
            look = tier.get('look', letter)
            tier_picture = f'{picture} {letter}'
            settings = monsters.merged(family, tier)
            # An extra tier may borrow another installed descriptor whole (`stand_in: ElemAir A` on the tier: XD-19's
            # air, water and earth guards in the fire elementals' family, D-47); else the family's, by `look`.
            borrowed = tier['stand_in'] if letter not in 'ABC' and tier.get('stand_in') else f'{stand_in} {look}'
            if tier.get('stand_in') and letter in 'ABC':
                raise BuildError(f'{where} {letter}: tiers A-C wear the family\'s descriptors (a slot spawns them)')
            cells, info = monsters.monster_row(row_id, tier['name'], tier_picture, int(tier['level']), settings,
                                               borrowed, False, f'{where} {letter}')
            data.add(cells, origin=f'{family_key}.{letter}')
            descriptor = monsters.descriptor_row(row_id, tier_picture, borrowed, settings, f'{where} {letter}')
            descriptors.add(descriptor, origin=f'{family_key}.{letter}')
            # NoArena (D-39): an extra tier is placed only; `no_arena` on the family or tier; a body too tall.
            if letter not in 'ABC' or settings.get('no_arena') or int(descriptor[2]) > ARENA_MAX_HEIGHT:
                no_arena[row_id] = tier['name']
            row_ids[f'{family_key}.{letter}'] = row_id
            ids.append(row_id)
            kinds[row_id] = monster_kinds(settings, f'{where} {letter}')
            # A tier's modifiers, else the family's (the octopods' swimmer profile, D-36); bosses keep their own.
            tier_modifiers = tier.get('modifiers', family.get('modifiers'))
            if tier_modifiers:
                modifiers[row_id] = copy.deepcopy(tier_modifiers)  # no YAML anchors in the output
            if tier.get('party') or tier.get('faction'):
                # A tier with its own relation to the party (Castle Burlock's King's Guard) is a faction of its own;
                # `faction` names one that several rows share (Graalg and his Brutes, D-23).
                own_faction(factions, party_relations, family_key, tier.get('faction') or letter.lower(), row_id,
                            tier.get('party'), f'{where} {letter}')
            else:
                faction_ids.append(row_id)
            report.append((family_key, letter, info, tier_picture, tier.get('model', family.get('model', '')),
                           tier.get('stand_in') or stand_in))
        for boss in family.get('bosses') or []:
            boss_where = f"{where} boss {boss.get('key')}"
            if not boss.get('key') or not isinstance(boss.get('id'), int):
                raise BuildError(f'{boss_where}: a boss needs key and id')
            if not block <= boss['id'] <= block + 9:
                raise BuildError(f'{boss_where}: id {boss["id"]} is outside its family block {block}-{block + 9}')
            look = boss.get('look', 'C')
            # `picture` where two bosses share a display name (the coven's Head Witch 11173 and XD-04's 11163, D-42).
            boss_picture = boss.get('picture') or f"Xeen {boss['name']}"
            if boss_picture in pictures:
                raise BuildError(f'{boss_where}: picture {boss_picture!r} is used twice')
            pictures.add(boss_picture)
            settings = monsters.merged(family, boss)
            cells, info = monsters.monster_row(boss['id'], boss['name'], boss_picture, int(boss['level']), settings,
                                               f'{stand_in} {look}', True, boss_where)
            data.add(cells, origin=boss['key'])
            descriptors.add(monsters.descriptor_row(boss['id'], boss_picture, f'{stand_in} {look}', settings,
                                                    boss_where),
                            origin=boss['key'])
            no_arena[boss['id']] = boss['name']   # every boss (D-39)
            kinds[boss['id']] = monster_kinds(settings, boss_where)
            row_ids[boss['key']] = boss['id']
            ids.append(boss['id'])
            if boss.get('party') or boss.get('faction'):
                own_faction(factions, party_relations, family_key, boss.get('faction') or boss['key'], boss['id'],
                            boss.get('party'), boss_where)
            else:
                faction_ids.append(boss['id'])
            if boss.get('modifiers'):
                modifiers[boss['id']] = boss['modifiers']
            report.append((family_key, 'boss', info, boss_picture, boss.get('model', family.get('model', '')),
                           stand_in))
        # Rows of other families may have joined this family's faction (`faction: <family>/`), before or after it.
        factions.setdefault(family_key, []).extend(faction_ids)
        relation = relation_name(family.get('party', monsters.defaults.get('party', 'long')), where)
        if party_relations.setdefault(family_key, relation) != relation:
            raise BuildError(f'{where}: a row joining this family\'s faction has another relation to the party')
        families_shared[family_key] = {'picture': picture, 'ids': ids, 'name': family.get('name', family_key)}

    # Named peaceful characters placed on maps (Crodo in his cell): one row each, friendly to the party.
    for character in source.get('characters') or []:
        where = f"{SOURCE} characters {character.get('key')}"
        if not character.get('key') or not isinstance(character.get('id'), int) or not character.get('stand_in'):
            raise BuildError(f'{where}: a character needs key, id and stand_in (a descriptor)')
        # `picture` where two characters share a display name (Queen Kalindra cursed in DD-14, wedded on P5; D-56).
        char_picture = character.get('picture') or f"Xeen {character['name']}"
        if char_picture in pictures:
            raise BuildError(f'{where}: picture {char_picture!r} is used twice')
        pictures.add(char_picture)
        settings = monsters.merged({}, character)
        cells, info = monsters.monster_row(character['id'], character['name'], char_picture, int(character['level']),
                                           settings, character['stand_in'], False, where)
        cells[7] = 0  # a peaceful character carries no loot
        data.add(cells, origin=character['key'])
        descriptors.add(monsters.descriptor_row(character['id'], char_picture, character['stand_in'], settings, where),
                        origin=character['key'])
        row_ids[character['key']] = character['id']
        if character.get('modifiers'):
            modifiers[character['id']] = copy.deepcopy(character['modifiers'])  # Lacey's wander radius (D-50)
        no_arena[character['id']] = character['name']
        factions[f"character_{character['key']}"] = [character['id']]
        party_relations[f"character_{character['key']}"] = relation_name(character.get('party', 'friendly'), where)
        report.append(('characters', 'named', info, char_picture, character.get('note', ''), character['stand_in']))

    # Rows friendly to the party at load (their faction's base relation) never fight in the arena either.
    names = {info['id']: info['name'] for _, _, info, _, _, _ in report}
    for key, relation in party_relations.items():
        if relation == 'friendly':
            for row_id in factions.get(key, []):
                no_arena.setdefault(row_id, names[row_id])
    # The engine reads monster kinds from bolster_monsters (Type, ExtraType): a family's `kind` (the Slayer Sword's
    # SlayingDemon, the slaying enchantments, the undead spells) and NoArena. The other columns stay empty, which the
    # bolster rules read as no row at all.
    bolster = ctx.table('bolster_monsters.txt', sources=[f'source/{SOURCE}'], domain='monsters',
                        engine='bolster_monsters.txt', header_rows=1)
    for row_id in sorted(set(no_arena) | {row_id for row_id, row_kinds in kinds.items() if row_kinds}):
        row_kinds = kinds.get(row_id) or []
        extra = row_kinds[1:] + (['NoArena'] if row_id in no_arena else [])
        bolster.add([row_id, names[row_id], row_kinds[0] if row_kinds else '', ','.join(extra), '', '', '', 0, True,
                     False, False, False, False, False], origin=f'kinds {row_id}')

    # Names of placed indoor monsters (place_mon, merge point 17): a studio `name:` takes the row of that name.
    place_names = ctx.table('english/place_mon.txt', sources=[f'source/{SOURCE}'], contribution='place_mon',
                            domain='placed_monster_names', engine='english/place_mon.txt', header_rows=1)
    seen_names = set()
    for entry in source.get('placed_names') or []:
        where = f"{SOURCE} placed_names {entry.get('id')}"
        if not isinstance(entry.get('id'), int) or not entry.get('name'):
            raise BuildError(f'{where}: a placed name needs id and name')
        if entry['name'] in seen_names:
            raise BuildError(f"{where}: the name {entry['name']!r} is listed twice")
        seen_names.add(entry['name'])
        place_names.add([entry['id'], entry['name']], origin=f"placed_names {entry.get('map', '')}")

    ctx.shared['monsters'] = row_ids
    ctx.shared['families'] = families_shared
    ctx.shared['rows_for_map_lanes'] = rows_table(report)

    relations = {'schema': 'openyamm.monsterRelations.v1',
                 'factions': {f'xeen_{key}': {'monsters': compact_ids(ids)} for key, ids in factions.items()},
                 'relations': [{'from': f'xeen_{key}', 'to': 'party', 'relation': relation}
                               for key, relation in party_relations.items()]}
    # Relations that switch on a quest bit (ENERGY_SHIELDS_AND_RELATIONS.md: later rules win while active): the pass
    # ogres friendly on q-d11 friends, hostile on q-d11 hostile; Hobstadt's court and the warren trolls on q-d13.
    for rule in source.get('relation_rules') or []:
        where = f"{SOURCE} relation_rules {rule.get('faction')}"
        if rule.get('faction') not in factions:
            raise BuildError(f'{where}: no faction {rule.get("faction")!r} (family key, or family_name of a `faction`)')
        bits = [key for key in ('after_qbit', 'until_qbit') if key in rule]
        if len(bits) != 1 or not isinstance(rule[bits[0]], int):
            raise BuildError(f'{where}: a rule needs one after_qbit or until_qbit number')
        relations['relations'].append({'from': f"xeen_{rule['faction']}", 'to': 'party',
                                       'relation': relation_name(rule['relation'], where), bits[0]: rule[bits[0]]})
    for feud in source.get('feuds') or []:
        # `from` and `to` name one faction or a list (D-52: DD-14's vampires and gargoyles leave Ambrose and the Queen).
        sides = [feud.get(key) if isinstance(feud.get(key), list) else [feud.get(key)] for key in ('from', 'to')]
        for name in sides[0] + sides[1]:
            if name not in factions:
                raise BuildError(f'{SOURCE} feuds: no faction {name!r} (family key, `faction` name or character_<key>)')
        for left in sides[0]:
            for right in sides[1]:
                relations['relations'].append({'from': f'xeen_{left}', 'to': f'xeen_{right}',
                                               'relation': relation_name(feud['relation'], f'{SOURCE} feuds')})
    ctx.text('relations.yml',
             '# Each family is a faction (a party hit on one alerts its kin) with its relation to the party. Xeen\n'
             '# monsters leave each other alone unless source/monsters.yml lists a feud (devdocs/'
             'ENERGY_SHIELDS_AND_RELATIONS.md).\n' + xeenlib.dump_yaml(relations),
             [f'source/{SOURCE}'])
    ctx.text('modifiers.yml',
             '# Boss and signature-monster behaviour (devdocs/MONSTER_MODIFIERS.md).\n'
             + xeenlib.dump_yaml({'schema': 'openyamm.monsterModifiers.v1',
                                  'monsters': {row_id: entries for row_id, entries in sorted(modifiers.items())}}),
             [f'source/{SOURCE}'])


def compact_ids(ids):
    """[11010, 11011, 11012, 11013] -> ['11010-11013']; single ids stay numbers."""
    result = []
    ordered = sorted(ids)
    start = previous = ordered[0]
    for value in ordered[1:] + [None]:
        if value is not None and value == previous + 1:
            previous = value
            continue
        result.append(start if start == previous else f'{start}-{previous}')
        if value is not None:
            start = previous = value
    return result


def rows_table(report):
    lines = ['| Family | Tier | Row | Name | Level | HP | XP | Picture (spawn slot name) | Sprites from | Model |',
             '| --- | --- | --: | --- | --: | --: | --: | --- | --- | --- |']
    for family_key, tier, info, picture, model, stand_in in report:
        slot = picture[:-2] if tier in ('A', 'B', 'C') else 'placed only'
        lines.append(f"| {family_key} | {tier} | {info['id']} | {info['name']} | {info['level']} | {info['hp']} | "
                     f"{info['xp']} | {slot} | {stand_in} | {model} |")
    return '\n'.join(lines)
