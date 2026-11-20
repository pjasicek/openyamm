dofile(arg[3])
local SCR = arg[1]
local function slice(path, a, b)
  local out, n = {}, 0
  for line in io.lines(path) do n = n + 1; if n >= a and n <= b then out[#out+1] = line end end
  return table.concat(out, "\n")
end
const = {Spells = {}, Skills = {Chain = 10}}
Game.BolsterAmount = 100
vars.MAWSETTINGS = {}
local statTbl = {{0,-6},{3,-5},{5,-4},{7,-3},{9,-2},{11,-1},{13,0},{15,1},{17,2},{19,3},{21,4}}
function Game.GetStatisticEffect(v)
  if v >= 25 then return math.floor(v/5) end
  local r = -6
  for _, p in ipairs(statTbl) do if v >= p[1] then r = p[2] end end
  return r
end
assert(load(slice(SCR .. "/General/zzMaw-Items.lua", 444, 877)))()
assert(load(slice(SCR .. "/General/zzMaw-Items.lua", 2047, 2082)))()
assert(load(slice(SCR .. "/General/zzMaw-Stats.lua", 263, 267)))()
assert(load(slice(SCR .. "/General/zzMaw-Stats.lua", 1462, 1530)))()
assert(load(slice(SCR .. "/General/zzMAW-Skills.lua", 149, 153)))(); assert(load(slice(SCR .. "/General/zzMAW-Skills.lua", 169, 172)))()
assert(load(slice(SCR .. "/General/zzMaw-Spells.lua", 2665, 2668)))()
TIER_LEVELS = 15
dofile(SCR .. "/Modules/MawCore/Estimates.lua")
function GetWeaponLevelDamage(it)
  return getWeaponLevelDamage(MawCore.ItemLevel.OfItem(it), IsTwoHandedWeapon(it), GetWeaponFlatDamage(it))
end
local ids = {[4]="Cold A",[5]="Frost C",[6]="Ice D",[7]="Sparks A",[8]="Lightning C",[9]="Thunderbolts D",
  [10]="Fire A",[11]="Flame C",[12]="Infernos D",[13]="Poison A",[14]="Venom C",[15]="Acid D",[39]="Ascension",[46]="Dragon"}
local order = {4,5,6,7,8,9,10,11,12,13,14,15,39,46}
local powers = {0, 10, 20, 40, 60, 80, 100}
for _, weapon in ipairs{{5, "1H top rung (Champion's Sword)"}, {10, "2H top rung (Headsman's Reaver)"}} do
  print("# " .. weapon[2])
  local hdr = "special"
  for _, p in ipairs(powers) do hdr = hdr .. "\tP" .. p .. "(L" .. p*5 .. ")" end
  print(hdr)
  local row = {"levelDamage"}
  for _, p in ipairs(powers) do row[#row+1] = string.format("%.1f", GetWeaponLevelDamage(makeItem(weapon[1], p))) end
  print(table.concat(row, "\t"))
  for _, id in ipairs(order) do
    local row = {id .. " " .. ids[id]}
    for _, p in ipairs(powers) do
      local lo, hi = enchantDamageRange(makeItem(weapon[1], p), id)
      row[#row+1] = string.format("%d-%d", math.floor(lo), math.floor(hi))
    end
    print(table.concat(row, "\t"))
  end
end
