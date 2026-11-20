local function dice(s) return (1+0.02*s)*1.025^s end
local function add(s) return (1+0.01*s*s)*1.025^s end
local function healpt(s) return (1+0.02*s)*1.015^s end
local function healbase(s) return (1+0.01*s*s)*1.015^s end
local function mana(s,m) return (1+0.125*s)*1.04^s*(1-0.125*m) end
local function ccmana(s,m) return (1+0.2*s)*1.03^s*(1-0.125*m) end
local function cast(s) return 1.015^s end
-- tooltip (MC/SkillTooltip.lua:169-173) versions
local function tthealpt(s) return (1+0.05*s)*1.02^s end
local function tthealbase(s) return (1+0.03*s*s)*1.02^s end
print("| s | m | dice | flat add | heal/pt | heal base | mana | CC mana | cast time / CC duration |")
for _,row in ipairs{{1,1},{4,1},{5,1},{7,2},{10,2},{12,3},{15,3},{20,4},{25,4},{30,4},{40,4},{50,4},{60,4},{75,4},{100,4}} do
  local s,m=row[1],row[2]
  print(string.format("| %d | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.3f |",s,m,dice(s),add(s),healpt(s),healbase(s),mana(s,m),ccmana(s,m),cast(s)))
end
print()
print("mana at m=0 vs m=1 vs m=4, s=5,10,20,30,50 (doc check)")
for _,s in ipairs{5,10,20,30,50} do print(s, string.format("%.2f %.2f %.2f", mana(s,0), mana(s,1), mana(s,4))) end
print()
print("tooltip vs code healing (s=10,20,30)")
for _,s in ipairs{10,20,30} do print(s, string.format("code %.2f/%.2f  tooltip %.2f/%.2f", healpt(s),healbase(s),tthealpt(s),tthealbase(s))) end
-- damage per mana and per second for a reference spell: Fire Bolt 8 + 1d2/pt, school skill 20, GM fire (cost 2, delay 90)
print()
print("Fire Bolt (8 add, 1d2) at Fire 20 GM, base cost 2, delay 90:  s, avgDmg, cost, dmg/mana, cast delay")
local function round(x) return math.floor(x+0.5) end
for _,row in ipairs{{0,0},{5,1},{10,2},{20,4},{30,4},{50,4}} do
  local s,m=row[1],row[2]
  local dmax=round(2*dice(s)); local dmin=1; local a=round(8*add(s))
  local avg=a+20*(dmin+dmax)/2
  local cost=math.ceil(2*mana(s,m))
  print(s,m,avg,cost,string.format("%.1f",avg/cost), round(90*cast(s)))
end
print()
print("Incinerate (19 add, 1d21) at Fire 30 GM, base cost 30, delay 90")
for _,row in ipairs{{0,0},{5,1},{10,2},{20,4},{30,4},{50,4}} do
  local s,m=row[1],row[2]
  local dmax=round(21*dice(s)); local a=round(19*add(s))
  local avg=a+30*(1+dmax)/2
  local cost=math.ceil(30*mana(s,m))
  print(s,m,avg,cost,string.format("%.1f",avg/cost), round(90*cast(s)))
end
