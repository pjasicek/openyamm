dofile(HERE.."harness.lua")
local SkillList={"Summoner","Venomous","Exploding","Thorn","Reflecting","Adamantite","Swapper","Regenerating","Puller","Leecher","Swift","Fixator","Shadow","Plagueborn"}
local function u(seed) return ((seed*9301+49297)%233280)/233280 end
print("step per boss", (31*9301)%233280/233280, "omni-brood offset", ((456-123)*9301)%233280/233280, "skill-brood offset", ((0-123)*9301)%233280/233280)
-- simulate Beyond Madness seeded path: counters, chanceMult 3
for _,base in ipairs{1761123456, 1700000000, 1800000001} do
  local vars_={total=0, bp=0, op=0}
  local cnt={}; local brood, omni = 0,0
  local N=100000
  for k=1,N do
    local seed=base
    local skill=SkillList[math.floor(u(seed+vars_.total*31)*#SkillList)+1]
    local ub=u(seed+vars_.total*31+123); local uo=u(seed+vars_.total*31+456)
    local pb=pity_chance(0.03, vars_.bp); local po=pity_chance(0.003, vars_.op)
    local sp
    if ub<pb then sp="Broodlord"; vars_.bp=0 else vars_.bp=vars_.bp+1 end
    if not sp and uo<po then sp="Omnipotent"; vars_.op=0 elseif not sp then vars_.op=vars_.op+1 end
    if sp=="Broodlord" then brood=brood+1 elseif sp=="Omnipotent" then omni=omni+1 else cnt[skill]=(cnt[skill] or 0)+1 end
    vars_.total=vars_.total+1
  end
  local s=string.format("base=%d: Broodlord %.3f%% Omnipotent %.3f%% |", base, brood/N*100, omni/N*100)
  for _,n in ipairs(SkillList) do s=s..string.format(" %s=%.1f", n:sub(1,4), (cnt[n] or 0)/N*100) end
  print(s)
  -- first 15 skills
  local seq={} for k=0,14 do seq[#seq+1]=SkillList[math.floor(u(base+k*31)*14)+1]:sub(1,4) end
  print("  first 15 bosses:", table.concat(seq," "))
end
-- get_affix second pick
local c={} for i=1,25 do c[i]=0 end c[1]=1
local w,tot={},0 for i=1,25 do w[i]=1/(25*(c[i]+1)) tot=tot+w[i] end
print(string.format("legendary affix after one find: found=%.2f%% others=%.2f%%", w[1]/tot*100, w[2]/tot*100))
