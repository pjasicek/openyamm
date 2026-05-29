-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NIGHTDWELLERS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }

-- NightDwellers.scr
-- by SJR
-- Porpoise:slap this baby on a
-- script object and it will
-- will spawn bugs, bandits,
-- and ghosts only at night...
script.labels["Main"] = function(ctx)
    -- NIGHTDWELLERS.scr:30
    ctx:getParam(0, "sCreatureName") -- NIGHTDWELLERS.scr:32
    ctx:getParam(1, "nQuantity") -- NIGHTDWELLERS.scr:33
    -- start out spawning at 6:00
    ctx:atTime(18, 0, "SpawnCreatures", "SpawnCreatures") -- NIGHTDWELLERS.scr:36
    ctx:atTime(6, 0, "RemoveCreatures", "RemoveCreatures") -- NIGHTDWELLERS.scr:37
    ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:self():pos() -- NIGHTDWELLERS.scr:40
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:42
end

script.labels["SpawnCreatures"] = function(ctx)
    -- NIGHTDWELLERS.scr:45
    -- check player distance, spawn
    -- if far enough away
    if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:49
        if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:51
            -- cprint "NightDwellers.scr retrieved NULL player!"
            do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:53
        end -- NIGHTDWELLERS.scr:54
    end -- NIGHTDWELLERS.scr:55
    ctx:state().nTemp = ctx:player():distanceTo(ctx:self()) -- NIGHTDWELLERS.scr:57
    -- player too close, reschedule
    if ctx:condition("nTemp<1000") then -- NIGHTDWELLERS.scr:60
        mm9.gosub(script, ctx, "RescheduleSpawn") -- NIGHTDWELLERS.scr:61
    else -- NIGHTDWELLERS.scr:62
        ctx:state().hCreature0 = ctx:spawn("xMe", "yMe", "zMe", "sCreatureName") -- NIGHTDWELLERS.scr:63
        ctx:state().hCreature1 = ctx:spawn("xMe", "yMe", "zMe", "sCreatureName") -- NIGHTDWELLERS.scr:64
    end -- NIGHTDWELLERS.scr:65
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:67
end

script.labels["RescheduleSpawn"] = function(ctx)
    -- NIGHTDWELLERS.scr:70
    -- reschedule 15 minutes later
    ctx:getGameTime("SPAWN_DELAY_HOUR", "SPAWN_DELAY_MINS") -- NIGHTDWELLERS.scr:73
    ctx:atTime("SPAWN_DELAY_HOUR", "SPAWN_DELAY_MINS", "SpawnCreatures", "SpawnCreatures") -- NIGHTDWELLERS.scr:75
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:77
end

script.labels["RemoveCreatures"] = function(ctx)
    -- NIGHTDWELLERS.scr:80
    if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:82
        if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:84
            -- cprint "NightDwellers.scr retrieved NULL player!"
            do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:86
        end -- NIGHTDWELLERS.scr:87
    end -- NIGHTDWELLERS.scr:88
    ctx:state().nTemp = ctx:player():distanceTo(ctx:self()) -- NIGHTDWELLERS.scr:90
    -- player too close, reschedule
    if ctx:condition("nTemp<1000") then -- NIGHTDWELLERS.scr:93
        mm9.gosub(script, ctx, "RescheduleSpawn") -- NIGHTDWELLERS.scr:94
    else -- NIGHTDWELLERS.scr:95
        if ctx:condition("hCreature0!=0") then -- NIGHTDWELLERS.scr:96
            ctx:object("hCreature0"):remove() -- NIGHTDWELLERS.scr:97
            ctx:state().hCreature0 = nil -- NIGHTDWELLERS.scr:98
        end -- NIGHTDWELLERS.scr:99
        if ctx:condition("hCreature1!=0") then -- NIGHTDWELLERS.scr:101
            ctx:object("hCreature1"):remove() -- NIGHTDWELLERS.scr:102
            ctx:state().hCreature1 = nil -- NIGHTDWELLERS.scr:103
        end -- NIGHTDWELLERS.scr:104
    end -- NIGHTDWELLERS.scr:105
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:107
end

script.labels["RescheduleDestroy"] = function(ctx)
    -- NIGHTDWELLERS.scr:110
    -- reschedule 15 minutes later
    ctx:getGameTime("REMOVE_DELAY_HOUR", "REMOVE_DELAY_MINS") -- NIGHTDWELLERS.scr:113
    ctx:atTime("REMOVE_DELAY_HOUR", "REMOVE_DELAY_MINS", "RemoveCreatures", "RemoveCreatures") -- NIGHTDWELLERS.scr:115
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:117
end

return script
