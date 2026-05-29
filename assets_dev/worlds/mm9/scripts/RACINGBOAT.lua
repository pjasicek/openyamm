-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RACINGBOAT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }

-- RacingBoat.scr
-- by SJR
-- 12-12-01
-- Purpose:float towards finish
-- line when damaged. Does not
-- buffer movements, so player
-- can't cheeze it.
script.labels["Main"] = function(ctx)
    -- RACINGBOAT.scr:34
    ctx:getParam(0, "sDestName") -- RACINGBOAT.scr:36
    ctx:getParam(1, "bIsAI") -- RACINGBOAT.scr:37
    ctx:onEvent("OnPostStartWorld", "InitRacingBoat") -- RACINGBOAT.scr:39
    ctx:onEvent("OnPostMiniSaveLoad", "InitRacingBoat") -- RACINGBOAT.scr:40
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:42
end

script.labels["InitRacingBoat"] = function(ctx)
    -- RACINGBOAT.scr:45
    -- wait until game has started
    ctx:addTrigger("on", "TurnOn") -- RACINGBOAT.scr:48
    -- turn it back off when race is over
    ctx:addTrigger("off", "TurnOff") -- RACINGBOAT.scr:50
    ctx:addTrigger("submerge", "Submerge") -- RACINGBOAT.scr:51
    ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:self():pos() -- RACINGBOAT.scr:54
    ctx:state().hDest = ctx:objectOrNil("sDestName") -- RACINGBOAT.scr:55
    if ctx:condition("hDest==0") then -- RACINGBOAT.scr:56
        do return ctx:exit("TRUE") end -- RACINGBOAT.scr:57
    end -- RACINGBOAT.scr:58
    ctx:self():faceObject(ctx:object("hDest"), 0, "DoNothing") -- RACINGBOAT.scr:60
    ctx:getConsoleStrVar("BOAT_JUDGE", "sJudgeName") -- RACINGBOAT.scr:61
    ctx:state().hJudge = ctx:objectOrNil("sJudgeName") -- RACINGBOAT.scr:62
    if ctx:condition("hJudge!=0") then -- RACINGBOAT.scr:63
        ctx:self():link(ctx:object("hJudge")) -- RACINGBOAT.scr:64
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- RACINGBOAT.scr:65
    end -- RACINGBOAT.scr:66
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:68
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- RACINGBOAT.scr:71
    ctx:state().hJudge = nil -- RACINGBOAT.scr:73
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:75
end

script.labels["TurnOn"] = function(ctx)
    -- RACINGBOAT.scr:78
    -- ready for racing action
    ctx:state().nDist = ctx:self():distanceTo(ctx:object("hDest")) -- RACINGBOAT.scr:81
    ctx:set("nDist", "nDist / 10") -- RACINGBOAT.scr:82
    -- if ai turned us on, start moving
    -- if player, wait till they shoot us
    if ctx:condition("bIsAI==TRUE") then -- RACINGBOAT.scr:86
        ctx:set("nTemp", "nDist / 2") -- RACINGBOAT.scr:87
        mm9.gosub(script, ctx, "StartMoveLoop") -- RACINGBOAT.scr:88
    else -- RACINGBOAT.scr:89
        mm9.gosub(script, ctx, "Ready") -- RACINGBOAT.scr:90
    end -- RACINGBOAT.scr:91
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:93
end

script.labels["TurnOff"] = function(ctx)
    -- RACINGBOAT.scr:96
    -- not ready for racing action
    ctx:self():stop() -- RACINGBOAT.scr:99
    -- go back, ready for another race
    ctx:self():setPos("xMe", "yMe", "zMe") -- RACINGBOAT.scr:101
    ctx:onEvent("OnDamage", "DoNothing") -- RACINGBOAT.scr:103
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:105
end

script.labels["MoveForward"] = function(ctx)
    -- RACINGBOAT.scr:108
    -- move in forward direction
    ctx:state().nRemainder = ctx:self():distanceTo(ctx:object("hDest")) -- RACINGBOAT.scr:111
    if ctx:condition("nRemainder<nDist") then -- RACINGBOAT.scr:113
        mm9.gosub(script, ctx, "Arrived") -- RACINGBOAT.scr:114
        do return ctx:exit("TRUE") end -- RACINGBOAT.scr:115
    end -- RACINGBOAT.scr:116
    -- take this off so player doesnt cheeze
    ctx:onEvent("OnDamage", "DoNothing") -- RACINGBOAT.scr:119
    ctx:self():moveDir("dx", 0, "dz", "nDist", "nDist", "Ready") -- RACINGBOAT.scr:120
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:122
end

script.labels["StartMoveLoop"] = function(ctx)
    -- RACINGBOAT.scr:125
    -- move in forward direction
    ctx:state().nRemainder = ctx:self():distanceTo(ctx:object("hDest")) -- RACINGBOAT.scr:128
    if ctx:condition("nRemainder<nDist") then -- RACINGBOAT.scr:129
        mm9.gosub(script, ctx, "Arrived") -- RACINGBOAT.scr:130
        do return ctx:exit("TRUE") end -- RACINGBOAT.scr:131
    else -- RACINGBOAT.scr:132
        ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:self():rotation() -- RACINGBOAT.scr:133
    end -- RACINGBOAT.scr:134
    ctx:randomInt("nTemp", "nDist", "nSpeed") -- RACINGBOAT.scr:136
    ctx:set("nSpeed", "nSpeed / 2") -- RACINGBOAT.scr:137
    ctx:self():moveDir("dx", 0, "dz", "nDist", "nSpeed", "StartMoveLoop") -- RACINGBOAT.scr:138
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:140
end

script.labels["Ready"] = function(ctx)
    -- RACINGBOAT.scr:143
    -- re-setup race
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:self():rotation() -- RACINGBOAT.scr:146
    ctx:onEvent("OnDamage", "MoveForward") -- RACINGBOAT.scr:147
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:149
end

script.labels["Arrived"] = function(ctx)
    -- RACINGBOAT.scr:152
    if ctx:condition("hJudge!=0") then -- RACINGBOAT.scr:154
        if ctx:condition("bIsAI==TRUE") then -- RACINGBOAT.scr:155
            ctx:trigger("hJudge", "CPUArrival") -- RACINGBOAT.scr:156
        else -- RACINGBOAT.scr:157
            ctx:trigger("hJudge", "PlayerArrival") -- RACINGBOAT.scr:158
        end -- RACINGBOAT.scr:159
    end -- RACINGBOAT.scr:160
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:162
end

script.labels["Submerge"] = function(ctx)
    -- RACINGBOAT.scr:165
    ctx:self():stop() -- RACINGBOAT.scr:167
    ctx:onEvent("OnDamage", "DoNothing") -- RACINGBOAT.scr:168
    ctx:self():moveDir(0, -1, 0, 64, 64, "ReturnToStart") -- RACINGBOAT.scr:169
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:171
end

script.labels["ReturnToStart"] = function(ctx)
    -- RACINGBOAT.scr:174
    ctx:set("nTemp", "yMe - 64") -- RACINGBOAT.scr:176
    ctx:self():setPos("xMe", "nTemp", "zMe") -- RACINGBOAT.scr:177
    mm9.gosub(script, ctx, "Surface") -- RACINGBOAT.scr:178
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:180
end

script.labels["Surface"] = function(ctx)
    -- RACINGBOAT.scr:183
    ctx:self():moveDir(0, 1, 0, 64, 64, "TurnOff") -- RACINGBOAT.scr:185
    do return ctx:exit("TRUE") end -- RACINGBOAT.scr:187
end

return script
