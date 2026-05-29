-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKACCOUNTANT.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "basewander.inc" }

-- THIS FILE IS NOTHING BUT WALKTO CALLBACKS!
-- these are IN order
-- Trigger, hButtons, UnlockButtons
script.labels["InitHonkAccountant"] = function(ctx)
    -- HONKACCOUNTANT.inc:35
    ctx:state().hChests = ctx:objectOrNil("CollectionChestM") -- HONKACCOUNTANT.inc:37
    -- GetObjectHandle , hButtons
    ctx:atTime(7, 0, "StartTrip", "DoNothing") -- HONKACCOUNTANT.inc:40
    ctx:atTime(19, 0, "StartTrip", "DoNothing") -- HONKACCOUNTANT.inc:41
    ctx:atTime(7, 30, "DoNothing", "DoNothing") -- HONKACCOUNTANT.inc:42
    ctx:atTime(19, 30, "DoNothing", "DoNothing") -- HONKACCOUNTANT.inc:43
    -- gosub BaseWanderInit
    -- gosub BaseWanderStartup
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:47
end

script.labels["AvoidObstacle"] = function(ctx)
    -- HONKACCOUNTANT.inc:50
    if ctx:condition("bTurning == TRUE") then -- HONKACCOUNTANT.inc:52
        do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:53
    end -- HONKACCOUNTANT.inc:54
    -- bTurning = TRUE
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:self():rightDir() -- HONKACCOUNTANT.inc:56
    ctx:set("x", "x * dir") -- HONKACCOUNTANT.inc:57
    ctx:set("z", "z * dir") -- HONKACCOUNTANT.inc:58
    ctx:self():faceDir("x", "y", "z", 0, "DoneAvoiding") -- HONKACCOUNTANT.inc:59
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:60
end

script.labels["DoneAvoiding"] = function(ctx)
    -- HONKACCOUNTANT.inc:63
    ctx:state().bTurning = false -- HONKACCOUNTANT.inc:65
    ctx:set("dir", "dir * -1") -- HONKACCOUNTANT.inc:66
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:67
end

script.labels["StartTrip"] = function(ctx)
    -- HONKACCOUNTANT.inc:69
    ctx:self():stop() -- HONKACCOUNTANT.inc:70
    ctx:onEvent("OnObstacle", "AvoidObstacle") -- HONKACCOUNTANT.inc:71
    mm9.gosub(script, ctx, "BaseWanderStop") -- HONKACCOUNTANT.inc:72
    mm9.gosub(script, ctx, "GoToWaypoint0") -- HONKACCOUNTANT.inc:73
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:74
end

script.labels["GoToWaypoint0"] = function(ctx)
    -- HONKACCOUNTANT.inc:76
    ctx:onEvent("OnStuck", "GoToWaypoint0") -- HONKACCOUNTANT.inc:77
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint0") -- HONKACCOUNTANT.inc:78
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint1") -- HONKACCOUNTANT.inc:79
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:80
end

script.labels["GoToWaypoint1"] = function(ctx)
    -- HONKACCOUNTANT.inc:82
    ctx:onEvent("OnStuck", "GoToWaypoint1") -- HONKACCOUNTANT.inc:83
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint1") -- HONKACCOUNTANT.inc:84
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint2") -- HONKACCOUNTANT.inc:85
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:86
end

script.labels["GoToWaypoint2"] = function(ctx)
    -- HONKACCOUNTANT.inc:88
    ctx:onEvent("OnStuck", "GoToWaypoint2") -- HONKACCOUNTANT.inc:89
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint2") -- HONKACCOUNTANT.inc:90
    if ctx:condition("bReturning==TRUE") then -- HONKACCOUNTANT.inc:91
        ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint3") -- HONKACCOUNTANT.inc:92
    else -- HONKACCOUNTANT.inc:93
        ctx:self():walkTo(ctx:object("hCurDest"), 20, "DoCollect") -- HONKACCOUNTANT.inc:94
    end -- HONKACCOUNTANT.inc:95
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:96
end

script.labels["GoToWaypoint3"] = function(ctx)
    -- HONKACCOUNTANT.inc:98
    ctx:self():setCrouch("FALSE") -- HONKACCOUNTANT.inc:99
    ctx:onEvent("OnStuck", "GoToWaypoint3") -- HONKACCOUNTANT.inc:100
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint3") -- HONKACCOUNTANT.inc:101
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint4") -- HONKACCOUNTANT.inc:102
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:103
end

script.labels["GoToWaypoint4"] = function(ctx)
    -- HONKACCOUNTANT.inc:105
    ctx:onEvent("OnStuck", "GoToWaypoint4") -- HONKACCOUNTANT.inc:106
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint4") -- HONKACCOUNTANT.inc:107
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint5") -- HONKACCOUNTANT.inc:108
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:109
end

script.labels["GoToWaypoint5"] = function(ctx)
    -- HONKACCOUNTANT.inc:111
    ctx:onEvent("OnStuck", "GoToWaypoint5") -- HONKACCOUNTANT.inc:112
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint5") -- HONKACCOUNTANT.inc:113
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint6") -- HONKACCOUNTANT.inc:114
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:115
end

script.labels["GoToWaypoint6"] = function(ctx)
    -- HONKACCOUNTANT.inc:117
    ctx:onEvent("OnStuck", "GoToWaypoint6") -- HONKACCOUNTANT.inc:118
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint6") -- HONKACCOUNTANT.inc:119
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint7") -- HONKACCOUNTANT.inc:120
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:121
end

script.labels["GoToWaypoint7"] = function(ctx)
    -- HONKACCOUNTANT.inc:123
    ctx:onEvent("OnStuck", "GoToWaypoint7") -- HONKACCOUNTANT.inc:124
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint7") -- HONKACCOUNTANT.inc:125
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint8") -- HONKACCOUNTANT.inc:126
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:127
end

script.labels["GoToWaypoint8"] = function(ctx)
    -- HONKACCOUNTANT.inc:129
    ctx:onEvent("OnStuck", "GoToWaypoint8") -- HONKACCOUNTANT.inc:130
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint8") -- HONKACCOUNTANT.inc:131
    ctx:self():walkTo(ctx:object("hCurDest"), 20, "GoToWaypoint9") -- HONKACCOUNTANT.inc:132
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:133
end

script.labels["GoToWaypoint9"] = function(ctx)
    -- HONKACCOUNTANT.inc:135
    -- Trigger hButtons, UnlockDoor
    ctx:onEvent("OnStuck", "GoToWaypoint9") -- HONKACCOUNTANT.inc:137
    ctx:state().hCurDest = ctx:objectOrNil("sWaypoint9") -- HONKACCOUNTANT.inc:138
    if ctx:condition("bReturning==TRUE") then -- HONKACCOUNTANT.inc:139
        ctx:self():walkTo(ctx:object("hCurDest"), 20, "DoNothing") -- HONKACCOUNTANT.inc:140
    else -- HONKACCOUNTANT.inc:141
        ctx:self():walkTo(ctx:object("hCurDest"), 20, "FinishTrip") -- HONKACCOUNTANT.inc:142
    end -- HONKACCOUNTANT.inc:143
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:144
end

script.labels["FinishTrip"] = function(ctx)
    -- HONKACCOUNTANT.inc:146
    ctx:self():stop() -- HONKACCOUNTANT.inc:147
    if ctx:condition("bReturning==FALSE") then -- HONKACCOUNTANT.inc:148
        ctx:state().bReturning = true -- HONKACCOUNTANT.inc:149
    else -- HONKACCOUNTANT.inc:150
        ctx:state().bReturning = false -- HONKACCOUNTANT.inc:151
    end -- HONKACCOUNTANT.inc:152
    mm9.gosub(script, ctx, "ReversePaths") -- HONKACCOUNTANT.inc:153
    mm9.gosub(script, ctx, "GoToWaypoint0") -- HONKACCOUNTANT.inc:154
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:155
end

script.labels["ReversePaths"] = function(ctx)
    -- HONKACCOUNTANT.inc:157
    ctx:set("sTemp", "sWaypoint0") -- HONKACCOUNTANT.inc:158
    ctx:set("sWaypoint0", "sWaypoint9") -- HONKACCOUNTANT.inc:159
    ctx:set("sWaypoint9", "sTemp") -- HONKACCOUNTANT.inc:160
    ctx:set("sTemp", "sWaypoint1") -- HONKACCOUNTANT.inc:162
    ctx:set("sWaypoint1", "sWaypoint8") -- HONKACCOUNTANT.inc:163
    ctx:set("sWaypoint8", "sTemp") -- HONKACCOUNTANT.inc:164
    ctx:set("sTemp", "sWaypoint2") -- HONKACCOUNTANT.inc:166
    ctx:set("sWaypoint2", "sWaypoint7") -- HONKACCOUNTANT.inc:167
    ctx:set("sWaypoint7", "sTemp") -- HONKACCOUNTANT.inc:168
    ctx:set("sTemp", "sWaypoint3") -- HONKACCOUNTANT.inc:170
    ctx:set("sWaypoint3", "sWaypoint6") -- HONKACCOUNTANT.inc:171
    ctx:set("sWaypoint6", "sTemp") -- HONKACCOUNTANT.inc:172
    ctx:set("sTemp", "sWaypoint4") -- HONKACCOUNTANT.inc:174
    ctx:set("sWaypoint4", "sWaypoint5") -- HONKACCOUNTANT.inc:175
    ctx:set("sWaypoint5", "sTemp") -- HONKACCOUNTANT.inc:176
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:178
end

script.labels["DoCollect"] = function(ctx)
    -- HONKACCOUNTANT.inc:180
    ctx:self():stop() -- HONKACCOUNTANT.inc:181
    ctx:self():faceObject(ctx:object("hChests"), 180, "PlayCollectSound") -- HONKACCOUNTANT.inc:182
    ctx:self():setCrouch("TRUE") -- HONKACCOUNTANT.inc:183
    ctx:wait(3, 3, "GoToWaypoint3") -- HONKACCOUNTANT.inc:184
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:185
end

script.labels["PlayCollectSound"] = function(ctx)
    -- HONKACCOUNTANT.inc:187
    ctx:playSound("sounds\\weapons\\knifereload.wav", "DoNothing", "hSound", 500, "FALSE", 100) -- HONKACCOUNTANT.inc:188
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:189
end

return script
