#!/usr/bin/env python3
"""Writes icons.json: every talent and keystone of assets_dev/engine/data_tables/talents.yml with its effect text,
tree colour identity and the subject to paint. Rerun after the table's texts change; the subjects live here."""
import json
import os

import yaml

STUDY = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
REPO = os.path.normpath(os.path.join(STUDY, '../../..'))

PALETTE = {
    'arms': 'ARMS tree: cold bright steel and deep blood red; a soft dark-crimson ember glow behind the subject.',
    'archery': 'ARCHERY tree: warm polished wood, leather, feather fletching and forest green; a soft leaf-green '
               'glow behind the subject.',
    'arcana': 'ARCANA tree: violet and electric blue arcane light; the subject itself glows violet-blue.',
    'any': 'ANY tree: old gold and bone ivory; a soft warm gold glow behind the subject.',
    'keystone': 'KEYSTONE (rarer and grander than an ordinary talent): old gold and bone ivory, with a stronger '
                'radiant gold glow and a few fine gold sparks, richer and more precious than the others.',
}

SUBJECTS = {
    'weapon_training': 'ONE upright steel longsword standing point-down, broad straight blade, a plain steel '
                       'crossguard and a dark blood-red leather grip and round pommel; a strong vertical silhouette.',
    'cleave': 'ONE heavy double-bitted steel battle axe swung sideways, its head at the left, leaving a wide '
              'bright crescent slash arc of white and crimson that sweeps through a broad 120-degree curve to the '
              'right. The arc is the main shape: a big bright crescent.',
    'sweeping_blows': 'ONE steel sword blade at the right end of a long curved crimson motion trail that sweeps '
                      'through three small dark shadowy enemy silhouettes (simple head-and-shoulders shapes) '
                      'standing in a row; the trail cuts across all three.',
    'onslaught': 'TWO bearded steel hand axes crossed in an X, their edges stained blood red, with three stacked '
                 'blood-red upward chevrons rising behind the crossing like a growing fury. A berserker emblem.',
    'charge': 'ONE bull-horned closed steel great helm in three-quarter profile rushing forward to the right, with '
              'long swept-back red and white speed streaks trailing behind it to the left.',
    'shield_wall': 'THREE round steel-rimmed shields with deep red faces overlapping side by side in a tight row, '
                   'front view, like a shield wall; a broad wide solid silhouette.',
    'marksman': 'ONE wooden recurve longbow fully drawn with an arrow nocked, held diagonally, the arrow pointing '
                'up and to the right; green fletching, a taut bright string.',
    'multishot': 'A FAN of five wooden arrows with green fletching flying outward from one point at the bottom '
                 'left, spreading across about sixty degrees toward the upper right, each with a short motion trail.',
    'piercing_arrows': 'ONE wooden arrow flying left to right, passing clean through two round wooden target discs '
                       'standing one behind the other in a line; the arrow shaft runs through both discs and its '
                       'head emerges past the second.',
    # Power Shot replaced Pinning Shot (2026-11-16); its icon (masters/pinning_shot.png) is kept but unused.
    'power_shot': 'ONE heavy wooden arrow with green fletching flying from lower left to upper right, its steel '
                  'head wrapped in a bright burst of golden-green force and a shock ring around the shaft, with '
                  'thick motion streaks behind it: a single overcharged shot.',
    'steady_aim': 'ONE round woven straw archery target seen from the front, with green and cream rings, and one '
                  'arrow struck dead centre in the bullseye, seen slightly from the side.',
    'quickfoot': 'ONE single tall brown leather ranger boot in side view with ONE green-tinted feathered wing at '
                 'its heel and short green motion streaks behind it. Only one boot (the game already has a pair of '
                 'white-winged boots as a spell icon, this must look different: single boot, green wing).',
    'attunement': 'ONE open leather-bound spellbook seen from slightly above, blank pages, with a bright violet-blue '
                  'arcane sigil (an abstract circle of light, no letters) rising and glowing above its pages.',
    'blink': 'ONE swirling violet-blue portal ring seen slightly from the side, and a bright streak of white-blue '
             'light leaping out of it forward to the right with a few sparks, as if someone has just teleported.',
    'spell_surge': 'ONE carved wooden wizard staff head holding a faceted violet crystal that bursts with a surge '
                   'of forked blue-white lightning radiating upward and outward.',
    'resolve': 'ONE translucent glowing violet-blue dome of force (a warding bubble) with a small orange flame, a '
               'pale ice shard and a little yellow lightning bolt glancing off its surface.',
    'overload': 'ONE crackling violet-blue spell orb in the centre splitting apart into four smaller crackling orbs '
                'that fly outward from it, linked to it by thin arcs of lightning.',
    'binding_circle': 'ONE glowing violet-blue magic circle on the ground seen in perspective from above, made of '
                      'two concentric rings with abstract rune notches (no letters), with pale violet light and '
                      'faint chains of light rising from its rim.',
    'bloodthirst': 'ONE large curved bone-ivory fang with a big glossy crimson blood drop dripping from its tip; '
                   'the drop and the fang share the main silhouette.',
    # Conditioning and Spell Suppression (user, 2026-11-16): +1 % to all seven stats; less damage from spells.
    'conditioning': 'ONE seven-pointed star of old gold seen from the front, each of its seven points tipped with a '
                    'small round gem of a different colour (red, blue, green, yellow, violet, white, orange), around '
                    'a glowing bone-ivory centre; balanced, symmetrical, a strong compact silhouette.',
    'spell_suppression': 'ONE old gold armoured gauntlet closing its fist around a crackling orange-and-violet spell '
                         'orb, smothering it: the orb is crushed and its light breaks into dim fading sparks and '
                         'wisps of smoke between the fingers. The fist is the main shape (not a shield, not a dome).',
    # Manathirst (user, 2026-11-16): Bloodthirst for the SP bar; its sibling, a mana drop in place of the blood.
    'manathirst': 'ONE large curved bone-ivory fang with a big glossy glowing sapphire-blue mana drop dripping from '
                  'its tip, a faint blue shimmer of light around the drop; the drop and the fang share the main '
                  'silhouette. A sibling of a fang dripping blood, but the drop is clearly blue magic, not water.',
    'cheat_death': 'ONE bone-ivory human skull seen from the front with a jagged crack across its brow, and a '
                   'bright golden spark of life bursting out through the crack.',
    'unbroken': 'ONE heart carved of solid grey stone, bound with crossed bands of old gold, whole and unbroken, '
                'with a few small chips glancing off it.',
}


def main():
    with open(os.path.join(REPO, 'assets_dev/engine/data_tables/talents.yml')) as f:
        table = yaml.safe_load(f)
    entries = []
    for talent in table['talents']:
        entries.append({'id': talent['id'], 'name': talent['name'], 'tree': talent['tree'], 'kind': talent['kind'],
                        'effect': talent['text'], 'palette': PALETTE[talent['tree']],
                        'subject': SUBJECTS[talent['id']]})
    for keystone in table['keystones']:
        entries.append({'id': keystone['id'], 'name': keystone['name'], 'tree': 'keystone', 'kind': 'keystone',
                        'effect': keystone['text'], 'palette': PALETTE['keystone'],
                        'subject': SUBJECTS[keystone['id']]})
    with open(os.path.join(STUDY, 'icons.json'), 'w') as f:
        json.dump(entries, f, indent=1, ensure_ascii=False)
        f.write('\n')
    for i, entry in enumerate(entries, 1):
        print(i, entry['id'], entry['tree'])


if __name__ == '__main__':
    main()
