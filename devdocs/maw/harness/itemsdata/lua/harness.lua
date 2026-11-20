-- Loads MAW's real item-level/weapon/armour code against MAW's ITEMS.txt.
-- usage: lua harness.lua <MAW Scripts dir> <MAW ITEMS.txt>
local SCRIPTS, ITEMS = arg[1], arg[2]
local function slice(path, a, b)
  local out, n = {}, 0
  for line in io.lines(path) do
    n = n + 1
    if n >= a and n <= b then out[#out+1] = line end
  end
  return table.concat(out, "\n")
end
function round(x) if x%1>=0.5 then x=x-x%1+1 else x=x-x%1 end return x end
math.round = round
function table.find(t, v) for k, x in pairs(t) do if x == v then return k end end end
MawCore = {}
vars = {}
local equipNames = {weapon=0, weapon1or2=0, weapon2=1, missile=2, bow=2, armor=3, shield=4, helm=5, belt=6,
  cloak=7, gauntlets=8, boots=9, ring=10, amulet=11, weaponw=12}
local skillNames = {staff=0, sword=1, dagger=2, axe=3, spear=4, bow=5, mace=6, blaster=7, shield=8, leather=9,
  chain=10, plate=11, club=39, misc=40}
local txt = {}
local high = 0
for line in io.lines(ITEMS) do
  local c = {}
  for f in (line .. "\t"):gmatch("([^\t]*)\t") do c[#c+1] = f end
  local id = tonumber(c[1])
  if id then
    local count, sides = (c[7] or ""):match("(%d+)[dD](%d+)")
    if not count then count = (c[7] or ""):match("^%s*(%d+)%s*$"); sides = 0 end
    txt[id] = {Number=id, Name=c[3], Value=tonumber(c[4]) or 0, EquipStatName=c[5],
      EquipStat=equipNames[(c[5] or ""):lower()] or 13, Skill=skillNames[(c[6] or ""):lower()] or 40,
      Mod1DiceCount=tonumber(count) or 0, Mod1DiceSides=tonumber(sides) or 0, Mod2=tonumber(c[8]) or 0,
      NotIdentifiedName=c[11] or ""}
    if id > high then high = id end
  end
end
for i = 0, high + 1 do txt[i] = txt[i] or {Number=i, NotIdentifiedName="", EquipStat=13, Skill=40,
  Mod1DiceCount=0, Mod1DiceSides=0, Mod2=0, Value=0, Name=""} end
txt.High = high
Game = {ItemsTxt = txt}
-- GameInitialized2 edits (zzMaw-Items.lua:406-407, 1412-1435)
txt[67].NotIdentifiedName = "Mace"
txt[804].NotIdentifiedName = "Longsword"
for _, h in ipairs{46,47,48,49,50,507,838,839,840,1638,1639,1640} do txt[h].EquipStat = 1 end
dofile(SCRIPTS .. "/Modules/MawCore/ItemLevel.lua")
dofile(SCRIPTS .. "/Modules/MawCore/Formulas.lua")
assert(load(slice(SCRIPTS .. "/Modules/MawCore/Estimates.lua", 98, 143)))()
for i = 1, 2199 do
  if (i>=1 and i<=83) or (i>=803 and i<=865) or (i>=1603 and i<=1665) then
    -- dice-side rewrite is irrelevant: GetWeaponDamageRows ignores Mod2/sides
  elseif txt[i].Skill == 8 then
    txt[i].Mod2 = txt[i].Mod2*2 + txt[i].Mod1DiceCount
  end
end
oneHandedAxes, twoHandedAxes = {}, {}
for i = 1, txt.High do
  if txt[i].Skill == 3 then
    if txt[i].EquipStat == 1 then twoHandedAxes[#twoHandedAxes+1] = i else oneHandedAxes[#oneHandedAxes+1] = i end
  end
end
-- referenceAC / referenceWeaponAttack (zzMaw-Items.lua:2614-2640)
referenceAC, referenceWeaponAttack = {}, {}
for i = 0, 2199 do
  local lookup = 0
  while txt[i + lookup + 1] and txt[i].NotIdentifiedName == txt[i + lookup + 1].NotIdentifiedName do
    lookup = lookup + 1
  end
  if (txt[i].Skill >= 8 and txt[i].Skill <= 11) or txt[i].Skill == 40 then
    referenceAC[i] = txt[i + lookup].Mod2 + txt[i + lookup].Mod1DiceCount
  elseif txt[i].Skill <= 7 or txt[i].Skill == 39 then
    referenceWeaponAttack[i] = txt[i + lookup].Mod2
  end
end
-- item helpers used by the real functions
function IsArtifactWeapon(it) return false end
MawCore.Artifacts = {BaseMult = function() return 1 end}
function ItemQualityMult(it) return 1 end
assert(load(slice(SCRIPTS .. "/General/zzMaw-Items.lua", 4555, 4603)))()
function makeItem(id, maxCharges)
  return {Number=id, MaxCharges=maxCharges, T=function(self) return txt[self.Number] end}
end
assert(load(slice(SCRIPTS .. "/General/zzMAW-Skills.lua", 25, 35):gsub("const%.Skills%.(%a+)", function(n)
  return tostring(({Bow=5, Blaster=7, Staff=0, Axe=3, Sword=1, Spear=4, Mace=6, Dagger=2})[n]) end)))()
assert(load(slice(SCRIPTS .. "/General/zzMAW-Skills.lua", 424, 440)))()
