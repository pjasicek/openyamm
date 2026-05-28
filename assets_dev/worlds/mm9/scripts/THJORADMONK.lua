-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THJORADMONK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basedoor.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Monksounds.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "MonkHostility.inc" }

-- ThjoradMonk.scr
-- timmy
-- Monks who walk to pray for bells
-- parameters:
-- p0 = Name of animation to run
-- p1 = name of marker to walk to at prayer timeo
script.labels["Pray"] = function(ctx)
    -- THJORADMONK.scr:24
    if ctx:condition("NPC_ID==NULL") then -- THJORADMONK.scr:27
        ctx:command("attachprop", "MonkHammer.ABC MonkHammer.dtx Hammer g_hobject2") -- THJORADMONK.scr:28
    end -- THJORADMONK.scr:29
    ctx:command("playanim", "stand Pray2") -- THJORADMONK.scr:31
    do return ctx:exit("") end -- THJORADMONK.scr:32
end

script.labels["Pray2"] = function(ctx)
    -- THJORADMONK.scr:37
    ctx:command("loopanim", "Anim_1, 0 Donothing") -- THJORADMONK.scr:39
    do return ctx:exit("") end -- THJORADMONK.scr:40
end

script.labels["OnGoToPray"] = function(ctx)
    -- THJORADMONK.scr:43
    if ctx:condition("NPC_ID==NULL") then -- THJORADMONK.scr:46
        ctx:command("detachprop", "g_hobject2 False") -- THJORADMONK.scr:47
    end -- THJORADMONK.scr:48
    ctx:command("set", "atPrayer, True") -- THJORADMONK.scr:50
    mm9.gosub(script, ctx, "BaseDoorInit") -- THJORADMONK.scr:51
    ctx:command("loopanim", "pray 0 DoNothing") -- THJORADMONK.scr:52
    ctx:command("set", "Anim_1 Pray") -- THJORADMONK.scr:53
    ctx:command("getobjecthandle", "L_Marker g_hobject") -- THJORADMONK.scr:54
    ctx:command("walkto", "g_hobject 8 Pray") -- THJORADMONK.scr:55
    do return ctx:exit("") end -- THJORADMONK.scr:56
end

script.labels["OnDamage"] = function(ctx)
    -- THJORADMONK.scr:59
    ctx:command("set", "AtPrayer, TRUE") -- THJORADMONK.scr:62
    ctx:command("getobjecthandle", "thjorad g_hobject") -- THJORADMONK.scr:63
    ctx:trigger("g_hobject", "TurnOn") -- THJORADMONK.scr:64
    ctx:command("playanim", "stand DoNothing") -- THJORADMONK.scr:65
    mm9.gosub(script, ctx, "BaseInit") -- THJORADMONK.scr:66
    do return ctx:exit("") end -- THJORADMONK.scr:67
end

script.labels["OnUse"] = function(ctx)
    -- THJORADMONK.scr:70
    if ctx:condition("NPC_ID!=NULL") then -- THJORADMONK.scr:73
        if ctx:condition("AtPrayer==0") then -- THJORADMONK.scr:74
            -- Getparam 0 g_hobject
            -- FaceObject g_hobject 200 DoNothing
            ctx:doRude("NPC_ID") -- THJORADMONK.scr:77
            do return ctx:exit("") end -- THJORADMONK.scr:78
        end -- THJORADMONK.scr:79
    end -- THJORADMONK.scr:80
    do return ctx:exit("") end -- THJORADMONK.scr:81
end

script.labels["OnRude"] = function(ctx)
    -- THJORADMONK.scr:84
    ctx:command("getobjecthandle", "Thjorad g_hobject") -- THJORADMONK.scr:87
    ctx:command("faceobject", "g_hobject 180 DoNothing") -- THJORADMONK.scr:88
    do return ctx:exit("") end -- THJORADMONK.scr:89
end

script.labels["OnStuck"] = function(ctx)
    -- THJORADMONK.scr:92
    ctx:command("walkto", "g_hobject 8 Pray") -- THJORADMONK.scr:95
    do return ctx:exit("") end -- THJORADMONK.scr:96
end

script.labels["Init"] = function(ctx)
    -- THJORADMONK.scr:100
    mm9.gosub(script, ctx, "MS_Init") -- THJORADMONK.scr:103
    mm9.gosub(script, ctx, "InitMonkHostility") -- THJORADMONK.scr:104
    mm9.gosub(script, ctx, "Pray") -- THJORADMONK.scr:105
    -- OnDamage OnDamage
    ctx:command("onstuck", "Onstuck") -- THJORADMONK.scr:107
    do return ctx:exit("") end -- THJORADMONK.scr:108
end

script.labels["Main"] = function(ctx)
    -- THJORADMONK.scr:111
    ctx:getParam(0, "Anim_1") -- THJORADMONK.scr:113
    ctx:getParam(1, "L_Marker") -- THJORADMONK.scr:114
    ctx:getParam(2, "NPC_ID") -- THJORADMONK.scr:115
    ctx:addTrigger("GoToPray", "OnGoToPray") -- THJORADMONK.scr:116
    ctx:addTrigger("Use", "Onuse") -- THJORADMONK.scr:117
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- THJORADMONK.scr:118
    ctx:command("onpoststartworld", "Init") -- THJORADMONK.scr:119
    ctx:command("onpostminisaveload", "Init") -- THJORADMONK.scr:120
    ctx:command("onpostsaveload", "Init") -- THJORADMONK.scr:121
    ctx:command("wait", "1 .1 Init") -- THJORADMONK.scr:122
    do return ctx:exit("") end -- THJORADMONK.scr:123
end

return script
