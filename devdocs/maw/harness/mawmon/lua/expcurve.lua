function round(x) if x%1>=0.5 then x=x-x%1+1 else x=x-x%1 end return x end
local l = {}
for s in io.lines(arg[1] .. "/Scripts/General/zzzMaw_Experience.lua") do l[#l+1] = s end
assert(load(table.concat(l, "\n", 7, 45)))()
l = {}
for s in io.lines(arg[1] .. "/Scripts/General/zzMaw-Monsters.lua") do l[#l+1] = s end
assert(load(table.concat(l, "\n", 5, 25)))()
print("E")
for _, L in ipairs({1,2,3,5,10,20,50,99,100,101,102,110,150,200,250,300,400,500,600,700,800,1000,1200,1500,2000,2001,2500,3000}) do
  print(string.format("E\t%d\t%.0f\t%.0f\t%.0f", L, calcExp(L), 500*L*(L-1), L < 2000 and calcExp(L+1)-calcExp(L) or 0))
end
for _, f in ipairs({0, 20, 50, 100, 200, 500}) do
  for _, n in ipairs({5, 10, 30, 50, 100}) do
    print(string.format("B\t%d\t%d\t%.3f", f, n, bolsteredLevel(f, n)))
  end
end
