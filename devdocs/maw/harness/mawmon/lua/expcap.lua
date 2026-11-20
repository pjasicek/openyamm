local l = {}
for s in io.lines(arg[1] .. "/Scripts/General/zzzMaw_Experience.lua") do l[#l+1] = s end
assert(load(table.concat(l, "\n", 7, 45)))()
for L = 1, 3000 do if calcExp(L+1) > 0x7FFFFFFF then print("req cap first hit at level", L) break end end
for L = 1, 3000 do if calcExp(L) > 2^32-3982296 then print("exp field cap below level", L) break end end
print(calcLevel(0x7FFFFFFF), calcLevel(2^32-3982296))
