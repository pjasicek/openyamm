-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BATHFURNACE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- BathFurnace.scr
-- Brett Yagi
-- This script is controls the furnace pistons
-- and turns on and off the damage brushes in water
-- Parameters
-- 0 - Marker that damagebrush will move to and from
-- 1 - Speed at which the damage brush moves
script.labels["dn"] = function(ctx)
    -- BATHFURNACE.scr:28
    do return ctx:exit(1) end -- BATHFURNACE.scr:31
end

script.labels["repeat0"] = function(ctx)
    -- BATHFURNACE.scr:35
    if ctx:condition("nSwitchOpen == 1") then -- BATHFURNACE.scr:38
        ctx:trigger("hPiston0", "toggle") -- BATHFURNACE.scr:39
    end -- BATHFURNACE.scr:40
    do return ctx:exit(1) end -- BATHFURNACE.scr:42
end

script.labels["repeat1"] = function(ctx)
    -- BATHFURNACE.scr:45
    if ctx:condition("nSwitchOpen == 1") then -- BATHFURNACE.scr:48
        ctx:trigger("hPiston1", "toggle") -- BATHFURNACE.scr:49
    end -- BATHFURNACE.scr:50
    do return ctx:exit(1) end -- BATHFURNACE.scr:52
end

script.labels["turnoff"] = function(ctx)
    -- BATHFURNACE.scr:56
    ctx:trigger("hBoilingSteam0", "off") -- BATHFURNACE.scr:59
    ctx:trigger("hBoilingSteam1", "off") -- BATHFURNACE.scr:60
    ctx:trigger("hDamageBrush0", "turnoff") -- BATHFURNACE.scr:61
    ctx:trigger("hDamageBrush1", "turnoff") -- BATHFURNACE.scr:62
    ctx:state().nSwitchOpen = 0 -- BATHFURNACE.scr:63
    do return ctx:exit(1) end -- BATHFURNACE.scr:64
end

script.labels["turnon"] = function(ctx)
    -- BATHFURNACE.scr:67
    ctx:trigger("hBoilingSteam0", "on") -- BATHFURNACE.scr:70
    ctx:trigger("hBoilingSteam1", "on") -- BATHFURNACE.scr:71
    ctx:trigger("hDamageBrush0", "turnon") -- BATHFURNACE.scr:72
    ctx:trigger("hDamageBrush1", "turnon") -- BATHFURNACE.scr:73
    ctx:trigger("hPiston0", "toggle") -- BATHFURNACE.scr:74
    ctx:trigger("hPiston1", "toggle") -- BATHFURNACE.scr:75
    ctx:wait(1, 2, "KillFatc") -- BATHFURNACE.scr:76
    ctx:state().nSwitchOpen = 1 -- BATHFURNACE.scr:77
    do return ctx:exit(1) end -- BATHFURNACE.scr:79
end

script.labels["KillFatc"] = function(ctx)
    -- BATHFURNACE.scr:82
    ctx:object("BigColWinPool2"):trigger("Die") -- BATHFURNACE.scr:85-86
    do return ctx:exit("") end -- BATHFURNACE.scr:88
end

script.labels["main2"] = function(ctx)
    -- BATHFURNACE.scr:91
    ctx:state().hBoilingSteam0 = ctx:objectOrNil("BoilingSteam0") -- BATHFURNACE.scr:94
    ctx:state().hBoilingSteam1 = ctx:objectOrNil("BoilingSteam1") -- BATHFURNACE.scr:95
    ctx:state().hDamageBrush0 = ctx:objectOrNil("PoolDamageBr0") -- BATHFURNACE.scr:96
    ctx:state().hDamageBrush1 = ctx:objectOrNil("PoolDamageBr1") -- BATHFURNACE.scr:97
    ctx:state().hPiston0 = ctx:objectOrNil("PistonDown0") -- BATHFURNACE.scr:98
    ctx:state().hPiston1 = ctx:objectOrNil("PistonDown1") -- BATHFURNACE.scr:99
    do return ctx:exit(1) end -- BATHFURNACE.scr:103
end

script.labels["main"] = function(ctx)
    -- BATHFURNACE.scr:107
    ctx:traceOn() -- BATHFURNACE.scr:110
    ctx:addTrigger("turnon", "turnon") -- BATHFURNACE.scr:112
    ctx:addTrigger("turnoff", "turnoff") -- BATHFURNACE.scr:113
    ctx:addTrigger("repeat0", "repeat0") -- BATHFURNACE.scr:114
    ctx:addTrigger("repeat1", "repeat1") -- BATHFURNACE.scr:115
    ctx:wait(0, .1, "main2") -- BATHFURNACE.scr:116
    do return ctx:exit(1) end -- BATHFURNACE.scr:118
end

return script
