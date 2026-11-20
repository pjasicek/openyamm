dofile(HERE.."golden.lua")
local names={[3]="MAW",[4]="Hard",[5]="Hell",[6]="Nightmare",[7]="Doom",[8]="Insanity",[9]="Madness"}
local ap={}
for _,d in ipairs{3,4,5,6,7,8,9} do for _,boss in ipairs{false,true} do
  local x=distribution(20,d,boss,"pity")
  local a=x[5]+x[6]+x[7]+x[8]
  ap[d..tostring(boss)]=a
  print(string.format("%-9s %-7s common=%.2f unc+=%.1f rare+=%.1f epic+=%.1f anc+=%.2f cel=%.3f", names[d], boss and "boss" or "regular",
    x[1]*100,(1-x[1])*100,(1-x[1]-x[2])*100,(1-x[1]-x[2]-x[3])*100,a*100,x[8]*100))
  if boss then
    -- first tier where boss Rare share is 0
    for t=0,40 do local y=distribution(t,d,true,"pity") if y[3]<1e-12 then print("   boss always >=Epic from tier "..t) break end end
  end
end
  print(string.format("   boss/regular Ancient+ ratio = %.2f", ap[d.."true"]/ap[d.."false"]))
end
print(string.format("Madness/MAW regular = %.2f, boss = %.2f", ap["9false"]/ap["3false"], ap["9true"]/ap["3true"]))
