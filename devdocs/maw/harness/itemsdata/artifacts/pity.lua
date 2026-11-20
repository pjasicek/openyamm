local function pity(c,f) if c>=1 then return 1 end return c^(1.38-c*f*0.5) end
local surv, mean, med = 1, 0, nil
for f=0,2000 do
  local p=math.min(pity(0.005,f),1)
  mean = mean + surv*p*(f+1)
  local ns = surv*(1-p)
  if not med and ns<=0.5 then med=f+1 end
  surv=ns
  if surv<=0 then print("certain at roll", f+1, "failures", f) break end
end
print("p0", pity(0.005,0), "p at 100", pity(0.005,100), "p at 152", pity(0.005,152), "p at 300", pity(0.005,300), "p at 500", pity(0.005,500))
print("mean rolls", mean, "median", med)
local function stu(L) local tier=L/15+math.min(1+L/15,6); local e = tier<=12 and 1+tier*2 or 25+math.min((tier-12)*3,75); return tier,e end
for _,L in ipairs{0,15,50,75,100,150,200,300,465,600,1000} do local t,e=stu(L); print("L",L,"tier",t,"encStrUp",e,"skill",math.ceil(math.max(e^0.5,e/10))) end
