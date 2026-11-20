dofile(arg[3])
local IL = MawCore.ItemLevel
local function req(drop, rung, minus)
  local L = drop + (math.min(math.max(rung, 1), IL.Tiers) - 1)*IL.PerTier
  return math.max(1, math.floor(IL.WearLevel(L) - minus))
end
print("drop\tpower\tr1\tr2.25\tr3.5\tr4.75\tr6\tr1_night\tr6_night\tr6_doomNight\tr6_insanity")
for _, d in ipairs{0,5,10,15,20,25,30,40,50,60,75,90,100,120,150,175,200,250,300,350,400,450,500,600,750,1000} do
  print(table.concat({d, IL.PowerFor(d), req(d,1,0), req(d,2.25,0), req(d,3.5,0), req(d,4.75,0), req(d,6,0),
    req(d,1,6), req(d,6,6), req(d,6,9), req(d,6,9)}, "\t"))
end
