-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "FarmAnimal.Inc" }

-- cow.scr
-- John Machin
-- Script for the wandering Cow
-- Used for cow tipping.  Need player coordinates
script.labels["OnUse"] = function(ctx)
    -- COW.scr:27
    if ctx:condition("g_bIsTipping == TRUE") then -- COW.scr:29
        do return ctx:exit("") end -- COW.scr:30
    end -- COW.scr:31
    ctx:state().g_bTemp = ctx:self():getStat("IsDead") -- COW.scr:33
    if ctx:condition("g_bTemp==TRUE") then -- COW.scr:35
        do return ctx:exit("") end -- COW.scr:36
    end -- COW.scr:37
    if ctx:condition("g_bRunningAway==TRUE") then -- COW.scr:39
        do return ctx:exit("") end -- COW.scr:40
    end -- COW.scr:41
    mm9.gosub(script, ctx, "DisableWandering") -- COW.scr:43
    ctx:state().g_bIsTipping = true -- COW.scr:45
    ctx:getParam(0, "g_hUsedBy") -- COW.scr:47
    ctx:state().g_nPlayerX, ctx:state().g_nPlayerY, ctx:state().g_nPlayerZ = ctx:object("g_hUsedBy"):pos() -- COW.scr:48
    -- Gets the angle between the player and the cow
    ctx:getAngleToPos("g_nPlayerX", "g_nPlayerY", "g_nPlayerZ", "g_nAngle") -- COW.scr:51
    -- Angle determines which way cow should fall
    if ctx:condition("g_nAngle >= 0") then -- COW.scr:54
        ctx:self():playAnimation("TipOver1", "OnTipOver1Done") -- COW.scr:55
    else -- COW.scr:56
        ctx:self():playAnimation("TipOver2", "OnTipOver2Done") -- COW.scr:57
    end -- COW.scr:58
    -- Make sure we don't get another wait statement interrupting us
    ctx:wait(0, 0, "DoNothing") -- COW.scr:61
    do return ctx:exit("") end -- COW.scr:63
end

script.labels["OnTipOver1Done"] = function(ctx)
    -- COW.scr:66
    ctx:self():playAnimation("StandUp1", "OnStandUpDone") -- COW.scr:68
    do return ctx:exit("") end -- COW.scr:70
end

script.labels["OnTipOver2Done"] = function(ctx)
    -- COW.scr:73
    ctx:self():playAnimation("StandUp2", "OnStandUpDone") -- COW.scr:75
    do return ctx:exit("") end -- COW.scr:77
end

script.labels["OnStandUpDone"] = function(ctx)
    -- COW.scr:80
    mm9.gosub(script, ctx, "EnableWandering") -- COW.scr:82
    ctx:state().g_bIsTipping = false -- COW.scr:83
    do return ctx:exit("") end -- COW.scr:85
end

script.labels["OnWalk"] = function(ctx)
    -- COW.scr:88
    ctx:self():walk() -- COW.scr:91
    do return ctx:exit("") end -- COW.scr:92
end

script.labels["OnTurnLeft"] = function(ctx)
    -- COW.scr:95
    ctx:self():rotate(0, 1, 0, 90, 180) -- COW.scr:97
    do return ctx:exit("") end -- COW.scr:98
end

script.labels["OnTurnRight"] = function(ctx)
    -- COW.scr:101
    ctx:self():rotate(0, 1, 0, -90, 180) -- COW.scr:103
    do return ctx:exit("") end -- COW.scr:104
end

script.labels["InitCow"] = function(ctx)
    -- COW.scr:107
    do return ctx:exit("") end -- COW.scr:111
end

script.labels["Main"] = function(ctx)
    -- COW.scr:115
    -- Setup the cow
    mm9.gosub(script, ctx, "InitCow") -- COW.scr:118
    -- Setup the following special triggers
    ctx:addTrigger("Use", "OnUse") -- COW.scr:122
    ctx:addTrigger("Walk", "OnWalk") -- COW.scr:123
    ctx:addTrigger("TurnLeft", "OnTurnLeft") -- COW.scr:124
    ctx:addTrigger("TurnRight", "OnTurnRight") -- COW.scr:125
    mm9.gosub(script, ctx, "FarmAnimalInit") -- COW.scr:127
    do return ctx:exit("") end -- COW.scr:129
end

return script
