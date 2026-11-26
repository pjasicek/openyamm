"""Xeen items: items.txt, item_effects.txt, item_sets.txt and random_items.txt from
source/items.yml (MONSTERS_AND_ITEMS.md section 4; the file's header for its fields).

Every row copies an engine item (`like`), so slot, skill, sprite and paper-doll placement are an existing item's,
and changes name, value, description, numbers and flags. Quest items carry Quest|NoRandom|NoShop (and may have an icon
of their own); artifacts and relics Unique|NoRandom|NoShop|World:xeen (they come only from fixed places); books
NoRandom|World:xeen (sold in shops); spellbooks World:xeen copies of MM8's (`spellbooks`, below). Artifacts, relics and the gemsmith gear wear an MM6-MM8 item's skin (the user,
2026-11-20, DECISIONS U-1): picture, paper-doll art and ground model are the like-item's, never an icon of their own.
The world adds no equipment bases; random_items.txt holds only its spellbooks' weights (MM8's).
Spellbooks: every world has its own book of each spell (devdocs/LOOT_POOL.md; a book is World:-flagged, and a guild sells
and random loot drops only its own world's, ItemTable::spellbookItemIdForSpell). Xeen had none, so every Xeen guild's
shelf was empty (feedback F7, 2026-11-21). `spellbooks` copies MM8's 99 books (the books Xeen's maps place, D-2.2)
under id_base + spell id: name, price, picture, ground object, description and random-treasure weights; no new art
(U-1).
Readable items (`readable: a3`) get their text from A3: gen_quests writes their readable_items rows, and
ctx.shared['readable_items'] (id -> key) lists them. Publishes ctx.shared['items'] (key -> id) for the quest and town
modules.
"""

from __future__ import annotations

import xeenlib
from xeenlib import BuildError

SOURCE = 'items.yml'
WIDTH = 32  # the standard columns 0-31 (ItemTable.cpp); 17-19 are package, canonical id and source id
EFFECT_COLUMNS = ['might', 'intellect', 'personality', 'endurance', 'speed', 'accuracy', 'luck', 'max_health',
                  'max_sp', 'armor_class', 'melee_attack', 'ranged_attack', 'melee_damage', 'ranged_damage',
                  'all_resistances', 'fire_resistance', 'air_resistance', 'water_resistance', 'earth_resistance',
                  'mind_resistance', 'body_resistance', 'spirit_resistance', 'skill_bonuses', 'weapon_damage',
                  'recovery_reduction_ticks', 'health_regen_per_second', 'spell_regen_per_second', 'effect_flags']
ITEMS_HEADER = ['Item #', 'Pic File', 'Name', 'Value', 'Equip Stat', 'Skill Group', 'Mod1', 'Mod2', 'material',
                'ID/Rep/St', 'Not identified name', 'Sprite Index', 'VarA', 'VarB', 'Equip X', 'Equip Y', 'Notes',
                'package_id', 'canonical_id', 'source_item_id', 'content_flags', 'normalized_tier', 'use_action',
                'use_target', 'set_id', 'effect_profile', 'allowed_class_roots', 'required_might',
                'required_accuracy', 'inventory_width', 'inventory_height', 'visual_status']


def engine_items():
    rows = {}
    for row in xeenlib.engine_table('items.txt'):
        item_id = xeenlib.parse_int(xeenlib.cell(row, 0))
        if item_id is not None:
            rows[item_id] = row
    return rows


WORN_SLOTS = ('Armor', 'Helm', 'Belt', 'Cloak', 'Boots')


def engine_doll_positions():
    """Engine complex_item_pictures rows (the paper-doll offsets of worn items) by item id."""
    rows = {}
    for row in xeenlib.engine_table('complex_item_pictures.txt'):
        item_id = xeenlib.parse_int(xeenlib.cell(row, 1))
        if item_id is not None and xeenlib.parse_int(xeenlib.cell(row, 0)) is not None:
            rows[item_id] = row
    return rows


# Fields an artifact, relic or gemsmith row may not carry: its look is its like-item's (DECISIONS U-1).
OWN_ART_FIELDS = ('icon', 'icon_needed', 'doll_art_needed', 'grip')
BORROWED_RARITIES = ('Artifact', 'Relic', 'Special')


class Items:
    def __init__(self, ctx):
        self.ctx = ctx
        self.engine = engine_items()
        self.items = ctx.table('items.txt', sources=[f'source/{SOURCE}'], domain='items', engine='items.txt',
                               header=[ITEMS_HEADER])
        self.effects = ctx.table('item_effects.txt', sources=[f'source/{SOURCE}'], domain='items',
                                 header=[['item_id', 'effect_profile'] + EFFECT_COLUMNS])
        self.sets = ctx.table('item_sets.txt', sources=[f'source/{SOURCE}'], numeric_key=False,
                              header=[['set_id', 'required_piece_count', 'effect_profile'] + EFFECT_COLUMNS])
        # A contribution table of world.yml: only the spellbooks' rows (the world adds no bases).
        self.random = ctx.table('random_items.txt', sources=[f'source/{SOURCE}'], domain='items', engine='random_items.txt',
                  header_rows=2)
        self.dolls = ctx.table('complex_item_pictures.txt', sources=[f'source/{SOURCE}'], domain='items',
                               engine='complex_item_pictures.txt', header_rows=2, key_column=1)
        self.engine_dolls = engine_doll_positions()
        self.ids: dict[str, int] = {}
        self.icons_needed: list[tuple[int, str, str]] = []
        self.readable_ids: dict[int, str] = {}

    def like_row(self, like, where):
        row = self.engine.get(like)
        if row is None:
            raise BuildError(f'{where}: engine item {like} does not exist')
        cells = [xeenlib.cell(row, index) for index in range(17)]
        return cells + [''] * (WIDTH - len(cells))

    def add(self, key, spec, flags, where, rarity=None, tier=0, set_id='', effect_profile='', borrowed_skin=False):
        item_id = spec.get('id')
        if not isinstance(item_id, int):
            raise BuildError(f'{where}: no id')
        if key in self.ids:
            raise BuildError(f'{where}: key {key} is used twice')
        row = self.like_row(spec['like'], where)
        row[0] = str(item_id)
        if borrowed_skin:
            own = [field for field in OWN_ART_FIELDS if field in spec]
            if own:
                raise BuildError(f'{where}: {own}: the look is the like-item\'s (DECISIONS U-1)')
        elif spec.get('icon'):
            row[1] = spec['icon']
        if row[8] in BORROWED_RARITIES:
            # The like-item's own enchantment (a Special's VarA) and rarity stay with it; a common row (gemsmith gear)
            # drops the "Artifact " of its unidentified name.
            row[12], row[13] = '0', '0'
            if not rarity:
                row[8] = '0'
                row[10] = row[10].split(' ', 1)[1] if ' ' in row[10] else row[5]
        row[2] = spec['name']
        row[3] = str(spec.get('value', row[3] or 0))
        if spec.get('equip'):
            row[4] = spec['equip']
        if 'damage' in spec:
            row[6] = str(spec['damage'])
        if 'bonus' in spec:
            row[7] = str(spec['bonus'])
        if rarity:
            row[8] = rarity
            row[9] = '20'
        row[16] = xeenlib.quote_text(spec.get('notes', ''))
        row[17] = xeenlib.WORLD_ID
        row[18] = f'{xeenlib.WORLD_ID}:item/{key}'
        row[19] = str(item_id)
        row[20] = '|'.join(flags)
        row[21] = str(tier) if tier else ''
        row[24] = set_id
        row[25] = effect_profile
        if spec.get('readable'):
            # The text is A3's: gen_quests writes the readable_items row (source/npcs/books.yml and the quest hooks);
            # the driver warns about a readable item that ends up without one.
            if spec['readable'] != 'a3':
                raise BuildError(f"{where}: readable is `a3` (A3 writes the text); A2's wording goes in readable_draft")
            row[4] = 'Mscroll'
            row[6] = '0'
            row[7] = '0'
            row[22] = 'ReadText'
            row[20] = '|'.join(flags + ['Readable'])
            self.readable_ids[item_id] = key
        self.items.add(row, origin=key)
        if row[4] in WORN_SLOTS:
            self.add_doll_position(item_id, row[1], spec['like'], spec['name'], where)
        self.ids[key] = item_id
        if spec.get('icon_needed'):
            self.icons_needed.append((item_id, spec['name'], spec['icon_needed']))

    def add_doll_position(self, item_id, picture, like, name, where):
        """A worn item is drawn on the paper doll from its picture's doll files (<pic>v1 ...) at the offsets of the
        engine item that owns that picture: copy that item's complex_item_pictures row under our id."""
        owners = [like] + sorted(item for item, row in self.engine.items() if xeenlib.cell(row, 1).lower() == picture.lower())
        source = next((self.engine_dolls[item] for item in owners
                       if item in self.engine_dolls and xeenlib.cell(self.engine[item], 1).lower() == picture.lower()),
                      None)
        if source is None:
            raise BuildError(f'{where}: worn picture {picture} has no paper-doll row (complex_item_pictures) in the '
                             'engine; a new worn picture needs its doll art and offsets first')
        row = list(source)
        row[1] = str(item_id)
        row[2] = name
        self.dolls.add(row, origin=f'doll {item_id}')

    def effect_cells(self, effects, where):
        unknown = set(effects) - set(EFFECT_COLUMNS)
        if unknown:
            raise BuildError(f'{where}: unknown effect columns {sorted(unknown)}')
        return [effects.get(column, '') for column in EFFECT_COLUMNS]


SPELL_COUNT = 99


def add_spellbooks(items, spec):
    """Xeen's own book of each spell: a World:xeen copy of the MM8 book (`like_first` + spell id - 1) at id_base + spell
    id, and its random_items row (MM8's weights)."""
    if not spec:
        raise BuildError(f'{SOURCE}: no `spellbooks`: Xeen\'s guilds would sell nothing (feedback F7)')
    where = f'{SOURCE} spellbooks'
    base, like_first = spec.get('id_base'), spec.get('like_first')
    if not isinstance(base, int) or not isinstance(like_first, int):
        raise BuildError(f'{where}: id_base and like_first are numbers')
    weights = {}
    for row in xeenlib.engine_table('random_items.txt'):
        item_id = xeenlib.parse_int(xeenlib.cell(row, 0))
        if item_id is not None:
            weights[item_id] = row
    for spell in range(1, SPELL_COUNT + 1):
        like = like_first + spell - 1
        row = items.like_row(like, where)
        if row[4] != 'Book' or row[6] != f'S{spell}':
            raise BuildError(f'{where}: engine item {like} is not the book of spell {spell} ({row[4]} {row[6]})')
        if like not in weights:
            raise BuildError(f'{where}: engine item {like} has no random_items row')
        item_id = base + spell
        key = f'spellbook_{spell}'
        row[0] = str(item_id)
        row[17] = xeenlib.WORLD_ID
        row[18] = f'{xeenlib.WORLD_ID}:item/{key}'
        row[19] = str(item_id)
        row[20] = f'World:{xeenlib.WORLD_ID}'
        items.items.add(row, origin=key)
        items.ids[key] = item_id
        weight_row = list(weights[like])
        weight_row[0] = str(item_id)
        items.random.add(weight_row, origin=key)


def build(ctx):
    source = ctx.load_source(SOURCE)
    items = Items(ctx)

    for key, spec in (source.get('quest_items') or {}).items():
        where = f'{SOURCE} quest_items {key}'
        # A worn quest item (Roxanne's tiara) may carry effects like an artifact.
        profile = f'{xeenlib.WORLD_ID}:item_effect/{key}' if spec.get('effects') else ''
        items.add(key, spec, ['Quest', 'NoRandom', 'NoShop'], where, effect_profile=profile)
        if profile:
            items.effects.add([spec['id'], profile] + items.effect_cells(spec['effects'], where), origin=key)

    for key, spec in (source.get('books') or {}).items():
        where = f'{SOURCE} books {key}'
        if spec.get('readable') != 'a3':
            raise BuildError(f'{where}: a book is readable: a3')
        items.add(key, spec, ['NoRandom', f'World:{xeenlib.WORLD_ID}'], where)

    # Gemsmith gear (Q-D7): named, made on demand, so neither unique nor random nor sold.
    for key, spec in (source.get('crafted') or {}).items():
        where = f'{SOURCE} crafted {key}'
        profile = f'{xeenlib.WORLD_ID}:item_effect/{key}' if spec.get('effects') else ''
        items.add(key, spec, ['NoRandom', 'NoShop', f'World:{xeenlib.WORLD_ID}'], where, tier=spec.get('tier', 0),
                  effect_profile=profile, borrowed_skin=True)
        if profile:
            items.effects.add([spec['id'], profile] + items.effect_cells(spec['effects'], where), origin=key)

    add_spellbooks(items, source.get('spellbooks'))

    sets = source.get('sets') or {}
    for key, spec in (source.get('artifacts') or {}).items():
        where = f'{SOURCE} artifacts {key}'
        rarity = spec.get('rarity', 'Artifact')
        if rarity not in ('Artifact', 'Relic'):
            raise BuildError(f'{where}: rarity is Artifact or Relic')
        set_key = spec.get('set')
        if set_key and set_key not in sets:
            raise BuildError(f'{where}: no set {set_key!r}')
        profile = f'{xeenlib.WORLD_ID}:item_effect/{key}' if spec.get('effects') else ''
        flags = ['Unique', 'NoRandom', 'NoShop', f'World:{xeenlib.WORLD_ID}']
        if rarity == 'Relic' and spec.get('equip') == 'Misc':
            flags = ['Quest'] + flags
        # `keep: true` (the Xeen Slayer Sword, D-47 Q12): never dropped (the engine's NoDrop) and never sold (value 0:
        # shops refuse an item without a price).
        if spec.get('keep'):
            if spec.get('value', 0) != 0:
                raise BuildError(f'{where}: a kept item has value 0 (shops buy every item with a price)')
            flags = flags + ['NoDrop']
        # `any_class: true` (U-17, the Xeen Slayer Sword): every character may wield it without its weapon skill (the
        # engine's EquipWithoutSkill); the skill still adds its bonus for those who have it.
        if spec.get('any_class'):
            flags = flags + ['EquipWithoutSkill']
        items.add(key, spec, flags, where, rarity=rarity, tier=6,
                  set_id=f'{xeenlib.WORLD_ID}:set/{set_key}' if set_key else '', effect_profile=profile,
                  borrowed_skin=True)
        if profile:
            items.effects.add([spec['id'], profile] + items.effect_cells(spec['effects'], where), origin=key)

    for key, spec in sets.items():
        where = f'{SOURCE} sets {key}'
        set_id = f'{xeenlib.WORLD_ID}:set/{key}'
        members = [name for name, item in (source.get('artifacts') or {}).items() if item.get('set') == key]
        if len(members) != spec.get('pieces'):
            raise BuildError(f"{where}: {spec.get('pieces')} pieces declared, {len(members)} artifacts name the set")
        items.sets.add([set_id, spec['pieces'], f'{xeenlib.WORLD_ID}:set_effect/{key}_complete']
                       + items.effect_cells(spec.get('effects') or {}, where), origin=key)

    if any(source.get(field) for field in ('bases', 'ladders', 'material_names', 'prices')):
        raise BuildError(f'{SOURCE}: the world adds no equipment bases (DECISIONS U-1)')

    ctx.shared['items'] = dict(items.ids)
    ctx.shared['icons_needed'] = list(items.icons_needed)
    ctx.shared['readable_items'] = dict(items.readable_ids)
