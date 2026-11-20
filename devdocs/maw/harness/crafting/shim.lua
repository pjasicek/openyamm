-- Permissive MMExtension/LuaJIT shim for loading MAW files and calling their pure functions.
local Dummy
local dmt = {}
dmt.__index = function(t, k) return Dummy end
dmt.__newindex = function(t, k, v) end
dmt.__call = function(...) return Dummy end
dmt.__concat = function(a, b) return "" end
dmt.__len = function() return 0 end
dmt.__lt = function() return false end
dmt.__le = function() return false end
dmt.__unm = function() return 0 end
dmt.__add = function() return 0 end
dmt.__sub = function() return 0 end
dmt.__mul = function() return 0 end
dmt.__div = function() return 0 end
Dummy = setmetatable({}, dmt)
DUMMY = Dummy
setmetatable(_G, {__index = function(t, k) return Dummy end})
unpack = table.unpack
table.find = function(t, v) for k, x in pairs(t) do if x == v then return k end end end
bit = {
  band = function(a, b) return a & b end, bor = function(a, b) return a | b end,
  rshift = function(a, n) return a >> n end, lshift = function(a, n) return a << n end,
}
events = setmetatable({}, {__index = function() return Dummy end, __newindex = function() end})
evt = {PotionEffects = {}}
setmetatable(evt, {__index = function() return Dummy end})
const = setmetatable({
  Rarity = {Common=1, Uncommon=2, Rare=3, Epic=4, Ancient=5, Primordial=6, Legendary=7, Celestial=8},
  Skills = setmetatable({Shield=8, Leather=9, Chain=10, Plate=11, Alchemy=35}, {__index=function() return 99 end}),
}, {__index = function() return Dummy end})
vars = {}
MawCore = {Formulas = {}, ItemLevel = {}}
function loadChunk(path)
  local f = assert(io.open(path)); local src = f:read("a"); f:close()
  local fn, err = load(src, "@" .. path)
  if not fn then error(err) end
  local ok, e = pcall(fn)
  if not ok then io.stderr:write("load warning " .. path .. ": " .. tostring(e) .. "\n") end
end
