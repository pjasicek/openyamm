-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THJORADMONKMOD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "MonkHostility.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "Monksounds.inc" }

-- ThjoradMonk.scr
-- timmy
-- Monks who walk to pray for bells
-- parameters:
-- p0 = Name of animation to run
-- p1 = name of marker to walk to at prayer timeo
script.labels["Pray"] = function(ctx)
    -- THJORADMONKMOD.scr:21
    if ctx:condition("NPC_ID==0") then -- THJORADMONKMOD.scr:24
        ctx:command("attachprop", "MonkHammer.ABC MonkHammer.dtx Hammer g_hobject2") -- THJORADMONKMOD.scr:25
    end -- THJORADMONKMOD.scr:26
    ctx:command("playanim", "stand Pray2") -- THJORADMONKMOD.scr:28
    do return ctx:exit("") end -- THJORADMONKMOD.scr:29
end

script.labels["Pray2"] = function(ctx)
    -- THJORADMONKMOD.scr:34
    ctx:command("loopanim", "Anim_1, 0 Donothing") -- THJORADMONKMOD.scr:36
    do return ctx:exit("") end -- THJORADMONKMOD.scr:37
end

script.labels["OnGoToPray"] = function(ctx)
    -- THJORADMONKMOD.scr:40
    if ctx:condition("NPC_ID==0") then -- THJORADMONKMOD.scr:43
        ctx:command("detachprop", "g_hobject2 False") -- THJORADMONKMOD.scr:44
    end -- THJORADMONKMOD.scr:45
    ctx:command("set", "atPrayer, True") -- THJORADMONKMOD.scr:47
    mm9.gosub(script, ctx, "BaseDoorInit") -- THJORADMONKMOD.scr:48
    ctx:command("loopanim", "pray 0 DoNothing") -- THJORADMONKMOD.scr:49
    ctx:command("set", "Anim_1 Pray") -- THJORADMONKMOD.scr:50
    ctx:command("getobjecthandle", "L_Marker g_hobject") -- THJORADMONKMOD.scr:51
    ctx:command("walkto", "g_hobject 8 Pray") -- THJORADMONKMOD.scr:52
    do return ctx:exit("") end -- THJORADMONKMOD.scr:53
end

script.labels["OnTurnedHostile"] = function(ctx)
    -- THJORADMONKMOD.scr:56
    ctx:command("set", "AtPrayer, TRUE") -- THJORADMONKMOD.scr:59
    ctx:command("getobjecthandle", "thjorad g_hobject") -- THJORADMONKMOD.scr:60
    ctx:trigger("g_hobject", "TurnOn") -- THJORADMONKMOD.scr:61
    ctx:command("playanim", "stand DoNothing") -- THJORADMONKMOD.scr:62
    mm9.gosub(script, ctx, "BaseInit") -- THJORADMONKMOD.scr:63
    do return ctx:exit("") end -- THJORADMONKMOD.scr:64
end

script.labels["OnUse"] = function(ctx)
    -- THJORADMONKMOD.scr:67
    if ctx:condition("NPC_ID!=0") then -- THJORADMONKMOD.scr:70
        if ctx:condition("AtPrayer==0") then -- THJORADMONKMOD.scr:71
            ctx:getParam(0, "g_hobject") -- THJORADMONKMOD.scr:72
            ctx:command("faceobject", "g_hobject 200 DoNothing") -- THJORADMONKMOD.scr:73
            ctx:doRude("NPC_ID") -- THJORADMONKMOD.scr:74
            do return ctx:exit("") end -- THJORADMONKMOD.scr:75
        end -- THJORADMONKMOD.scr:76
    end -- THJORADMONKMOD.scr:77
    do return ctx:exit("") end -- THJORADMONKMOD.scr:78
end

script.labels["OnRude"] = function(ctx)
    -- THJORADMONKMOD.scr:81
    ctx:command("getobjecthandle", "Thjorad g_hobject") -- THJORADMONKMOD.scr:84
    ctx:command("faceobject", "g_hobject 180 DoNothing") -- THJORADMONKMOD.scr:85
    do return ctx:exit("") end -- THJORADMONKMOD.scr:86
end

script.labels["OnStuck"] = function(ctx)
    -- THJORADMONKMOD.scr:89
    ctx:command("walkto", "g_hobject 8 Pray") -- THJORADMONKMOD.scr:92
    do return ctx:exit("") end -- THJORADMONKMOD.scr:93
end

script.labels["Main"] = function(ctx)
    -- THJORADMONKMOD.scr:96
    -- TraceON
    ctx:getParam(0, "Anim_1") -- THJORADMONKMOD.scr:100
    ctx:getParam(1, "L_Marker") -- THJORADMONKMOD.scr:101
    ctx:getParam(2, "NPC_ID") -- THJORADMONKMOD.scr:102
    mm9.gosub(script, ctx, "Pray") -- THJORADMONKMOD.scr:103
    ctx:command("onstuck", "Onstuck") -- THJORADMONKMOD.scr:104
    ctx:addTrigger("GoToPray", "OnGoToPray") -- THJORADMONKMOD.scr:105
    ctx:addTrigger("Use", "Onuse") -- THJORADMONKMOD.scr:106
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- THJORADMONKMOD.scr:107
    mm9.gosub(script, ctx, "MS_Init") -- THJORADMONKMOD.scr:108
    ctx:command("wait", "0, 5, InitMonkHostility") -- THJORADMONKMOD.scr:109
    do return ctx:exit("") end -- THJORADMONKMOD.scr:110
end

return script
