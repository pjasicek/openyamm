-- Port of MAW ef23ee17 potion formulas (reimplemented for analysis only).
-- Sources: zzAlchemy.lua, zzMaw-Spells.lua:2655-2700,3111-3215, MawCore/Estimates.lua, Formulas.lua, zzMaw-Items.lua.
local DIFF = tonumber(arg[1] or 3)          -- GetDifficulty(): 3 baseline (bolster 100), 7 Doom, 8 insanity, 9 madness
local mode = { madness = DIFF == 9, insanity = DIFF == 8, doom = DIFF == 7 }

local function round(x) if x % 1 >= 0.5 then return x - x % 1 + 1 end return x - x % 1 end

-- Rarity model (zzMaw-Items.lua:574-700, 757-866)
local R = {Common=1,Uncommon=2,Rare=3,Epic=4,Ancient=5,Primordial=6,Legendary=7,Celestial=8}
local rarityUpgradeChance = {[8]=0.002,[7]=0.03,[6]=0.04,[5]=0.12}
local rarityDifficultyMult = {1,1,1,1.1,1.2,1.4,1.6,1.8,2}
local enchantChances = {[4]={Base=5,PerTier=0.75,Cap=20},[3]={Base=20,PerTier=2,Cap=60},
  [2]={Base=60,PerTier=1,Cap=80},[1]={Base=100,PerTier=0,Cap=100}}
local rarityBandMult = {{},{},{},{[4]=1.5,[3]=1.4,[2]=1.4},{[4]=2,[3]=1.8,[2]=1.6},{[4]=2.5,[3]=2.2,[2]=1.8},
  {[4]=3,[3]=2.6,[2]=2},{[4]=4,[3]=3,[2]=2.2},{[4]=5.5,[3]=3.4,[2]=2.4}}
local enchantStrengthRange = {[8]={Min=25,Max=25},[6]={Min=25,Max=25},[5]={Min=20,Max=25},[7]={Min=16,Max=20}}
local DEF = {Min=8,Max=20}
local DIV = 20
local enchantCount = {0,1,2,3,3,3,3,3}
local function encChance(r,t) local c=enchantChances[r] return math.min(c.Base+c.PerTier*t,c.Cap) end
local function bands(t,d)
  local mult=rarityBandMult[d] or {} local w,total,prev={},0,0
  for r=4,1,-1 do local th=encChance(r,t) local x=math.max(th-prev,0)*(mult[r] or 1) w[r]=x total=total+x prev=th end
  for r,x in pairs(w) do w[r]=x/total*100 end return w
end
local function baseMult(t,d) return (rarityDifficultyMult[d] or 1)*(encChance(2,t)/enchantChances[2].Cap) end
local function dist(t,d)
  local b=bands(t,d) local out={} for r=1,4 do out[r]=(b[r] or 0)/100 end
  local epic=out[4] local m=baseMult(t,d) local left=1
  for r=8,5,-1 do local ch=math.min(rarityUpgradeChance[r]*m,1) out[r]=epic*left*ch left=left-left*ch end
  out[4]=epic*left return out
end
local function mean(r) local g=enchantStrengthRange[r] or DEF return (g.Min+g.Max)/2/DIV end
local function frac(r) return enchantCount[r]/enchantCount[8]*mean(r)/mean(6) end
local order={} for r=1,8 do order[#order+1]=r end table.sort(order,function(a,b) return frac(a)<frac(b) end)
local function expectedFrac(t,drops,d)
  local ds=dist(t,d) local n=math.max(drops or 1,1) local e,below=0,0
  for _,r in ipairs(order) do local c=below+(ds[r] or 0) e=e+frac(r)*(c^n-below^n) below=c end return e
end
local TIER_LEVELS=15
local function lootTier(l) return l/TIER_LEVELS+math.min(1+l/TIER_LEVELS,6) end
local function encStrUp(t) if t<=12 then return 1+t*2 end return 25+math.min((t-12)*3,75) end
local function extraPower() if mode.insanity then return 1.2 elseif mode.doom then return 1.1 end return 1 end
local function maxEnchant(l) return encStrUp(lootTier(l))*extraPower()*((1.25-1)*0.4+1) end
local DENS={0.40,0.40,0.40,0.43,0.43,0.47,0.59,0.66,0.70}
local function seen(l,dens) return (l/(3.6+l/140)+1)*dens end
local function geared(l)
  local t=lootTier(l)
  return (l+20)/(l+100)*expectedFrac(t,seen(l,DENS[DIFF]),DIFF)/expectedFrac(t,seen(l,1),9)
end
-- skills (Estimates.lua:79-99, zzMaw-Stats.lua:1462-1505)
local function th() if mode.madness then return {0,10,24,40} elseif mode.insanity then return {0,8,16,25} end return {0,4,7,10} end
local function pointsAt(l) if l<2 then return 0 end local q=math.floor(l/10) local r=l-q*10 return 5*(l-1)+5*q*(q-1)+q*(r+1) end
local function fromPoints(p) return (math.sqrt(1+8*(p+1))-1)/2 end
local function estimateSkill(l) return fromPoints(pointsAt(l)/5) end
local function masteryFor(S) local t=th() for i=4,1,-1 do if S>=t[i] then return i end end return 1 end
local function gradual(tbl,s,m)
  m=math.max(m or 0,0) if m<1 then return tbl[0] or 0 end
  local t=th() local i=math.min(m,#t) local from=t[i] local to=t[i+1] or from*1.4
  local prev=tbl[m-1] or 0 local cur=tbl[m] or prev
  if to<=from then return cur end
  return prev+(cur-prev)*math.min(math.max((s-from)/(to-from),0),1)
end
local function gradualRow(tbl,s,m) if m<=1 then return tbl[1] or 0 end return gradual(tbl,s,m) end
local function statPct(s,light) return math.min(10+s/(light and 7 or 5),20)/100 end
local function buffRamp(s) local t=th() return math.min(math.max((s-t[2])/(t[3]-t[2]),0),1) end
local function statEffect(v)   -- MM8 table below 25, MAW floor(v/5) from 25 (zzMaw-Stats.lua:947)
  if v>=25 then return math.floor(v/5) end
  local t={{21,4},{19,3},{17,2},{15,1},{13,0},{11,-1},{9,-2},{7,-3},{5,-4},{3,-5}}
  for _,p in ipairs(t) do if v>=p[1] then return p[2] end end return -6
end
local function estimateStat(l)
  local skill=estimateSkill(l)
  return (17+math.min(l,500)*0.2+3*13.75*maxEnchant(l)*0.25*geared(l))*(1+statPct(skill,true)*buffRamp(skill))
end
local bodybuildingHP={[0]=0,0.5,1,1.5,2}
function estimateHealth(l)
  local per=math.min(6*l/(mode.madness and 330 or 210),6)+3
  local stat=estimateStat(l) local skill=estimateSkill(l) local m=masteryFor(skill)
  local hp=stat/10 local flat=hp*math.min(1+hp/50,5)*4
  local bbm=math.min(m,3)
  local bbFlat=skill*gradualRow({1,2,3},skill,bbm)
  local bbPct=gradual(bodybuildingHP,skill,bbm)
  local h=25+per*l+(stat/5+bbFlat)*per+flat
  return h*(1+bbPct*skill/100)*(1+stat/1000)
end
function estimateMana(l)
  local per=math.min(6*l/(mode.madness and 330 or 210),6)+3
  local stat=estimateStat(l) local skill=estimateSkill(l) local m=masteryFor(skill)
  local pool=15+per*(l+2*statEffect(stat)+skill*gradualRow({1,2,3,5},skill,m))
  local enl=gradualRow({0.5,1,1.5,2},skill,m)/100*skill
  return pool*(1+enl)
end
-- potion heals (zzAlchemy.lua:410-425)
local HEAL={[222]={"HP",20,0.25},[223]={"SP",10,0.25},[247]={"HP",50,0.35},[248]={"SP",50,0.35}}
function potionHeal(id,p) local h=HEAL[id] local pool=h[1]=="SP" and estimateMana(p) or estimateHealth(p) return round(h[2]+pool*h[3]) end
-- potion buffs (zzMaw-Spells.lua:2655-2700, 3111-3135)
local buffPower={[5]={10,2},[17]={15,3},[51]={15,3},[38]={20,2},[46]={20,2},[3]={10,2},[83]={20,2},[85]={10,2},[47]={5,1},[71]={5,2}}
local function frac2(p) local t=math.min(math.max(p,0),200)/200 return 0.75+0.75*t end
local function pskill(p,spell) local span=(spell==83 or spell==85) and 70 or 50 return span*(frac2(p)-1) end
local function plevel(p) return p*0.5*frac2(p) end
local function mult(spell,s) local b=buffPower[spell] return b[1]/100+b[2]*s/1000 end
local function flat(spell,s,l,dop) local b=buffPower[spell] return (b[1]+l/4)*(1+b[2]/100*s/(dop and 1.4 or 1)) end
local function regen(fhp,p) local s=math.floor(p/2) return fhp^0.5*s^1.25*(5/1000) end

local P={0,10,50,100,200,500}
print(("difficulty %d"):format(DIFF))
print("power | heal222 | sp223 | heal247 | sp248 | estHP(lvl=P) | estSP(lvl=P)")
for _,p in ipairs(P) do
  print(("%5d | %7d | %5d | %7d | %5d | %9.0f | %9.0f"):format(p,potionHeal(222,p),potionHeal(223,p),potionHeal(247,p),potionHeal(248,p),estimateHealth(p),estimateMana(p)))
end
if DIFF==3 then
print("\npower | f | skill | lvl | Haste% | Heroism% | Shield% | StoneSkinAC | BlessAtk | BlessAcc% | stat%(240-250) | ResFlat(249/250) | DoG%(257) | DoP res(263) | regen233 HP/s@1000HP | med232 skill")
for _,p in ipairs(P) do
  local s=pskill(p) local l=plevel(p) local sw=pskill(p,83)
  print(("%5d | %.3f | %6.2f | %6.2f | %5.1f | %5.1f | %5.1f | %6.1f | %6.1f | %4.1f | %4.1f | %6.1f | %4.1f | %6.1f | %6.2f | %d"):format(
    p,frac2(p),s,l,mult(5,s)*100,mult(51,s)*100,mult(17,s)*100,flat(38,s,l),flat(46,s,l),statPct(s)*100,statPct(s)*100,
    flat(3,s,l),statPct(sw,true)*100,flat(85,sw,l,true),regen(1000,p),math.ceil(p^0.5/1.5)+1))
end
print("\nblack potions: step=floor(min(P,500)/50)")
for _,p in ipairs({10,50,100,200,500}) do local st=math.floor(math.min(p,500)/50)
  print(("P=%d step=%d stat(252-254)=+%d res(261/262)=+%d transcendence=%d SP total"):format(p,st,st*20,st*30,5*st*st+15*st)) end
print("\nhotkeys: G heals round(P^1.4)+10; V adds 20+2P (shows round(P^1.4*2/3)+10)")
for _,p in ipairs({10,50,100,200}) do print(p, round(p^1.4)+10, 20+2*p, round(p^1.4*2/3)+10) end
print("\nreagent power (shown/used before alchemy): floor(base*(1+B*0.25/20)+0.75B)")
for _,b in ipairs({1,5,10,20,30,45}) do local row={} for _,B in ipairs({0,10,50,100,200}) do
  row[#row+1]= B>0 and math.floor(b*((B*0.25)/20+1)+B*0.75) or b end print("base "..b..": B=0,10,50,100,200 -> "..table.concat(row,", ")) end
end
