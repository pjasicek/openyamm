-- MAW 8967ae88 balance-model harness (line ranges updated from 8fbb48d1) (Lua 5.4 with Lua 5.1/MMExt shims).
-- usage: lua harness.lua <maw_root> <bolster> <mode> <insanity> <madness> <trueNightmare> <austerity>
--                        <partyCount> <buffTable: spells|mapping> <statEffectRounding: trunc|round> [levels...]
local ROOT = arg[1]
local cfg = {bolster=tonumber(arg[2]), mode=tonumber(arg[3]), insanity=arg[4]=="1", madness=arg[5]=="1",
  trueNightmare=arg[6]=="1", austerity=arg[7]=="1", party=tonumber(arg[8]), buff=arg[9], statRound=arg[10]}

-- ---------------- shims ----------------
unpack = unpack or table.unpack
function round(x) if x%1>=0.5 then x=x-x%1+1 else x=x-x%1 end return x end   -- zz_Maw-initialize.lua:315
function table.find(t, v) for k, x in pairs(t) do if x == v then return k end end end
events = {}
vars = {Mode = cfg.mode ~= 0 and cfg.mode or nil, insanityMode = cfg.insanity or nil, madnessMode = cfg.madness or nil,
        trueNightmare = cfg.trueNightmare or nil, AusterityMode = cfg.austerity or nil}
mapvars = {}
Party = {Count = cfg.party}
MawCore = {}
const = {
  Novice = 1, Expert = 2, Master = 3, GM = 4,
  Skills = {Staff=0, Sword=1, Dagger=2, Axe=3, Spear=4, Bow=5, Mace=6, Blaster=7, Shield=8, Leather=9, Chain=10,
            Plate=11, Fire=12, Air=13, Water=14, Earth=15, Spirit=16, Mind=17, Body=18, Light=19, Dark=20,
            DarkElfAbility=21, VampireAbility=22, DragonAbility=23, IdentifyItem=24, Merchant=25, Repair=26,
            Bodybuilding=27, Meditation=28, Perception=29, Regeneration=30, DisarmTraps=31, Dodging=32,
            Unarmed=33, IdentifyMonster=34, Armsmaster=35, Stealing=36, Alchemy=37, Learning=38},  -- MM8 values
  Spells = {Haste=5, FireResistance=3, Shield=17, StoneSkin=38, Bless=46, Fate=47, Heroism=51, Heal=68,
            CureDisease=74, RemoveCurse=49, SharedLife=54, Resurrection=55, PowerCure=77},
}
-- Engine statistic-effect table (MM7/MM8 0x48E18E; same as OpenEnroth param_to_bonus_table)
local TH = {500,400,350,300,275,250,225,200,175,150,125,100,75,50,40,35,30,25,21,19,17,15,13,11,9,7,5,3,0}
local VA = {30,25,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0,-1,-2,-3,-4,-5,-6}
local function engineStatEffect(v)
  for i = 1, #TH do if v >= TH[i] then return VA[i] end end
  return VA[#VA]
end
Game = {BolsterAmount = cfg.bolster}
function Game.GetStatisticEffect(v)
  -- mem.call passes an int32: fractional model stats are converted (assumed truncation, see BALANCE_MODEL.md)
  local iv = cfg.statRound == "round" and math.floor(v + 0.5) or (v >= 0 and math.floor(v) or math.ceil(v))
  local t = {Value = iv, Result = engineStatEffect(iv)}
  if events.GetStatisticEffect then events.GetStatisticEffect(t) end
  return t.Result
end

-- ---------------- loader ----------------
local cache = {}
local function fileLines(rel)
  if not cache[rel] then
    local t = {}
    for l in io.lines(ROOT .. "/" .. rel) do t[#t+1] = l end
    cache[rel] = t
  end
  return cache[rel]
end
local function chunk(rel, a, b, extra)
  local l = fileLines(rel)
  local src = table.concat(l, "\n", a, b or #l) .. "\n" .. (extra or "")
  local f, err = load(src, "@" .. rel .. ":" .. a)
  assert(f, err)
  return f()
end
local G = "Scripts/General/"
chunk(G .. "zzMaw-Stats.lua", 262, 266)        -- STAT_DAMAGE_DIVISOR, GetMightDamageMultiplier
chunk(G .. "zzMaw-Stats.lua", 295, 297)        -- getIntellectDamageMultiplier
chunk(G .. "zzMaw-Stats.lua", 946, 950)        -- events.GetStatisticEffect (>=25 -> floor(v/5))
chunk(G .. "zzMaw-Stats.lua", 1461, 1529)      -- masteryForSkill .. GetDifficulty
chunk(G .. "zzMAW-Skills.lua", 23, 182)        -- baseRecovery .. skillMasteryLadder
chunk(G .. "zzMAW-Skills.lua", 408, 418)       -- SPELL_HASTE_DIVISOR, GetSpeedBonusFromStat
chunk(G .. "zzMaw-Items.lua", 444, 893)        -- enchant strength, loot tier, rarity, expected enchant fraction
chunk(G .. "zzMaw-Items.lua", 2045, 2062)      -- enchantbonusdamage, ENCHANT_DAMAGE_MULT
chunk(G .. "zzMaw-Items.lua", 2095, 2095)      -- LEGENDARY19_ENCHANT_MULT
chunk(G .. "zzMaw-Items.lua", 4282, 4282)      -- fireAuraDamage
chunk(G .. "zzMaw-Spells.lua", 80, 82)         -- getHealPersonalityBonus
chunk(G .. "zzMaw-Spells.lua", 2087, 2091)     -- ascendHealingValues
chunk(G .. "zzMaw-Spells.lua", 2361, 2380)     -- getBaseHealingSpells
chunk(G .. "zzMaw-Spells.lua", 2682, 2718)     -- GetBuffMultiplier, GetBuffStatPct, buffPower
if cfg.buff == "mapping" then
  chunk("Scripts/Global/zzMaw_Mapping.lua", 36, 56)  -- the table AfterLoadMap installs on every map load
end
chunk("Scripts/Modules/MawCore/Formulas.lua", 1, 318)
chunk("Scripts/Modules/MawCore/ItemLevel.lua", 1, 86)
chunk(G .. "zzzMaw_Experience.lua", 7, 45)     -- calcLevel / calcExp
chunk(G .. "zzMaw-Monsters.lua", 5, 25)        -- bolsteredLevel, MawTierB
chunk(G .. "zzMaw-Monsters.lua", 770, 796)     -- density tables, GetMonsterExpMult
-- encStrUp selection done in zzMaw-Items.lua:895-901 (BeforeLoadMap)
encStrUp = vars.AusterityMode and encStrUpAusterity or encStrUpNormal
-- Estimates.lua with its locals exported for the golden table
chunk("Scripts/Modules/MawCore/Estimates.lua", 1, 755, [[
EXPORT = {armor = estimateArmorClass, res = estimateResistance, enchRes = estimateEnchantResistance,
  hit = estimateChanceToGetHit, phys = estimatePhysicalDamageTaken, magic = estimateMagicDamageTaken,
  leg = estimateLegendaryDamageTaken, cover = coverMultiplier, worn = estimateWornArmor}
]])

-- ---------------- output ----------------
local levels = {}
if #arg > 10 then
  for i = 11, #arg do levels[#levels+1] = tonumber(arg[i]) end
else
  for l = 1, 100 do levels[#levels+1] = l end
  for l = 110, 600, 10 do levels[#levels+1] = l end
  for l = 700, 2000, 100 do levels[#levels+1] = l end
end
local function g(x) return string.format("%.6g", x) end
print(table.concat({"level","difficulty","skill","mastery","stat","geared","max_enchant","health","mana","armor_class",
  "resistance","enchant_resistance","phys_taken","magic_taken","chance_hit","legendary_taken","cover_mult","vitality",
  "attack","power","spell_power","monster_hp_b","monster_dmg_b","exp_mult"}, ","))
for _, L in ipairs(levels) do
  local vit, phys, magic, taken, health = getPlayerEstimatedVitality(L)
  print(table.concat({L, GetDifficulty(), g(estimateSkill(L)), masteryPerLevel(L), g(estimateStat(L)),
    g(gearedFraction(L)), g(GetMaxEnchantStrength(L)), g(health), g(getPlayerEstimatedMana(L)),
    g(EXPORT.armor(L)), g(EXPORT.res(L)), g(EXPORT.enchRes(L)), g(phys), g(magic), g(EXPORT.hit(L)),
    g(EXPORT.leg(L)), g(EXPORT.cover(L)), g(vit), g(getPlayerEstimatedAttack(L)), g(getPlayerEstimatedPower(L)),
    g(getPlayerEstimatedSpellPower(L)), g(getMonsterHealth(nil, L)), g(getMonsterDamage(nil, L)),
    g(GetMonsterExpMult())}, ","))
end
