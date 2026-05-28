-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC9.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- NPC9.scr
-- timmy
-- handles Ketil Strongpick's voice and quest stuff.
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC9.scr:26
    do return ctx:exit("") end -- NPC9.scr:28
    -- removed because it wasn't working correctly.
    if ctx:hasKey(9509) then -- NPC9.scr:32-33
        ctx:command("removetrigger", "use") -- NPC9.scr:34
        ctx:command("walking", "= TRUE") -- NPC9.scr:35
        ctx:command("target", "L_htarget") -- NPC9.scr:36
        ctx:command("l_marker", "= \"Marker0\"") -- NPC9.scr:37
        ctx:command("wait", "1 .5 OnWalkTo") -- NPC9.scr:38
        do return ctx:exit("") end -- NPC9.scr:39
    end -- NPC9.scr:40
    do return ctx:exit("") end -- NPC9.scr:42
end

script.labels["OnWalkTo"] = function(ctx)
    -- NPC9.scr:45
    if ctx:condition("Walking==TRUE") then -- NPC9.scr:48
        ctx:command("ontargetbeyonddist", "256 OnStop") -- NPC9.scr:49
        ctx:command("getobjecthandle", "L_Marker g_hobject") -- NPC9.scr:50
        ctx:command("walkto", "g_hobject 8 OnExit") -- NPC9.scr:51
        do return ctx:exit("") end -- NPC9.scr:52
    end -- NPC9.scr:53
    do return ctx:exit("") end -- NPC9.scr:54
end

script.labels["OnUse"] = function(ctx)
    -- NPC9.scr:57
    ctx:getParam(0, "L_hTarget") -- NPC9.scr:61
    ctx:command("playsound", "sound, Onexit, 100, 240, FALSE, 100") -- NPC9.scr:62
    do return ctx:exit("") end -- NPC9.scr:63
end

script.labels["OnStop"] = function(ctx)
    -- NPC9.scr:66
    if ctx:condition("panic==TRUE") then -- NPC9.scr:68
        do return ctx:exit("") end -- NPC9.scr:69
    end -- NPC9.scr:70
    ctx:command("stop", "") -- NPC9.scr:72
    ctx:command("target", "L_HTarget") -- NPC9.scr:73
    ctx:command("faceobject", "L_HTarget 200 DoNothing") -- NPC9.scr:74
    ctx:command("ontargetwithindist", "256 OnWalkTo") -- NPC9.scr:75
    do return ctx:exit("") end -- NPC9.scr:76
end

script.labels["OnExit"] = function(ctx)
    -- NPC9.scr:79
    ctx:command("stop", "") -- NPC9.scr:81
    ctx:command("panic", "= FALSE") -- NPC9.scr:82
    ctx:command("walking", "= FALSE") -- NPC9.scr:83
    do return ctx:exit("") end -- NPC9.scr:84
end

script.labels["OnRunAway"] = function(ctx)
    -- NPC9.scr:88
    -- finds the closest safe marker
    -- and runs to it
    ctx:command("stop", "") -- NPC9.scr:92
    ctx:command("panic", "= TRUE") -- NPC9.scr:93
    ctx:command("getobjecthandle", "Marker0 g_hobject") -- NPC9.scr:94
    ctx:command("aigetdistance", "g_hobject Marker_Dist1") -- NPC9.scr:95
    ctx:command("getobjecthandle", "Marker1 g_hobject") -- NPC9.scr:96
    ctx:command("aigetdistance", "g_hobject Marker_Dist2") -- NPC9.scr:97
    if ctx:condition("Marker_Dist1<Marker_Dist2") then -- NPC9.scr:99
        ctx:command("getobjecthandle", "Marker0 g_hobject") -- NPC9.scr:100
        ctx:command("runto", "g_hobject 8 OnExit") -- NPC9.scr:101
        do return ctx:exit("") end -- NPC9.scr:102
    else -- NPC9.scr:103
        ctx:command("getobjecthandle", "Marker1 g_hobject") -- NPC9.scr:104
        ctx:command("runto", "g_hobject 8 OnExit") -- NPC9.scr:105
        do return ctx:exit("") end -- NPC9.scr:106
    end -- NPC9.scr:107
    do return ctx:exit("") end -- NPC9.scr:108
end

script.labels["Main"] = function(ctx)
    -- NPC9.scr:111
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sound") -- NPC9.scr:117
    ctx:getParam(1, "Params") -- NPC9.scr:118
    ctx:getParam(2, "g_ntemp") -- NPC9.scr:119
    if ctx:condition("Params!=\"\"") then -- NPC9.scr:120
        if ctx:condition("g_ntemp>0") then -- NPC9.scr:121
            ctx:command("loopanim", "Params, g_ntemp ONExit") -- NPC9.scr:122
        end -- NPC9.scr:123
    end -- NPC9.scr:124
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC9.scr:125
    ctx:addTrigger("Use", "OnUse") -- NPC9.scr:126
    ctx:command("attachprop", "MonkHammer.ABC MonkHammer.dtx RHand1 g_hobject2") -- NPC9.scr:127
    mm9.gosub(script, ctx, "BaseWanderInit") -- NPC9.scr:128
    ctx:command("ondamage", "OnRunAway") -- NPC9.scr:129
    do return ctx:exit("") end -- NPC9.scr:130
end

return script
