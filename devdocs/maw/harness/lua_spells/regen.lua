local function spAt(lvl) if lvl<2 then return 0 end local q=math.floor(lvl/10); local r=lvl-q*10; return 5*(lvl-1)+5*q*(q-1)+q*(r+1) end
local function lvlFromPts(p) return (math.sqrt(1+8*(p+1))-1)/2 end
local function estimateSkill(l) return lvlFromPts(spAt(l)/5) end
for _,l in ipairs{20,40,50,100,200,400} do io.write(string.format("estimateSkill(%d)=%.1f  ",l,estimateSkill(l))) end print()
print("Meditation aura SP/s (in combat, no recent loss: mult 1; x2 after 20 s no SP loss; x4 out of combat)")
print("| caster level | s | FSP 300 | FSP 1000 | FSP 3000 |")
for _,r in ipairs{{40,7},{50,20},{100,30},{200,50},{400,50}} do
  local l,s=r[1],r[2]; local e=estimateSkill(l)
  local row=string.format("| %d | %d |",l,s)
  for _,f in ipairs{300,1000,3000} do row=row..string.format(" %.1f |",(0.01*f^0.35*e^1.4+1)*(1+0.02*math.min(s,50))) end
  print(row)
end
print("Regeneration aura HP/s (mult 1)")
print("| caster level | s | FHP 500 | FHP 2000 | FHP 8000 |")
for _,r in ipairs{{40,7},{50,20},{100,30},{200,50},{400,50}} do
  local l,s=r[1],r[2]; local sk=l^0.65*(1+math.min(s,50)*5/100)
  local row=string.format("| %d | %d |",l,s)
  for _,f in ipairs{500,2000,8000} do row=row..string.format(" %.1f |", f^0.5*sk^1.25*0.005) end
  print(row)
end
print("Personality mana factor 0.99^(Pers/(10+0.06*min(totalLevel,1000)))")
for _,r in ipairs{{50,20},{100,100},{300,200},{500,500},{1000,1000},{2000,1000}} do
 print(r[1],r[2],string.format("%.3f",0.99^(r[1]/(10+0.06*math.min(r[2],1000)))))
end
print("Heal personality mult 1+Pers/min(1000+3*lvl,4000)")
for _,r in ipairs{{50,20},{200,100},{500,300},{1000,500},{2000,1000}} do print(r[1],r[2],string.format("%.3f",1+r[1]/math.min(1000+3*r[2],4000))) end
-- Heal GM skill 20 asc 20 GM
local function round(x) return math.floor(x+0.5) end
local function ah(s,b,sc) return round(sc*(1+0.02*s)*1.015^s), round(b*(1+0.01*s*s)*1.015^s) end
print("Heal (68) GM, Body 20: base 16 + 6/pt")
for _,a in ipairs{0,10,20,30,50} do local sc,b=ah(a,16,6); print(a, b, sc, b+sc*20) end
print("Greater Heal (74) GM, Body 30: 40+10/pt")
for _,a in ipairs{0,10,20,30,50} do local sc,b=ah(a,40,10); print(a, b, sc, b+sc*30) end
-- heal cost
local function hc(c,s,m) return round(c*(1+s*0.125)*1.04^s*(1-0.125*m)) end
print("Heal GM cost 8 at asc s/m:", hc(8,0,0),hc(8,10,2),hc(8,20,4),hc(8,30,4),hc(8,50,4))
