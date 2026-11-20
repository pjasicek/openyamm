local step={0.5,0.65,0.8,1}
local cc={ {"Slow (35)",6,1},{"Charm (60, Mind)",10,2},{"Vampire Charm (113)",10,2},{"Berserk (62)",4.5,2},{"Mass Fear (63)",3,2},
 {"Dragon Fear (122)",4,2},{"Enslave (66)",5,2},{"Paralyze (81)",3,3},{"Shrinking Ray (92) flat",4,1},{"Dark Grasp (96)",6,1},
 {"Turn Undead (48)",5,2},{"Control Undead (94)",10,2}}
print("Durations in real seconds (1 game minute = 2 s), party (not solo), first cast (no DR), non-boss")
print("| Spell | DR group | N asc0 res0 | GM asc0 res0 | GM asc20 res0 | GM asc20 res50 | GM asc50 res100 |")
for _,c in ipairs(cc) do
  local name,base,g=c[1],c[2],c[3]
  local flat = name:find("flat")
  local function d(m,asc,res) local mm= flat and 1 or step[m]; local a=asc; if name:find("122") then a=0 end; return base*2*mm*1.015^a/(1+res/100) end
  print(string.format("| %s | %d | %.1f | %.1f | %.1f | %.1f | %.1f |",name,g,d(1,0,0),d(4,0,0),d(4,20,0),d(4,20,50),d(4,50,100)))
end
-- DR simulation: window 10 game minutes. cast at expiry, repeated
local function mult(r) if r>=0.6 then return 0 elseif r>=0.45 then return 0.25 elseif r>=0.3 then return 0.5 elseif r>=0.15 then return 0.75 end return 1 end
local function sim(name, dur, gap, boss)
  local hist={}; local t=0; local out={}
  for i=1,12 do
    local ws=t-10; local tot=0
    for _,e in ipairs(hist) do local s=math.max(e[1],ws); local en=math.min(e[2],t); if en>s then tot=tot+en-s end end
    local r=tot/10; local m=mult(r); local d=dur*m
    if boss and m>0 then d=d/2 end
    if m>0 then hist[#hist+1]={t,t+d} end
    out[#out+1]=string.format("t=%.1fs ratio=%.2f -> %.1fs", t*2, r, d*2)
    t=t+math.max(d,gap)
  end
  print(name); for _,l in ipairs(out) do print("  "..l) end
end
print()
sim("Group-2 CC lasting 8 s (4 game min), recast as soon as it ends (min 1 s gap)", 4, 0.5, false)
sim("Same on a boss (NameId 220-299): halved after DR", 4, 0.5, true)
sim("Short 3 s stun-type (1.5 min), recast every 3 s", 1.5, 1.5, false)
