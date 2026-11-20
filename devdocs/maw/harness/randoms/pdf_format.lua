dofile(HERE.."golden.lua")
local function fmt(x) x=x*100 if x<0.00005 then return "—" elseif x>=9.995 then return string.format("%.1f",x) else return string.format("%.2f",x) end end
local names={[3]="MAW",[4]="Hard",[5]="Hell",[6]="Nightmare",[7]="Doom",[8]="Road to Insanity",[9]="Beyond Madness"}
for _,d in ipairs{3,4,5,6,7,8,9} do for _,boss in ipairs{false,true} do
  print(string.format("== %s %s", names[d], boss and "Bosses" or "Regular"))
  for t=0,20,2 do
    local x = distribution(t,d,boss,"pity")
    local row = {string.format("%2d",t)}
    for r=1,7 do row[#row+1]=string.format("%6s",fmt(x[r])) end
    print(table.concat(row," "))
  end
  local x = distribution(20,d,boss,"pity")
  local ap=x[5]+x[6]+x[7]+x[8]
  print(string.format("   tier20: 1 in %.1f Ancient+, Celestial 1 in %.0f", 1/ap, 1/x[8]))
end end
