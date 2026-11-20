import sys, json
S = sys.argv[1]
def rows(p):
    out = []
    for line in open(p, encoding='latin-1'):
        c = line.rstrip('\r\n').split('\t')
        if len(c) > 16 and c[1].strip() and c[15].strip() in ('A', 'B', 'C', 'D'):
            out.append(c)
    return out
maw = rows(S + '/maw/SPCITEMS.TXT')
base = rows(S + '/base/SPCITEMS.TXT')
assert len(maw) == 80 and len(base) == 73, (len(maw), len(base))
I = 'General/zzMaw-Items.lua'
# MAW behaviour per id: (effect, sources)
stat = lambda stats, mod, van: ('stat special: %s +%s x chargesStatMult (vanilla table value %s)' % (stats, mod, van),
                                [I + ':1772-1799', I + ':2758-2785'])
dmg = lambda kind, lo, hi, coeff: ('damage special: %s, roll shape {%d,%d}, average = %s x item-level weapon damage '
                                   '(see damage_specials)' % (kind, lo, hi, coeff), [I + ':2047-2082'])
school = lambda s: ('%s Magic skill + floor(MaxCharges/4) + 5 (replaces the vanilla +50%% spell effect); total item '
                    'skill bonus capped at 2x base skill' % s, [I + ':2786-2789', I + ':3447-3457', I + ':2605-2611'])
B = {
 1: stat('resistances 11-16', 10, 10),
 2: stat('Might..Luck (1-7)', 8, 10),
 3: ('bow arrows explode (engine Carnage); MAW multiplies every Carnage arrow hit by 0.25 (text says half)',
     ['Modules/MawCore/Damage.lua:444-499']),
 4: dmg('Cold (Water)', 3, 4, 0.2), 5: dmg('Cold (Water)', 9, 12, 0.3), 6: dmg('Cold (Water)', 18, 24, 0.4),
 7: dmg('Electrical (Air)', 2, 5, 0.2), 8: dmg('Electrical (Air)', 6, 15, 0.3), 9: dmg('Electrical (Air)', 12, 30, 0.4),
 10: dmg('Fire', 1, 6, 0.2), 11: dmg('Fire', 3, 18, 0.3), 12: dmg('Fire', 6, 36, 0.4),
 13: dmg('Poison (Body)', 5, 5, 0.25), 14: dmg('Poison (Body)', 12, 12, 0.35), 15: dmg('Poison (Body)', 24, 24, 0.45),
 16: ('leech flag: melee 10 %, ranged 5 %, spells 10 % of damage dealt as a share of the reference monster HP '
      '(does not stack with 40/41 or another 16); engine Vampiric disabled', [I + ':3213-3276', I + ':2460-2491']),
 17: ('vanilla (recovery from being hit); weight 0 in every slot, never rolls', []),
 18: ('immunity to disease (9, 10, 11) and curse (1)', [I + ':1458-1476']),
 19: ('immunity to insanity (5) and spell-point drain (22)', [I + ':1458-1476']),
 20: ('immunity to paralysis (12) and fear (23)', [I + ':1458-1476']),
 21: ('immunity to poison (6, 7, 8) and weakness (2)', [I + ':1458-1476']),
 22: ('immunity to sleep (3) and unconsciousness (13)', [I + ':1458-1476']),
 23: ('immunity to stone (15) and premature ageing (21)', [I + ':1458-1476']),
 24: ('vanilla knockback; weight 0 in every slot, never rolls', []),
 25: ('immunity to death (14) and eradication (16); the vanilla +5 Level is lost because MAW zeroes all engine '
      'item stat bonuses (events.CalcStatBonusByItems sets Result 0)', [I + ':1458-1476', I + ':2566-2584']),
 26: school('Air'), 27: school('Body'), 28: school('Dark'), 29: school('Earth'), 30: school('Fire'),
 31: school('Light'), 32: school('Mind'), 33: school('Spirit'), 34: school('Water'),
 35: ('vanilla (lockpick/steal); weight 0, never rolls', []),
 36: ('physical damage taken x0.85 once (flag, any number of items); replaces "half damage from missiles"',
      [I + ':3412-3418', 'General/zzMaw-Stats.lua:1064-1067']),
 37: ('HP regen: +2 % of max HP per second per item (0.2 % per 0.1 s tick) plus max(1 % max HP - 1, 0) per '
      'engine regeneration tick', ['General/zzMAW-Skills.lua:1358-1361', 'General/zzMaw-Stats.lua:670-679']),
 38: ('Meditation skill + floor(MaxCharges*3/20) + 3; plus max(1 % max SP - 1, 0) per engine regeneration tick',
      [I + ':2790-2793', I + ':3465', 'General/zzMaw-Stats.lua:681-686']),
 39: ('spells only: adds damage {20,40} x coeff 0.5 x item-level damage (see damage_specials) to every spell, from '
      'any of the three weapon slots; plus Intellect and Personality +25 x chargesStatMult. Repurposed from Ogre '
      'Slaying.', [I + ':2060', I + ':2125-2128', I + ':1772-1799', 'General/zzMaw-Spells.lua:2022-2036']),
 40: ('spell leech 10 % (flag) and spell delay /1.1 from any weapon slot, one instance only. Repurposed from '
      'Dragon Slaying.', [I + ':2084-2095', I + ':3254-3256', 'General/zzMaw-Stats.lua:172-175']),
 41: ('physical leech flag (melee 10 %, ranged 5 %) and swiftness +0.3 (2H, bow) / +0.15 (1H)',
      [I + ':3248-3253', 'General/zzMAW-Skills.lua:463-465', 'General/zzMAW-Skills.lua:492-498']),
 42: stat('stats 1-16 (stats, HP, SP, AC, resistances)', 3, 1),
 43: stat('Endurance, HP, AC (4, 8, 10)', 10, 10),
 44: stat('HP (8)', 10, 10),
 45: stat('Accuracy, Speed (5, 6)', 10, 5),
 46: ('melee and bow only: Fire damage {20,40} x coeff 0.5 x item-level damage; plus Might +25 x chargesStatMult',
      [I + ':2061', I + ':2125-2128', I + ':1772-1799']),
 47: stat('SP (9)', 10, 10),
 48: stat('Endurance (4) +15, AC (10) +5', '15/5', '15/5'),
 49: stat('Intellect, Luck (2, 7)', 10, 10),
 50: stat('Fire resistance (11)', 30, 30),
 51: stat('Intellect, Speed, SP (2, 6, 9)', 10, 10),
 52: stat('Endurance, Accuracy (4, 5)', 10, 10),
 53: stat('Might, Personality (1, 3)', 20, 10),
 54: stat('Endurance (4)', 15, 15),
 55: stat('Luck (7)', 15, 15),
 56: stat('Might, Endurance (1, 4)', 10, 5),
 57: stat('Intellect, Personality (2, 3)', 15, 5),
 58: ('value: SPCITEMS Value X 10 (multiplier < 11) and x2.5 more in getItemValue', [I + ':1956-1960']),
 59: ('swiftness +0.3 (2H, bow) / +0.15 (1H)', ['General/zzMAW-Skills.lua:463-465', 'General/zzMAW-Skills.lua:492-498']),
 60: ('vanilla +3 Unarmed and Dodging; weight 0 in every slot; the skill bonus is lost under MAW (engine item '
      'skill bonuses are zeroed, only 62 is re-added)', [I + ':2566-2584', I + ':2587-2612']),
 61: ('vanilla +3 Stealing and Disarm; weight 0; skill bonus lost under MAW as for 60', [I + ':2566-2584']),
 62: ('+3 ID Item and +3 ID Monster, fixed (not scaled) (explicit fix for the zeroed engine bonus)',
      [I + ':2759-2763']),
 63: ('vanilla x2 vs elementals; weight 0 in MAW, never rolls', []),
 64: ('vanilla x2 vs undead; weight 0 in MAW, never rolls', []),
 65: ('vanilla x2 vs titans (unused); weight 0', []),
 66: ('HP regen like 37 (+2 % max HP per second) and Meditation skill + floor(MaxCharges*3/20) + 3; not in the '
      'engine-tick regen lists', ['General/zzMAW-Skills.lua:1358-1361', I + ':3465']),
 67: ('vanilla 5 Body damage + 2 Disarm; weight 0; neither part works under MAW (no enchantbonusdamage entry, '
      'engine item damage and skill bonuses zeroed)', [I + ':2047-2061', 'Global/zzMaw_Legendaries.lua:6-20']),
 68: ('vanilla 6-8 Cold + 5 AC; weight 0; lost under MAW like 67', []),
 69: ('vanilla +20 Air res + Shielding; weight 0; stat part lost under MAW', []),
 70: ('vanilla +10 Water res + 2 Alchemy; weight 0; stat part lost under MAW', []),
 71: ('vanilla no drowning damage (engine)', []),
 72: ('vanilla no falling damage (engine)', []),
 73: ('vanilla sparks (engine); weight 0', []),
 74: stat('Personality, Accuracy (3, 5)', 20, 0),
 75: stat('Might, Intellect (1, 2)', 20, 0),
 76: stat('Intellect, Accuracy (2, 5)', 20, 0),
 77: stat('Might, Intellect, Personality (1, 2, 3)', 15, 0),
 78: stat('Fire, Air, Water, Earth resistance (11-14)', 20, 0),
 79: stat('Mind, Body resistance (15, 16)', 20, 0),
 80: stat('stats 1-16', 5, 0),
}
TT = {  # tooltip text the player sees
 3: 'Explosive Impact! (half damage)  [BonusStat override :1479, :1509]',
 16: 'Leech 10% of physical and magical damage  [override :1488]',
 18: 'Disease and Curse Immunity  [override :1480]', 19: 'Insanity and SP drain Immunity  [override :1481]',
 20: 'Paralysis and fear Immunity  [override :1482]', 21: 'Poison and weakness Immunity  [override :1483]',
 22: 'Sleep and Unconscious Immunity  [override :1484]', 23: 'Stone and premature ageing Immunity  [override :1485]',
 25: 'Death and Eradication Immunity  [override :1486]',
 36: 'Reduces Physical damage taken by 15%  [override :1487]',
 40: 'Leech 10% of magical damage, increases cast speed (does not stack)  [override :1490]',
 41: 'Leech 10% of physical damage, increases attack speed  [override :1489]',
}
CHECK = {  # checktext (zzMaw-Items.lua:1836-1890) used when Bonus2 is in bonusEffects or enchantList
 1: '" +<floor(10*m)> to all Resistances."', 2: '" +<floor(8*m)> to all Seven Statistics."',
 4: 'Adds <lo-hi> points of Cold damage.', 5: 'Adds <lo-hi> points of Cold damage.', 6: 'Adds <lo-hi> points of Cold damage.',
 7: 'Adds <lo-hi> points of Electrical damage.', 8: 'Adds <lo-hi> points of Electrical damage.',
 9: 'Adds <lo-hi> points of Electrical damage.', 10: 'Adds <lo-hi> points of Fire damage.',
 11: 'Adds <lo-hi> points of Fire damage.', 12: 'Adds <lo-hi> points of Fire damage.',
 13: 'Adds <lo-hi> points of Body damage.', 14: 'Adds <lo-hi> points of Body damage.', 15: 'Adds <lo-hi> points of Body damage.',
 26: 'Air Magic Skill +<school>', 27: 'Body Magic Skill +<school>', 28: 'Dark Magic Skill +<school>',
 29: 'Earth Magic Skill +<school>', 30: 'Fire Magic Skill +<school>', 31: 'Light Magic Skill +<school>',
 32: 'Mind Magic Skill +<school>', 33: 'Spirit Magic Skill +<school>', 34: 'Water Magic Skill +<school>',
 38: 'Meditation Skill +<med>',
 39: 'Adds <lo-hi> to spell damage and +<floor(25*m)> Intellect and personality.',
 42: '" +<floor(3*m)> to Seven Stats, HP, SP, Armor, Resistances."',
 43: '" +<floor(10*m)> to Endurance, Armor, Hit points."',
 44: '" +<floor(10*m)> Hit points and Regenerate Hit points over time."',
 45: '" +<floor(10*m)> Speed and Accuracy."',
 46: 'Adds <lo-hi> points of Fire damage to <Melee|Bow> attacks and +<floor(25*m)> Might.',
 47: '" +<floor(10*m)> Spell points and Meditation Skill +<med>"',
 48: '" +<floor(15*m)> Endurance and +<floor(5*m)> Armor."', 49: '" +<floor(10*m)> Intellect and Luck."',
 50: '" +<floor(30*m)> Fire Resistance and Regenerate Hit points over time."',
 51: '" +<floor(10*m)> Spell points, Speed, Intellect."', 52: '" +<floor(10*m)> Endurance and Accuracy."',
 53: '" +<floor(20*m)> Might and Personality."',
 54: '" +<floor(15*m)> Endurance and Regenerate Hit points over time."',
 55: '" +<floor(15*m)> Luck and Meditation Skill +<med>"', 56: '" +<floor(10*m)> Might and Endurance."',
 57: '" +<floor(15*m)> Intellect and Personality."',
 66: 'Regenerates Hit Points and Meditation Skill +<med>',
 74: '" +<floor(20*m)> Personality and Accuracy."', 75: '" +<floor(20*m)> Intellect and Might."',
 76: '" +<floor(20*m)> Intellect and Accuracy."', 77: '" +<floor(15*m)> Might, Intellect and Personality."',
 78: '" +<floor(20*m)> Elemental Resistances."', 79: '" +<floor(20*m)> Body and mind Resistances."',
 80: '" +<floor(5*m)> to Seven Stats, HP, SP, Armor, Resistances."',
}
slots = ['W1', 'W2', 'Miss', 'Arm', 'Shld', 'Helm', 'Belt', 'Cape', 'Gaunt', 'Boot', 'Ring', 'Amul']
def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
out = ['specials:', '  # id = 1-based SPCITEMS row = MAW Bonus2 = OpenYAMM special_item_enchants id (rows 1-73).',
       '  # weights: W1 W2 Miss Arm Shld Helm Belt Cape Gaunt Boot Ring Amul (ChanceForSlot by EquipStat 0..11)']
for i, c in enumerate(maw, 1):
    w = [int(x or 0) for x in c[2:14]]
    out.append('  %d:' % i)
    out.append('    name: %s' % q(c[1].strip()))
    out.append('    lvl: %s' % c[15].strip())
    out.append('    weights: [%s]' % ', '.join(map(str, w)))
    out.append('    value: %s' % q(c[14].strip()))
    out.append('    table_text: %s' % q(c[0].strip().strip('"')))
    if i <= 73:
        b = base[i - 1]
        bw = [int(x or 0) for x in b[2:14]]
        ch = []
        if b[1].strip() != c[1].strip(): ch.append('name %s' % b[1].strip())
        if b[15].strip() != c[15].strip(): ch.append('lvl %s' % b[15].strip())
        if bw != w: ch.append('weights [%s]' % ', '.join(map(str, bw)))
        if b[14].strip() != c[14].strip(): ch.append('value %s' % b[14].strip())
        if b[0].strip() != c[0].strip(): ch.append('text %s' % b[0].strip())
        if ch:
            out.append('    base_mmerge: %s' % q('; '.join(ch)))
    else:
        out.append('    base_mmerge: "new in MAW"')
    if i in TT:
        out.append('    tooltip: %s' % q(TT[i]))
    elif i in CHECK:
        out.append('    tooltip: %s' % q(CHECK[i] + '  [checktext]'))
    eff, src = B[i]
    out.append('    maw_effect: %s' % q(eff))
    if src:
        line = '    source: [%s]' % ', '.join(q(s) for s in src)
        if len(line) <= 120:
            out.append(line)
        else:
            out.append('    source:')
            for s2 in src:
                out.append('      - %s' % q(s2))
print('\n'.join(out))
