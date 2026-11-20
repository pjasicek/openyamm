dofile(HERE.."golden.lua")
-- self-check: nominal regular == MAW's own GetRarityDistribution
local maxerr=0
for d=1,9 do for t=0,20 do
  local a = distribution(t,d,false,"nominal"); local b = GetRarityDistribution(t,d)
  for r=1,8 do maxerr=math.max(maxerr, math.abs(a[r]-b[r])) end
end end
io.stderr:write("max |nominal - GetRarityDistribution| = "..maxerr.."\n")
local out = io.open(OUT, "w")
out:write("difficulty_index,difficulty,source,model,loot_tier,upgrade_mult,common,uncommon,rare,epic,ancient,primordial,legendary,celestial,ancient_plus,one_in_ancient_plus,one_in_celestial\n")
local diffNames={"Easy","Normal","MAW","Hard","Hell","Nightmare","Doom","RoadToInsanity","BeyondMadness"}
for d=1,9 do for _,src in ipairs{"regular","boss"} do for _,mode in ipairs{"pity_longrun","nominal"} do for t=0,20 do
  local dist, mult = distribution(t, d, src=="boss", mode=="nominal" and "nominal" or "pity")
  local ap = dist[5]+dist[6]+dist[7]+dist[8]
  local row = {d, diffNames[d], src, mode, t, string.format("%.6f", mult)}
  for r=1,8 do row[#row+1] = string.format("%.6f", dist[r]*100) end
  row[#row+1] = string.format("%.6f", ap*100)
  row[#row+1] = ap>0 and string.format("%.1f", 1/ap) or ""
  row[#row+1] = dist[8]>0 and string.format("%.0f", 1/dist[8]) or ""
  out:write(table.concat(row, ",").."\n")
end end end end
out:close()
