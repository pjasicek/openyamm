-- Loads the map-level tables of zzMaw-Monsters.lua (lines 946-1811) and dumps them as TSV.
function round(x) if x%1>=0.5 then x=x-x%1+1 else x=x-x%1 end return x end
local f = assert(io.open(arg[1]))
local lines = {}
for l in f:lines() do lines[#lines+1] = l end
local chunk = table.concat(lines, "\n", 946, 1811)
chunk = chunk:gsub("local mm6MapProgression", "mm6MapProgression")
             :gsub("local mm7MapProgression", "mm7MapProgression")
             :gsub("local mm8MapProgression", "mm8MapProgression")
assert(load(chunk))()
local function keys(t) local k={} for n in pairs(t) do k[#k+1]=n end table.sort(k) return k end
for _, n in ipairs(keys(mapLevels)) do
  local v = mapLevels[n]
  print("L", n, v.Low, v.Mid, v.High)
end
for _, n in ipairs(keys(horizontalMaps)) do print("H", n) end
for _, n in ipairs(keys(madnessStartingMaps)) do print("S", n) end
for w, t in pairs({mm6=mm6MapProgression, mm7=mm7MapProgression, mm8=mm8MapProgression}) do
  for _, n in ipairs(keys(t)) do print("P", w, n, t[n]) end
end
for _, n in ipairs(keys(madnessMapLevels)) do print("M", n, madnessMapLevels[n]) end
