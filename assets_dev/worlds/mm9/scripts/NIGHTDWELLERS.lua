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
    ctx:command("@m", "18 : 0 , SpawnCreatures, SpawnCreatures") -- NIGHTDWELLERS.scr:36
    ctx:command("@m", "6 : 0 , RemoveCreatures, RemoveCreatures") -- NIGHTDWELLERS.scr:37
    ctx:command("getmyhandle", "hMe") -- NIGHTDWELLERS.scr:39
    ctx:command("getpos", "hMe, xMe,yMe,zMe") -- NIGHTDWELLERS.scr:40
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:42
end

script.labels["SpawnCreatures"] = function(ctx)
    -- NIGHTDWELLERS.scr:45
    -- check player distance, spawn
    -- if far enough away
    if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:49
        ctx:command("getplayerhandle", "hPlayer") -- NIGHTDWELLERS.scr:50
        if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:51
            -- cprint "NightDwellers.scr retrieved NULL player!"
            do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:53
        end -- NIGHTDWELLERS.scr:54
    end -- NIGHTDWELLERS.scr:55
    ctx:command("getdistance", "hPlayer, hMe, nTemp") -- NIGHTDWELLERS.scr:57
    -- player too close, reschedule
    if ctx:condition("nTemp<1000") then -- NIGHTDWELLERS.scr:60
        mm9.gosub(script, ctx, "RescheduleSpawn") -- NIGHTDWELLERS.scr:61
    else -- NIGHTDWELLERS.scr:62
        ctx:command("spawn", "hCreature0, xMe,yMe,zMe, sCreatureName") -- NIGHTDWELLERS.scr:63
        ctx:command("spawn", "hCreature1, xMe,yMe,zMe, sCreatureName") -- NIGHTDWELLERS.scr:64
    end -- NIGHTDWELLERS.scr:65
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:67
end

script.labels["RescheduleSpawn"] = function(ctx)
    -- NIGHTDWELLERS.scr:70
    -- reschedule 15 minutes later
    ctx:command("getgametime", "SPAWN_DELAY_HOUR, SPAWN_DELAY_MINS") -- NIGHTDWELLERS.scr:73
    ctx:command("@m", "SPAWN_DELAY_HOUR : SPAWN_DELAY_MINS, SpawnCreatures, SpawnCreatures") -- NIGHTDWELLERS.scr:75
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:77
end

script.labels["RemoveCreatures"] = function(ctx)
    -- NIGHTDWELLERS.scr:80
    if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:82
        ctx:command("getplayerhandle", "hPlayer") -- NIGHTDWELLERS.scr:83
        if ctx:condition("hPlayer==0") then -- NIGHTDWELLERS.scr:84
            -- cprint "NightDwellers.scr retrieved NULL player!"
            do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:86
        end -- NIGHTDWELLERS.scr:87
    end -- NIGHTDWELLERS.scr:88
    ctx:command("getdistance", "hPlayer, hMe, nTemp") -- NIGHTDWELLERS.scr:90
    -- player too close, reschedule
    if ctx:condition("nTemp<1000") then -- NIGHTDWELLERS.scr:93
        mm9.gosub(script, ctx, "RescheduleSpawn") -- NIGHTDWELLERS.scr:94
    else -- NIGHTDWELLERS.scr:95
        if ctx:condition("hCreature0!=0") then -- NIGHTDWELLERS.scr:96
            ctx:command("removeobject", "hCreature0") -- NIGHTDWELLERS.scr:97
            ctx:command("hcreature0", "= NULL") -- NIGHTDWELLERS.scr:98
        end -- NIGHTDWELLERS.scr:99
        if ctx:condition("hCreature1!=0") then -- NIGHTDWELLERS.scr:101
            ctx:command("removeobject", "hCreature1") -- NIGHTDWELLERS.scr:102
            ctx:command("hcreature1", "= NULL") -- NIGHTDWELLERS.scr:103
        end -- NIGHTDWELLERS.scr:104
    end -- NIGHTDWELLERS.scr:105
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:107
end

script.labels["RescheduleDestroy"] = function(ctx)
    -- NIGHTDWELLERS.scr:110
    -- reschedule 15 minutes later
    ctx:command("getgametime", "REMOVE_DELAY_HOUR, REMOVE_DELAY_MINS") -- NIGHTDWELLERS.scr:113
    ctx:command("@m", "REMOVE_DELAY_HOUR : REMOVE_DELAY_MINS, RemoveCreatures, RemoveCreatures") -- NIGHTDWELLERS.scr:115
    do return ctx:exit("TRUE") end -- NIGHTDWELLERS.scr:117
end

return script
