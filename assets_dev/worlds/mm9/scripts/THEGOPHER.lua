-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THEGOPHER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- thegopher.scr
-- John Machin
-- Gopher script handles specific anims for gopher
-- Passed in Parameter to get Wander distance
script.labels["OnSpecial"] = function(ctx)
    -- THEGOPHER.scr:18
    ctx:randomInt(0, 10, "g_nRandom") -- THEGOPHER.scr:20
    if ctx:condition("g_nRandom < 6") then -- THEGOPHER.scr:21
        ctx:self():playAnimation("up", "GopherUpDone") -- THEGOPHER.scr:22
    else -- THEGOPHER.scr:23
        -- We put the gopher down here so we can peek out
        ctx:self():playAnimation("down", "GopherDownDone") -- THEGOPHER.scr:25
    end -- THEGOPHER.scr:26
    ctx:wait(0, 2, "WanderTick") -- THEGOPHER.scr:28
    do return ctx:exit("") end -- THEGOPHER.scr:30
end

script.labels["GopherUpDone"] = function(ctx)
    -- THEGOPHER.scr:33
    ctx:wait(0, 2, "WanderTick") -- THEGOPHER.scr:35
    do return ctx:exit("") end -- THEGOPHER.scr:37
end

script.labels["GopherDownDone"] = function(ctx)
    -- THEGOPHER.scr:40
    ctx:wait(0, 4, "GopherPeek") -- THEGOPHER.scr:42
    do return ctx:exit("") end -- THEGOPHER.scr:44
end

script.labels["GopherPeek"] = function(ctx)
    -- THEGOPHER.scr:47
    ctx:self():playAnimation("peek") -- THEGOPHER.scr:49
    do return ctx:exit("") end -- THEGOPHER.scr:51
end

script.labels["OnSpecialDone"] = function(ctx)
    -- THEGOPHER.scr:54
    -- Were done just exit
    do return ctx:exit("") end -- THEGOPHER.scr:58
end

script.labels["InitTheGopher"] = function(ctx)
    -- THEGOPHER.scr:61
    -- Set wander distance
    ctx:getParam(1, "g_nDistance") -- THEGOPHER.scr:64
    if ctx:condition("g_nDistance != 0") then -- THEGOPHER.scr:66
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- THEGOPHER.scr:67
    else -- THEGOPHER.scr:68
        ctx:state().MAX_DIST_FROM_STARTPOINT = 350 -- THEGOPHER.scr:69
    end -- THEGOPHER.scr:70
    -- Set how often we idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 10 -- THEGOPHER.scr:73
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 10 -- THEGOPHER.scr:76
    ctx:state().g_IdleCheckMax = 10 -- THEGOPHER.scr:77
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 7 -- THEGOPHER.scr:80
    do return ctx:exit("") end -- THEGOPHER.scr:82
end

script.labels["Main"] = function(ctx)
    -- THEGOPHER.scr:85
    -- Initialize the gopher
    mm9.gosub(script, ctx, "InitTheGopher") -- THEGOPHER.scr:88
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- THEGOPHER.scr:91
    -- setup these triggers
    ctx:addTrigger("SpecialAnim", "OnSpecial") -- THEGOPHER.scr:94
    do return ctx:exit("") end -- THEGOPHER.scr:96
end

return script
