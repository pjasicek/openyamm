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
    ctx:self():runTo(ctx:object("hEscape"), 25, "Disappear") -- IVSARFOLLOWNEW.scr:33
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:34
end

script.labels["Disappear"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:37
    ctx:state().hRadius = ctx:self() -- IVSARFOLLOWNEW.scr:39
    ctx:object("hRadius"):remove() -- IVSARFOLLOWNEW.scr:40
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:41
end

script.labels["Stop"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:44
    ctx:self():stop() -- IVSARFOLLOWNEW.scr:46
    ctx:state().bAvoidingObstacle = false -- IVSARFOLLOWNEW.scr:47
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOWNEW.scr:48
        ctx:onEvent("OnTargetBeyondDist", "WALK_RADIUS", "StartWalking") -- IVSARFOLLOWNEW.scr:49
    end -- IVSARFOLLOWNEW.scr:50
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:51
end

script.labels["WalkAfterTarget"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:54
    -- cprint WalkAfterTarget
    ctx:self():runTo(ctx:object("g_hTarget"), "STOP_RADIUS", "Stop") -- IVSARFOLLOWNEW.scr:57
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:58
end

script.labels["RunAfterTarget"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:61
    -- cprint RunAfterTarget
    ctx:self():runTo(ctx:object("g_hTarget"), "WALK_RADIUS", "WalkAfterTarget") -- IVSARFOLLOWNEW.scr:64
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:65
end

script.labels["StartWalking"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:68
    ctx:onEvent("OnTargetBeyondDist", "RUN_RADIUS", "StartRunning") -- IVSARFOLLOWNEW.scr:70
    ctx:onEvent("OnTargetWithinDist", 0) -- IVSARFOLLOWNEW.scr:71
    mm9.gosub(script, ctx, "WalkAfterTarget") -- IVSARFOLLOWNEW.scr:72
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:73
end

script.labels["StartRunning"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:76
    if ctx:condition("bAvoidingObstacle==TRUE") then -- IVSARFOLLOWNEW.scr:78
        do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:79
    end -- IVSARFOLLOWNEW.scr:80
    ctx:onEvent("OnTargetBeyondDist", 0) -- IVSARFOLLOWNEW.scr:82
    ctx:onEvent("OnTargetWithinDist", "WALK_RADIUS", "StartWalking") -- IVSARFOLLOWNEW.scr:83
    mm9.gosub(script, ctx, "RunAfterTarget") -- IVSARFOLLOWNEW.scr:85
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:87
end

script.labels["OnFollowStart"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:90
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOWNEW.scr:92
    ctx:set("g_hTarget", "g_hObject") -- IVSARFOLLOWNEW.scr:93
    ctx:state().distance = ctx:self():aiDistanceTo(ctx:object("hWaterfall")) -- IVSARFOLLOWNEW.scr:94
    if ctx:condition("distance<radius") then -- IVSARFOLLOWNEW.scr:95
        mm9.gosub(script, ctx, "GoEscape") -- IVSARFOLLOWNEW.scr:96
    end -- IVSARFOLLOWNEW.scr:97
    ctx:self():setTarget(ctx:object("g_hTarget")) -- IVSARFOLLOWNEW.scr:98
    ctx:onEvent("OnLostTarget", "StopMoving") -- IVSARFOLLOWNEW.scr:100
    ctx:self():faceObject(ctx:object("g_hTarget"), 180, "FollowTarget") -- IVSARFOLLOWNEW.scr:102
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:104
end

script.labels["FollowTarget"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:107
    ctx:state().distance = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- IVSARFOLLOWNEW.scr:109
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
    ctx:state().hWaterfall = ctx:objectOrNil("MarkerWaterfall") -- IVSARFOLLOWNEW.scr:125
    ctx:state().hRadius = ctx:objectOrNil("MarkerRadius") -- IVSARFOLLOWNEW.scr:126
    ctx:state().hEscape = ctx:objectOrNil("EscapeMarker") -- IVSARFOLLOWNEW.scr:127
    ctx:state().radius = ctx:object("hWaterfall"):distanceTo(ctx:object("hRadius")) -- IVSARFOLLOWNEW.scr:128
    mm9.gosub(script, ctx, "BaseDoorInit") -- IVSARFOLLOWNEW.scr:129
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:130
end

script.labels["ObstacleAvoided"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:133
    ctx:state().bAvoidingObstacle = false -- IVSARFOLLOWNEW.scr:135
    mm9.gosub(script, ctx, "FollowTarget") -- IVSARFOLLOWNEW.scr:136
    ctx:onEvent("OnObstacleAvoided") -- IVSARFOLLOWNEW.scr:137
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:138
end

script.labels["OnAvoidingObstacle"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:141
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOWNEW.scr:143
    ctx:getParam(1, "g_nTemp") -- IVSARFOLLOWNEW.scr:144
    if ctx:condition("g_nTemp > MAX_RUN_ANGLE") then -- IVSARFOLLOWNEW.scr:145
        -- Let's walk around it...
        mm9.gosub(script, ctx, "StartWalking") -- IVSARFOLLOWNEW.scr:147
        ctx:onEvent("OnObstacleAvoided", "ObstacleAvoided") -- IVSARFOLLOWNEW.scr:148
        ctx:state().bAvoidingObstacle = true -- IVSARFOLLOWNEW.scr:149
    end -- IVSARFOLLOWNEW.scr:150
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:151
end

script.labels["FollowInit"] = function(ctx)
    -- IVSARFOLLOWNEW.scr:154
    ctx:self():setIdle() -- IVSARFOLLOWNEW.scr:156
    ctx:addTrigger("Use", "OnUse") -- IVSARFOLLOWNEW.scr:157
    ctx:onEvent("OnAvoidingObstacle", "OnAvoidingObstacle") -- IVSARFOLLOWNEW.scr:158
    ctx:onEvent("OnStuckDone", "FollowTarget") -- IVSARFOLLOWNEW.scr:159
    ctx:wait(0, .1, "InitIvsar") -- IVSARFOLLOWNEW.scr:160
    do return ctx:exit("TRUE") end -- IVSARFOLLOWNEW.scr:161
end

return script
