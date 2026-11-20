dofile(HERE.."golden.lua")
-- Monte Carlo through MAW's own RollItemRarity (Epic-band rolls only), compare with renewal formula
math.randomseed(12345)
for _,cfg in ipairs{{3,20,false},{9,20,true},{6,0,false},{9,0,true}} do
  local d,t,boss = cfg[1],cfg[2],cfg[3]
  CURRENT_DIFF = d; vars = {}
  local N = 4000000
  local cnt = {0,0,0,0,0,0,0,0}
  for i=1,N do local r = RollItemRarity(t, boss, false, 1, false); cnt[r]=cnt[r]+1 end
  local mult = GetRarityBaseMultiplier(t,nil,d)*(boss and 2 or 1)
  local f = cascade(1, mult, "pity")
  local s = string.format("d=%d t=%d boss=%s mult=%.3f |", d, t, tostring(boss), mult)
  for r=4,8 do s = s..string.format(" %s mc=%.4f%% calc=%.4f%%", r, cnt[r]/N*100, f[r]*100) end
  print(s)
end
