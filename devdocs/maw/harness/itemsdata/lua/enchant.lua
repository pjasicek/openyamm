dofile(arg[3])
local SCR = arg[1]
local function slice(path, a, b)
  local out, n = {}, 0
  for line in io.lines(path) do n = n + 1; if n >= a and n <= b then out[#out+1] = line end end
  return table.concat(out, "\n")
end
const = {}
local DIFF = 1
function GetDifficultyExtraPower() return DIFF end
-- encStrUp, applyDifficulty, rollEnchantStrength (444-475), rarity tables (574-583, 665-674)
local chunk = slice(SCR .. "/General/zzMaw-Items.lua", 574, 583) .. "\n" .. slice(SCR .. "/General/zzMaw-Items.lua", 667, 674)
  .. "\n" .. slice(SCR .. "/General/zzMaw-Items.lua", 444, 475)
  .. "\nreturn rollEnchantStrength"
local fixed = {}
local mode = "min"
math.random = function(a, b) if mode == "min" then return a else return b end end
local roll = assert(load(chunk))()
local R = const.Rarity
print("tier\tencStrUp\tausterity\tCE_min\tCE_max\tLeg_min\tLeg_max\tAnc_min\tAnc_max\tPrim\tPrim_x1.2")
for tier = 0, 40 do
  local row = {tier, encStrUpNormal(tier), encStrUpAusterity(tier)}
  for _, r in ipairs{R.Epic, R.Legendary, R.Ancient} do
    mode = "min"; row[#row+1] = roll(tier, r)
    mode = "max"; row[#row+1] = roll(tier, r)
  end
  mode = "max"; row[#row+1] = roll(tier, R.Primordial)
  DIFF = 1.2; row[#row+1] = roll(tier, R.Primordial); DIFF = 1
  for i = 1, #row do if type(row[i]) == "number" and row[i] == math.floor(row[i]) then row[i] = math.floor(row[i]) end end
  print(table.concat(row, "\t"))
end
