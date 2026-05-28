-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IVSARFOLLOWNEW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "basedoor.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "BaseGlobals.inc" }

-- IvsarfollowNew.Scr
-- SJR
-- 10-26-01
-- The Ivsar follows the player to
-- press the "use" key on her...
script.labels["GoEscape"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:31
    ctx:command("runto", "hEscape, 25, Disappear") -- IVSARFOLLOWNEW.scr:33
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:34
end

script.labels["Disappear"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:37
    ctx:command("getmyhandle", "hRadius") -- IVSARFOLLOWNEW.scr:39
    ctx:command("removeobject", "hRadius") -- IVSARFOLLOWNEW.scr:40
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:41
end

script.labels["Stop"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:44
    ctx:command("stop", "") -- IVSARFOLLOWNEW.scr:46
    ctx:command("bavoidingobstacle", "= FALSE") -- IVSARFOLLOWNEW.scr:47
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOWNEW.scr:48
        ctx:command("ontargetbeyonddist", "WALK_RADIUS, StartWalking") -- IVSARFOLLOWNEW.scr:49
    end -- IVSARFOLLOWNEW.scr:50
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:51
end

script.labels["WalkAfterTarget"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:54
    -- cprint WalkAfterTarget
    ctx:command("runto", "g_hTarget, STOP_RADIUS, Stop") -- IVSARFOLLOWNEW.scr:57
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:58
end

script.labels["RunAfterTarget"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:61
    -- cprint RunAfterTarget
    ctx:command("runto", "g_hTarget, WALK_RADIUS, WalkAfterTarget") -- IVSARFOLLOWNEW.scr:64
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:65
end

script.labels["StartWalking"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:68
    ctx:command("ontargetbeyonddist", "RUN_RADIUS, StartRunning") -- IVSARFOLLOWNEW.scr:70
    ctx:command("ontargetwithindist", "0") -- IVSARFOLLOWNEW.scr:71
    mm9.gosub(script, ctx, "WalkAfterTarget") -- IVSARFOLLOWNEW.scr:72
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:73
end

script.labels["StartRunning"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:76
    if ctx:condition("bAvoidingObstacle==TRUE") then -- IVSARFOLLOWNEW.scr:78
        do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:79
    end -- IVSARFOLLOWNEW.scr:80
    ctx:command("ontargetbeyonddist", "0") -- IVSARFOLLOWNEW.scr:82
    ctx:command("ontargetwithindist", "WALK_RADIUS, StartWalking") -- IVSARFOLLOWNEW.scr:83
    mm9.gosub(script, ctx, "RunAfterTarget") -- IVSARFOLLOWNEW.scr:85
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:87
end

script.labels["OnFollowStart"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:90
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOWNEW.scr:92
    ctx:command("g_htarget", "= g_hObject") -- IVSARFOLLOWNEW.scr:93
    ctx:command("aigetdistance", "hWaterfall, distance") -- IVSARFOLLOWNEW.scr:94
    if ctx:condition("distance<radius") then -- IVSARFOLLOWNEW.scr:95
        mm9.gosub(script, ctx, "GoEscape") -- IVSARFOLLOWNEW.scr:96
    end -- IVSARFOLLOWNEW.scr:97
    ctx:command("target", "g_hTarget, FALSE") -- IVSARFOLLOWNEW.scr:98
    ctx:command("onlosttarget", "StopMoving") -- IVSARFOLLOWNEW.scr:100
    ctx:command("faceobject", "g_hTarget, 180, FollowTarget") -- IVSARFOLLOWNEW.scr:102
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:104
end

script.labels["FollowTarget"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:107
    ctx:command("aigetdistance", "g_hTarget, distance") -- IVSARFOLLOWNEW.scr:109
    if ctx:condition("distance > RUN_RADIUS") then -- IVSARFOLLOWNEW.scr:110
        mm9.gosub(script, ctx, "StartRunning") -- IVSARFOLLOWNEW.scr:111
    else -- IVSARFOLLOWNEW.scr:112
        if ctx:condition("distance > WALK_RADIUS") then -- IVSARFOLLOWNEW.scr:113
            mm9.gosub(script, ctx, "StartWalking") -- IVSARFOLLOWNEW.scr:114
        else -- IVSARFOLLOWNEW.scr:115
            mm9.gosub(script, ctx, "Stop") -- IVSARFOLLOWNEW.scr:116
        end -- IVSARFOLLOWNEW.scr:117
    end -- IVSARFOLLOWNEW.scr:118
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:119
end

script.labels["InitIvsar"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:122
    ctx:command("getmyhandle", "g_hMyObject") -- IVSARFOLLOWNEW.scr:124
    ctx:command("getobjecthandle", "MarkerWaterfall, hWaterfall") -- IVSARFOLLOWNEW.scr:125
    ctx:command("getobjecthandle", "MarkerRadius, hRadius") -- IVSARFOLLOWNEW.scr:126
    ctx:command("getobjecthandle", "EscapeMarker, hEscape") -- IVSARFOLLOWNEW.scr:127
    ctx:command("getdistance", "hWaterfall, hRadius, radius") -- IVSARFOLLOWNEW.scr:128
    mm9.gosub(script, ctx, "BaseDoorInit") -- IVSARFOLLOWNEW.scr:129
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:130
end

script.labels["ObstacleAvoided"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:133
    ctx:command("bavoidingobstacle", "= FALSE") -- IVSARFOLLOWNEW.scr:135
    mm9.gosub(script, ctx, "FollowTarget") -- IVSARFOLLOWNEW.scr:136
    ctx:command("onobstacleavoided", "") -- IVSARFOLLOWNEW.scr:137
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:138
end

script.labels["OnAvoidingObstacle"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:141
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOWNEW.scr:143
    ctx:getParam(1, "g_nTemp") -- IVSARFOLLOWNEW.scr:144
    if ctx:condition("g_nTemp > MAX_RUN_ANGLE") then -- IVSARFOLLOWNEW.scr:145
        -- Let's walk around it...
        mm9.gosub(script, ctx, "StartWalking") -- IVSARFOLLOWNEW.scr:147
        ctx:command("onobstacleavoided", "ObstacleAvoided") -- IVSARFOLLOWNEW.scr:148
        ctx:command("bavoidingobstacle", "= TRUE") -- IVSARFOLLOWNEW.scr:149
    end -- IVSARFOLLOWNEW.scr:150
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:151
end

script.labels["FollowInit"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:154
    ctx:command("setidle", "") -- IVSARFOLLOWNEW.scr:156
    ctx:addTrigger("Use", "OnUse") -- IVSARFOLLOWNEW.scr:157
    ctx:command("onavoidingobstacle", "OnAvoidingObstacle") -- IVSARFOLLOWNEW.scr:158
    ctx:command("onstuckdone", "FollowTarget") -- IVSARFOLLOWNEW.scr:159
    ctx:command("wait", "0, .1, InitIvsar") -- IVSARFOLLOWNEW.scr:160
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:161
end

return script
