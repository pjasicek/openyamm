local cost={[3]=60,[4]=90,[14]=60,[25]=60,[36]=60,[58]=60,[69]=60,[5]=120,[8]=40,[17]=75,[28]=150,[38]=75,[46]=75,[47]=75,[50]=120,[51]=120,[56]=120,[71]=120,[73]=75,[75]=180,[83]=200,[85]=150,[86]=300,[91]=150,[95]=10}
local names={[3]="Fire Res",[4]="Fire Aura",[14]="Air Res",[25]="Water Res",[36]="Earth Res",[58]="Mind Res",[69]="Body Res",[5]="Haste",[8]="Immolation",[17]="Shield",[28]="Empower Magic",[38]="Stone Skin",[46]="Bless",[47]="Fate",[50]="Preservation",[51]="Heroism",[56]="Meditation",[71]="Regeneration",[73]="Hammerhands",[75]="Prot. from Magic",[83]="Day of the Gods",[85]="Day of Protection",[86]="Hour of Power",[91]="Vampiric Aura",[95]="Pain Reflection"}
local order={3,14,25,36,58,69,4,5,8,17,28,38,46,47,50,51,56,71,73,75,83,85,86,91,95}
local classes={{"SPFactor 1 (Paladin, Ranger, Seraphim, Shaman T1/T2=1/1.5)",1},{"2 (Druid T1? no: WarriorMage, Initiate, Sekhem 1.5->2)",2},{"3 (Cleric, Druid, Sorcerer, Necromancer)",3},{"4 (Priest, Wizard, Elementalist T1)",4},{"6 (Arch Mage, Lich, Warlock, Priest of Light)",6},{"8 (Master of Elements)",8}}
print("| Spell | cost | f=1 | f=2 | f=3 | f=4 | f=6 | f=8 | f=6 + Enlightenment GM |")
for _,id in ipairs(order) do
  local c=cost[id]
  local row=string.format("| %s (%d) | %d |",names[id],id,c)
  for _,f in ipairs{1,2,3,4,6,8} do row=row..string.format(" %.1f%% |", c/f) end
  row=row..string.format(" %.1f%% |", c/(6+2))
  print(row)
end
print()
-- buff values
local function mult(base,scal,s) return base+scal*s/10 end -- percent
local function flat(base,scal,s,level) return (base+level/4)*(1+scal*s/100) end
local function statpct(s,light) return math.min(10+s/(light and 7 or 5),20) end
print("| s | Haste % | Shield % | Heroism/Hammer % | Fate % | Empower (as coded: Haste row) % | stat % | DoG stat % |")
for _,s in ipairs{0,7,10,20,30,40,50} do
  print(string.format("| %d | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f |",s,mult(10,2,s),math.min(mult(15,3,s),30),mult(15,3,s),mult(5,1,s),mult(10,2,s),statpct(s),statpct(s,true)))
end
print()
print("flat: res buff (base 10) / StoneSkin, Bless (base 20) / DoP (base 10, s/1.4) at caster level L")
print("| s | L | res | AC or attack | DoP res |")
for _,r in ipairs{{7,40},{10,20},{20,50},{30,100},{50,200},{50,400},{75,400}} do
  local s,l=r[1],r[2]; local sc=math.min(s,50); local sd=math.min(s,75)
  print(string.format("| %d | %d | %.1f | %.1f | %.1f |",s,l,flat(10,2,sc,l),flat(20,2,sc,l),(10+l/4)*(1+2/100*sd/1.4)))
end
print()
print("Hour of Power vs own spell: HoP s/1.5, HoP skill cap 75 -> effective 50")
for _,s in ipairs{15,30,45,60,75} do local e=math.min(s,75)/1.5; print(s, string.format("eff %.1f haste %.1f%% shield %.1f%% fate %.1f%%",e,mult(10,2,e),math.min(mult(15,3,e),30),mult(5,1,e))) end
print()
print("Bless hit-chance bonus = 5% + 5% * min(s,50)/50")
for _,s in ipairs{0,10,25,50} do print(s, 5+5*math.min(s,50)/50) end
