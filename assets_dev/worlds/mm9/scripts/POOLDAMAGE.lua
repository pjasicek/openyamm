-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "POOLDAMAGE.scr"
script.includes = {}
script.labels = {}


-- PoolDamage.scr
-- Brett Yagi
-- This script is controls the damage brush for the pool
-- damage brush
-- Parameters
-- 0 - Marker that damagebrush will move to and from
-- 1 - Speed at which the damage brush moves
script.labels["dn"] = function(ctx)
    -- POOLDAMAGE.scr:32
    do return ctx:exit(1) end -- POOLDAMAGE.scr:35
end

script.labels["turnoff"] = function(ctx)
    -- POOLDAMAGE.scr:38
    ctx:self():moveToPos("bx", "by", "bz", "nSpeed", "dn") -- POOLDAMAGE.scr:41
    do return ctx:exit(1) end -- POOLDAMAGE.scr:43
end

script.labels["turnon"] = function(ctx)
    -- POOLDAMAGE.scr:46
    ctx:self():moveToPos("ax", "ay", "az", "nSpeed", "dn") -- POOLDAMAGE.scr:49
    do return ctx:exit(1) end -- POOLDAMAGE.scr:51
end

script.labels["main2"] = function(ctx)
    -- POOLDAMAGE.scr:54
    ctx:state().myH = ctx:self() -- POOLDAMAGE.scr:57
    ctx:state().ma = ctx:objectOrNil("sMarker") -- POOLDAMAGE.scr:58
    ctx:state().ax, ctx:state().ay, ctx:state().az = ctx:object("ma"):pos() -- POOLDAMAGE.scr:59
    ctx:state().bx, ctx:state().by, ctx:state().bz = ctx:self():pos() -- POOLDAMAGE.scr:60
    do return ctx:exit(1) end -- POOLDAMAGE.scr:62
end

script.labels["main"] = function(ctx)
    -- POOLDAMAGE.scr:66
    ctx:getParam(0, "sMarker") -- POOLDAMAGE.scr:69
    ctx:getParam(1, "nSpeed") -- POOLDAMAGE.scr:70
    ctx:addTrigger("turnon", "turnon") -- POOLDAMAGE.scr:71
    ctx:addTrigger("turnoff", "turnoff") -- POOLDAMAGE.scr:72
    ctx:wait(0, .1, "main2") -- POOLDAMAGE.scr:73
    do return ctx:exit(1) end -- POOLDAMAGE.scr:75
end

return script
