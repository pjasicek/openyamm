-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DAGRELLOLD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "base.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- dagrell.scr
-- John Machin
-- This script uses base.inc and adds
-- functionality for some special animations
-- that this creature has.
-- Initialize crouching bool
-- Frequency Dagrell crouches.  1 = 10% etc
-- Number of times to loop crouch anim
-- same as crouch but for standing
-- This number should be the same (or close to) the animation length for the jump
-- animation.  (This info can be found using ModelEdit...)
script.labels["OnUse"] = function(ctx)
    -- DAGRELLOLD.scr:40
    ctx:getParam(0, "g_hObject") -- DAGRELLOLD.scr:42
    ctx:self():faceObject(ctx:object("g_hObject"), 180) -- DAGRELLOLD.scr:44
    do return ctx:exit("") end -- DAGRELLOLD.scr:46
end

script.labels["DagrellTargetDead"] = function(ctx)
    -- DAGRELLOLD.scr:49
    -- We override this so we can crouch after
    -- killing a player.  We call base first
    ctx:getParam(0, "g_nTemp") -- DAGRELLOLD.scr:53
    ctx:self():setTarget(nil) -- DAGRELLOLD.scr:55
    ctx:state().g_hTarget = nil -- DAGRELLOLD.scr:56
    if ctx:condition("g_nTemp == g_hMyObject") then -- DAGRELLOLD.scr:58
        ctx:self():taunt("DagrellTauntDone") -- DAGRELLOLD.scr:59
    else -- DAGRELLOLD.scr:60
        mm9.gosub(script, ctx, "DagrellCrouch") -- DAGRELLOLD.scr:61
    end -- DAGRELLOLD.scr:62
    do return ctx:exit("TRUE") end -- DAGRELLOLD.scr:64
end

script.labels["DagrellTauntDone"] = function(ctx)
    -- DAGRELLOLD.scr:67
    mm9.gosub(script, ctx, "DagrellCrouch") -- DAGRELLOLD.scr:69
    do return ctx:exit("") end -- DAGRELLOLD.scr:71
end

script.labels["DagrellCrouch"] = function(ctx)
    -- DAGRELLOLD.scr:74
    -- If not standing begin crouch
    if ctx:condition("g_bIsCrouching == FALSE") then -- DAGRELLOLD.scr:77
        ctx:self():playAnimation("returntocrouch") -- DAGRELLOLD.scr:78
    else -- DAGRELLOLD.scr:79
        -- if we are already crouched might as well fidget
        ctx:self():playAnimation("CrouchFidget") -- DAGRELLOLD.scr:81
    end -- DAGRELLOLD.scr:82
    ctx:state().g_bIsCrouching = 1 -- DAGRELLOLD.scr:84
    -- How long are we going to crouch for
    ctx:randomInt("g_nCrouchMin", "g_nCrouchMax", "g_nRandom") -- DAGRELLOLD.scr:87
    ctx:self():loopAnimation("Crouch", "g_nRandom", "DagrellCrouchDone") -- DAGRELLOLD.scr:88
    do return ctx:exit("") end -- DAGRELLOLD.scr:90
end

script.labels["DagrellCrouchDone"] = function(ctx)
    -- DAGRELLOLD.scr:93
    -- Once he is done crouching we should fidget
    ctx:self():playAnimation("CrouchFidget", "DagrellFidgetDone") -- DAGRELLOLD.scr:96
    do return ctx:exit("") end -- DAGRELLOLD.scr:98
end

script.labels["DagrellFidgetDone"] = function(ctx)
    -- DAGRELLOLD.scr:101
    -- Fidget is done so startup ticker again
    mm9.gosub(script, ctx, "DagrellTick") -- DAGRELLOLD.scr:104
    do return ctx:exit("") end -- DAGRELLOLD.scr:106
end

script.labels["DagrellStand"] = function(ctx)
    -- DAGRELLOLD.scr:110
    -- Start standing up.  If we are already standing then start
    -- ticker back up.  We use aware to stand because it is the only
    -- anim that stands smoothly.
    if ctx:condition("g_bIsCrouching == TRUE") then -- DAGRELLOLD.scr:115
        ctx:self():playAnimation("Aware", "DagrellAwareDone") -- DAGRELLOLD.scr:116
        ctx:state().g_bIsCrouching = 0 -- DAGRELLOLD.scr:117
    else -- DAGRELLOLD.scr:118
        mm9.gosub(script, ctx, "DagrellTick") -- DAGRELLOLD.scr:119
    end -- DAGRELLOLD.scr:120
    do return ctx:exit("") end -- DAGRELLOLD.scr:122
end

script.labels["DagrellAwareDone"] = function(ctx)
    -- DAGRELLOLD.scr:125
    -- Ok the aware anim finished we can now complete the standup process
    ctx:self():playAnimation("Stand") -- DAGRELLOLD.scr:128
    -- How long should we stand before starting up ticker?
    ctx:randomInt("g_nStandMin", "g_nStandMax", "g_nRandom") -- DAGRELLOLD.scr:131
    ctx:wait(0, "g_nRandom", "DagrellTick") -- DAGRELLOLD.scr:132
    do return ctx:exit("") end -- DAGRELLOLD.scr:134
end

script.labels["DagrellTick"] = function(ctx)
    -- DAGRELLOLD.scr:136
    -- Heartbeat function.  This gets called to keep things rolling
    ctx:randomInt(0, 10, "g_nRandom") -- DAGRELLOLD.scr:139
    if ctx:condition("g_nRandom <= g_nCrouchFrequency") then -- DAGRELLOLD.scr:140
        mm9.gosub(script, ctx, "DagrellCrouch") -- DAGRELLOLD.scr:141
    else -- DAGRELLOLD.scr:142
        mm9.gosub(script, ctx, "DagrellStand") -- DAGRELLOLD.scr:143
    end -- DAGRELLOLD.scr:144
    do return ctx:exit("") end -- DAGRELLOLD.scr:146
end

script.labels["DagrellFoundPlayer"] = function(ctx)
    -- DAGRELLOLD.scr:149
    -- We override foundplayer to squat before the aware anim
    -- plays.  The aware anim starts from a sitting position.
    if ctx:condition("g_bIsCrouching == FALSE") then -- DAGRELLOLD.scr:153
        mm9.gosub(script, ctx, "BaseGoGetHim") -- DAGRELLOLD.scr:154
    else -- DAGRELLOLD.scr:155
        mm9.gosub(script, ctx, "BaseFoundPlayer") -- DAGRELLOLD.scr:156
    end -- DAGRELLOLD.scr:157
    do return ctx:exit("TRUE") end -- DAGRELLOLD.scr:159
end

script.labels["JumpDone"] = function(ctx)
    -- DAGRELLOLD.scr:162
    mm9.gosub(script, ctx, "BaseGoGetHim") -- DAGRELLOLD.scr:165
    do return ctx:exit("TRUE") end -- DAGRELLOLD.scr:167
end

script.labels["DagrellTargetWithinDist"] = function(ctx)
    -- DAGRELLOLD.scr:170
    -- Jump at him!
    ctx:self():jump("JumpDone") -- DAGRELLOLD.scr:173
    ctx:onEvent("OnTargetBeyondDist", "minJumpDist", "DagrellTargetBeyondDist") -- DAGRELLOLD.scr:175
    do return ctx:exit("TRUE") end -- DAGRELLOLD.scr:177
end

script.labels["DagrellTargetBeyondDist"] = function(ctx)
    -- DAGRELLOLD.scr:180
    ctx:onEvent("OnTargetWithinDist", "minJumpDist", "DagrellTargetWithinDist") -- DAGRELLOLD.scr:183
    do return ctx:exit("TRUE") end -- DAGRELLOLD.scr:185
end

script.labels["Main"] = function(ctx)
    -- DAGRELLOLD.scr:189
    -- This routine is automatically run
    -- at script startup...
    -- JSL--> For now, just do base stuff.... (was getting stuck!)
    mm9.gosub(script, ctx, "InitBase") -- DAGRELLOLD.scr:195
    do return ctx:exit("") end -- DAGRELLOLD.scr:196
    ctx:addTrigger("Use", "OnUse") -- DAGRELLOLD.scr:199
    mm9.gosub(script, ctx, "InitBase") -- DAGRELLOLD.scr:201
    -- Override these base handlers
    ctx:onEvent("OnTargetDead", "DagrellTargetDead") -- DAGRELLOLD.scr:204
    ctx:onEvent("OnFoundPlayer", "DagrellFoundPlayer") -- DAGRELLOLD.scr:205
    -- GetDims g_hMyObject, dimsX, dimsY, dimsZ
    ctx:state().minJumpDist = ctx:self():getStat("JumpVel") -- DAGRELLOLD.scr:208
    ctx:mul("minJumpDist", "jumpTime") -- DAGRELLOLD.scr:210
    -- Take off 20 %
    ctx:mul("minJumpDist", 0.80) -- DAGRELLOLD.scr:213
    ctx:onEvent("OnTargetBeyondDist", "minJumpDist", "DagrellTargetBeyondDist") -- DAGRELLOLD.scr:215
    mm9.gosub(script, ctx, "DagrellTick") -- DAGRELLOLD.scr:218
    do return ctx:exit("") end -- DAGRELLOLD.scr:220
end

return script
