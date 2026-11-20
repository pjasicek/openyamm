-- Hourglass: the apply path (zzAlchemy.lua:826-844) and the ALT preview (Tooltip.lua:298-331), copied
-- with the random draws fixed (stat = rolled type, u = the 0..1 draw) to compare what each produces.
local function round(x) if x%1>=0.5 then return x-x%1+1 end return x-x%1 end
local function vitality(roll, slotMult) return roll*(1+math.min(roll/50/slotMult,5)) end
local function apply(bonus1, str1, stat, u, slotMult, bolster)
  local mult=math.max((bolster-100)/1000+1,1)
  local cap=math.min(100*mult*slotMult,65535)
  return math.min(round(str1*(1+0.25*u)),cap)
end
local function preview(bonus1, str1, stat, u, slotMult, bolster)
  local mult=math.max((bolster-100)/1000+1,1)
  local cap=100*mult
  local power=str1
  if bonus1==8 then power=math.floor((-100+(100^2+power*200)^0.5)/2) end  -- 't.Bonus==9' typo: SP never
  if stat==8 or stat==9 then power=power*(1+math.min(power/50/mult,5)) end
  cap=math.min(cap*slotMult,65535)
  return math.min(round(power*(1+0.25*u)),cap)
end
print("enc1 | str1 | rolled enc2 | slot | apply stored | apply shown | preview shown")
for _, c in ipairs({{1,40,4,1},{1,40,8,1},{8,40,4,1},{8,40,9,1},{9,40,8,1},{8,80,8,2},{1,90,9,1.5},{17,6,8,1}}) do
  local b1, s1, st, sm = table.unpack(c)
  local a = apply(b1, s1, st, 0.5, sm, 100)
  local shown = (st==8 or st==9) and round(vitality(a, sm)) or a
  print(string.format("%d | %d | %d | x%.2f | %d | %d | %d", b1, s1, st, sm, a, shown, preview(b1, s1, st, 0.5, sm, 100)))
end
