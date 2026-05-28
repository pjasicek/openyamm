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
    ctx:command("getobjecthandle", "CollectionChestM, hChests") -- HONKACCOUNTANT.inc:37
    -- GetObjectHandle , hButtons
    ctx:command("@m", "7 : 0, StartTrip, DoNothing") -- HONKACCOUNTANT.inc:40
    ctx:command("@m", "19 : 0, StartTrip, DoNothing") -- HONKACCOUNTANT.inc:41
    ctx:command("@m", "7 : 30, DoNothing, DoNothing") -- HONKACCOUNTANT.inc:42
    ctx:command("@m", "19 : 30, DoNothing, DoNothing") -- HONKACCOUNTANT.inc:43
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
    ctx:command("getrightdir", "x,y,z") -- HONKACCOUNTANT.inc:56
    ctx:command("x", "= x * dir") -- HONKACCOUNTANT.inc:57
    ctx:command("z", "= z * dir") -- HONKACCOUNTANT.inc:58
    ctx:command("facedir", "x,y,z, 0, DoneAvoiding") -- HONKACCOUNTANT.inc:59
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:60
end

script.labels["DoneAvoiding"] = function(ctx)
    -- HONKACCOUNTANT.inc:63
    ctx:command("bturning", "= FALSE") -- HONKACCOUNTANT.inc:65
    ctx:command("dir", "= dir * -1") -- HONKACCOUNTANT.inc:66
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:67
end

script.labels["StartTrip"] = function(ctx)
    -- HONKACCOUNTANT.inc:69
    ctx:command("stop", "") -- HONKACCOUNTANT.inc:70
    ctx:command("onobstacle", "AvoidObstacle") -- HONKACCOUNTANT.inc:71
    mm9.gosub(script, ctx, "BaseWanderStop") -- HONKACCOUNTANT.inc:72
    mm9.gosub(script, ctx, "GoToWaypoint0") -- HONKACCOUNTANT.inc:73
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:74
end

script.labels["GoToWaypoint0"] = function(ctx)
    -- HONKACCOUNTANT.inc:76
    ctx:command("onstuck", "GoToWaypoint0") -- HONKACCOUNTANT.inc:77
    ctx:command("getobjecthandle", "sWaypoint0, hCurDest") -- HONKACCOUNTANT.inc:78
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint1") -- HONKACCOUNTANT.inc:79
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:80
end

script.labels["GoToWaypoint1"] = function(ctx)
    -- HONKACCOUNTANT.inc:82
    ctx:command("onstuck", "GoToWaypoint1") -- HONKACCOUNTANT.inc:83
    ctx:command("getobjecthandle", "sWaypoint1, hCurDest") -- HONKACCOUNTANT.inc:84
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint2") -- HONKACCOUNTANT.inc:85
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:86
end

script.labels["GoToWaypoint2"] = function(ctx)
    -- HONKACCOUNTANT.inc:88
    ctx:command("onstuck", "GoToWaypoint2") -- HONKACCOUNTANT.inc:89
    ctx:command("getobjecthandle", "sWaypoint2, hCurDest") -- HONKACCOUNTANT.inc:90
    if ctx:condition("bReturning==TRUE") then -- HONKACCOUNTANT.inc:91
        ctx:command("walkto", "hCurDest, 20, GoToWaypoint3") -- HONKACCOUNTANT.inc:92
    else -- HONKACCOUNTANT.inc:93
        ctx:command("walkto", "hCurDest, 20, DoCollect") -- HONKACCOUNTANT.inc:94
    end -- HONKACCOUNTANT.inc:95
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:96
end

script.labels["GoToWaypoint3"] = function(ctx)
    -- HONKACCOUNTANT.inc:98
    ctx:command("setcrouch", "FALSE") -- HONKACCOUNTANT.inc:99
    ctx:command("onstuck", "GoToWaypoint3") -- HONKACCOUNTANT.inc:100
    ctx:command("getobjecthandle", "sWaypoint3, hCurDest") -- HONKACCOUNTANT.inc:101
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint4") -- HONKACCOUNTANT.inc:102
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:103
end

script.labels["GoToWaypoint4"] = function(ctx)
    -- HONKACCOUNTANT.inc:105
    ctx:command("onstuck", "GoToWaypoint4") -- HONKACCOUNTANT.inc:106
    ctx:command("getobjecthandle", "sWaypoint4, hCurDest") -- HONKACCOUNTANT.inc:107
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint5") -- HONKACCOUNTANT.inc:108
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:109
end

script.labels["GoToWaypoint5"] = function(ctx)
    -- HONKACCOUNTANT.inc:111
    ctx:command("onstuck", "GoToWaypoint5") -- HONKACCOUNTANT.inc:112
    ctx:command("getobjecthandle", "sWaypoint5, hCurDest") -- HONKACCOUNTANT.inc:113
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint6") -- HONKACCOUNTANT.inc:114
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:115
end

script.labels["GoToWaypoint6"] = function(ctx)
    -- HONKACCOUNTANT.inc:117
    ctx:command("onstuck", "GoToWaypoint6") -- HONKACCOUNTANT.inc:118
    ctx:command("getobjecthandle", "sWaypoint6, hCurDest") -- HONKACCOUNTANT.inc:119
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint7") -- HONKACCOUNTANT.inc:120
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:121
end

script.labels["GoToWaypoint7"] = function(ctx)
    -- HONKACCOUNTANT.inc:123
    ctx:command("onstuck", "GoToWaypoint7") -- HONKACCOUNTANT.inc:124
    ctx:command("getobjecthandle", "sWaypoint7, hCurDest") -- HONKACCOUNTANT.inc:125
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint8") -- HONKACCOUNTANT.inc:126
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:127
end

script.labels["GoToWaypoint8"] = function(ctx)
    -- HONKACCOUNTANT.inc:129
    ctx:command("onstuck", "GoToWaypoint8") -- HONKACCOUNTANT.inc:130
    ctx:command("getobjecthandle", "sWaypoint8, hCurDest") -- HONKACCOUNTANT.inc:131
    ctx:command("walkto", "hCurDest, 20, GoToWaypoint9") -- HONKACCOUNTANT.inc:132
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:133
end

script.labels["GoToWaypoint9"] = function(ctx)
    -- HONKACCOUNTANT.inc:135
    -- Trigger hButtons, UnlockDoor
    ctx:command("onstuck", "GoToWaypoint9") -- HONKACCOUNTANT.inc:137
    ctx:command("getobjecthandle", "sWaypoint9, hCurDest") -- HONKACCOUNTANT.inc:138
    if ctx:condition("bReturning==TRUE") then -- HONKACCOUNTANT.inc:139
        ctx:command("walkto", "hCurDest, 20, DoNothing") -- HONKACCOUNTANT.inc:140
    else -- HONKACCOUNTANT.inc:141
        ctx:command("walkto", "hCurDest, 20, FinishTrip") -- HONKACCOUNTANT.inc:142
    end -- HONKACCOUNTANT.inc:143
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:144
end

script.labels["FinishTrip"] = function(ctx)
    -- HONKACCOUNTANT.inc:146
    ctx:command("stop", "") -- HONKACCOUNTANT.inc:147
    if ctx:condition("bReturning==FALSE") then -- HONKACCOUNTANT.inc:148
        ctx:command("breturning", "= TRUE") -- HONKACCOUNTANT.inc:149
    else -- HONKACCOUNTANT.inc:150
        ctx:command("breturning", "= FALSE") -- HONKACCOUNTANT.inc:151
    end -- HONKACCOUNTANT.inc:152
    mm9.gosub(script, ctx, "ReversePaths") -- HONKACCOUNTANT.inc:153
    mm9.gosub(script, ctx, "GoToWaypoint0") -- HONKACCOUNTANT.inc:154
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:155
end

script.labels["ReversePaths"] = function(ctx)
    -- HONKACCOUNTANT.inc:157
    ctx:command("stemp", "= sWaypoint0") -- HONKACCOUNTANT.inc:158
    ctx:command("swaypoint0", "= sWaypoint9") -- HONKACCOUNTANT.inc:159
    ctx:command("swaypoint9", "= sTemp") -- HONKACCOUNTANT.inc:160
    ctx:command("stemp", "= sWaypoint1") -- HONKACCOUNTANT.inc:162
    ctx:command("swaypoint1", "= sWaypoint8") -- HONKACCOUNTANT.inc:163
    ctx:command("swaypoint8", "= sTemp") -- HONKACCOUNTANT.inc:164
    ctx:command("stemp", "= sWaypoint2") -- HONKACCOUNTANT.inc:166
    ctx:command("swaypoint2", "= sWaypoint7") -- HONKACCOUNTANT.inc:167
    ctx:command("swaypoint7", "= sTemp") -- HONKACCOUNTANT.inc:168
    ctx:command("stemp", "= sWaypoint3") -- HONKACCOUNTANT.inc:170
    ctx:command("swaypoint3", "= sWaypoint6") -- HONKACCOUNTANT.inc:171
    ctx:command("swaypoint6", "= sTemp") -- HONKACCOUNTANT.inc:172
    ctx:command("stemp", "= sWaypoint4") -- HONKACCOUNTANT.inc:174
    ctx:command("swaypoint4", "= sWaypoint5") -- HONKACCOUNTANT.inc:175
    ctx:command("swaypoint5", "= sTemp") -- HONKACCOUNTANT.inc:176
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:178
end

script.labels["DoCollect"] = function(ctx)
    -- HONKACCOUNTANT.inc:180
    ctx:command("stop", "") -- HONKACCOUNTANT.inc:181
    ctx:command("faceobject", "hChests, 180, PlayCollectSound") -- HONKACCOUNTANT.inc:182
    ctx:command("setcrouch", "TRUE") -- HONKACCOUNTANT.inc:183
    ctx:command("wait", "3, 3, GoToWaypoint3") -- HONKACCOUNTANT.inc:184
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:185
end

script.labels["PlayCollectSound"] = function(ctx)
    -- HONKACCOUNTANT.inc:187
    ctx:command("playsound", "sounds\\weapons\\knifereload.wav, DoNothing, hSound, 500, FALSE, 100") -- HONKACCOUNTANT.inc:188
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.inc:189
end

return script
