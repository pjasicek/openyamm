local function round(x) return math.floor(x+0.5) end
print("== Elder/Ultimate HP/SP factor (0.75+0.25n)")
local cls={{"Champion",8,0},{"MasterArcher",6,3},{"Archangel",5,3},{"LichKing",7,0},{"MasterOfElements",3,8},{"Marabou",5,1}}
for _,c in ipairs(cls) do
  io.write(string.format("%-16s", c[1]))
  for n=1,3 do local m=n>1 and (0.75+0.25*n) or 1; io.write(string.format(" n=%d HP/lvl %.2f SP/lvl %.2f |", n, c[2]*m, c[3]*m)) end
  print()
end
print("== DK Frost/Unholy flat dmg per school (gradual mastery, normal thresholds 0,4,7,10)")
local th={0,4,7,10}; local tbl={[0]=0,0.5,0.75,1,1}
local function grad(s,m) if m<1 then return 0 end local from=th[m]; local to=th[m+1] or from*1.4; local prev=tbl[m-1] or 0; local cur=tbl[m]
 return prev+(cur-prev)*math.min(math.max((s-from)/(to-from),0),1) end
for _,p in ipairs({{3,1},{5,2},{8,3},{10,4},{20,4},{50,4}}) do print(string.format("s=%d m=%d per-pt %.3f total %.1f", p[1],p[2],grad(p[1],p[2]), grad(p[1],p[2])*p[1])) end
print("== Blood Leech per hit max(FHP^0.5*s^1.5/70*(1+m/4), 2s); Superior x2")
for _,p in ipairs({{500,5,1},{1000,10,2},{2000,20,3},{5000,30,4},{20000,50,4}}) do local v=math.max(p[1]^0.5*p[2]^1.5/70*(1+p[3]/4), p[2]*2) print(string.format("FHP=%d s=%d m=%d leech %.1f superior %.1f",p[1],p[2],p[3],v,2*v)) end
print("== Shaman Body leech max(round(FHP^0.5*s^1.5/70*(0.5+m/2)), s); Mind SP s^1.25; Fire 0.1%/pt cur HP")
for _,p in ipairs({{500,5,1},{1000,10,2},{2000,20,3},{5000,30,4},{20000,50,4}}) do print(string.format("FHP=%d s=%d m=%d bodyLeech %d mindSP %.1f fire%%=%.1f", p[1],p[2],p[3], math.max(round(p[1]^0.5*p[2]^1.5/70*(0.5+p[3]/2)),p[2]), p[2]^1.25, p[2]*0.1)) end
print("== Seraph Body heal on hit s^1.3*m*2*meleeMult*(1+Pers/1000) (meleeMult=1, Pers=100/500)")
for _,p in ipairs({{5,1},{10,2},{20,3},{30,4},{50,4}}) do print(string.format("s=%d m=%d heal %d / %d", p[1],p[2], round(p[1]^1.3*p[2]*2*1.1), round(p[1]^1.3*p[2]*2*1.5))) end
print("== Assassin energy regen (0.6+0.2m)*10 /s; melee cost 50-5m; kill +(1+m)*5")
for m=0,4 do print(string.format("m=%d regen %.0f/s cost %d killSP %d maxEnergyBonus %d", m, (0.6+0.2*m)*10, 50-5*m, (1+m)*5, m*10)) end
print("== Assassination crowd cut: reduction = min(0.8,(n-1)*0.2) of flat (n = monsters within 384 incl. target)")
for n=1,6 do print(n, math.min(0.8,(n-1)*0.2)) end
print("== Dragon effective level / fang / breath (might=100, mightEffect=0 approx)")
local function eff(lvl,bol) local l=lvl; if lvl/bol>1.2 then l=math.min(lvl/2,bol) end return math.min(l,600) end
local fang={4,6,8,10}; local breath={3,4,5,6}
for _,p in ipairs({{20,20,10,2,10,2},{100,100,30,3,30,3},{200,200,50,4,50,4}}) do
  local L=eff(p[1],p[2]+1); local might=100
  local fb=(1+fang[p[4]]*p[3]/100)*(L*2+30); local favg=(fb*(1+might/1000))*(1+p[3]*0.015)
  local bb=(1+breath[p[6]]*p[5]/100)*(20+2*L); local bavg=bb*(1+might/1000)*(1+p[5]*0.015)
  print(string.format("lvl %d fang s%d m%d: %d-%d (attack +%d, recovery x%.2f); breath s%d m%d: %d-%d", p[1],p[3],p[4], round(favg*0.75),round(favg*1.25), fang[p[4]]-0+0, 1+p[3]*0.015, p[5],p[6], round(bavg*0.75), round(bavg*1.25)))
end
print("== Elementalist progress per hit tier^1.5*lvl^0.5*sqrt(partyCount) (AoE /3); hits to next tier")
local req={0,0,500,1500,5000,10000,20000,40000,80000,160000,320000}
for _,p in ipairs({{2,10,4},{6,30,4},{9,60,4},{11,100,4}}) do local g=p[1]^1.5*p[2]^0.5*p[3]^0.5 print(string.format("tier %d vs lvl %d party %d: %.1f per single-target hit", p[1],p[2],p[3],g)) end
for t=3,11 do local g=(t-1)^1.5*50^0.5*2 print(string.format("unlock tier %2d needs %6d: ~%d hits of tier %d vs lvl50 (party 4)", t, req[t], math.ceil((req[t]-req[t-1])/g), t-1)) end
print("== Elementalist stacks: dmg x(1+0.1k), cast delay x1.5/(1+0.05k), cost (base+k)*asc*(1+0.075k)")
for k=0,10,2 do print(string.format("k=%d dmg x%.2f delay x%.3f costmult(base 10) x%.3f", k, 1+0.1*k, 1.5/(1+0.05*k), (10+k)/10*(1+0.075*k))) end
print("== Elder/Ultimate: Lich reset, nothing numeric")
