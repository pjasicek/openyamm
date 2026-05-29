-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GOPHER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- Gopher.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
script.labels["OnSpecial"] = function(ctx)
    -- GOPHER.scr:18
    ctx:randomInt(0, 10, "g_nRandom") -- GOPHER.scr:20
    if ctx:condition("g_nRandom < 6") then -- GOPHER.scr:21
        ctx:self():playAnimation("up", "GopherUpDone") -- GOPHER.scr:22
    else -- GOPHER.scr:23
        -- We put the gopher down here so we can peek out
        ctx:self():playAnimation("down", "GopherDownDone") -- GOPHER.scr:25
    end -- GOPHER.scr:26
    ctx:wait(1, 1, "WanderTick") -- GOPHER.scr:28
    do return ctx:exit("") end -- GOPHER.scr:31
end

script.labels["GopherUpDone"] = function(ctx)
    -- GOPHER.scr:34
    ctx:self():playAnimation("down") -- GOPHER.scr:36
    ctx:wait(2, 2, "WanderTick") -- GOPHER.scr:38
    do return ctx:exit("") end -- GOPHER.scr:40
end

script.labels["GopherDownDone"] = function(ctx)
    -- GOPHER.scr:43
    ctx:self():playAnimation("peek") -- GOPHER.scr:45
    ctx:wait(2, 2, "WanderTick") -- GOPHER.scr:47
    do return ctx:exit("") end -- GOPHER.scr:49
end

script.labels["OnSpecialDone"] = function(ctx)
    -- GOPHER.scr:52
    -- Were done just exit
    do return ctx:exit("") end -- GOPHER.scr:56
end

script.labels["Main"] = function(ctx)
    -- GOPHER.scr:59
    -- Set wander distance
    ctx:getParam(1, "g_nDistance") -- GOPHER.scr:63
    if ctx:condition("g_nDistance != 0") then -- GOPHER.scr:65
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- GOPHER.scr:66
    else -- GOPHER.scr:67
        ctx:state().MAX_DIST_FROM_STARTPOINT = 350 -- GOPHER.scr:68
    end -- GOPHER.scr:69
    -- Set how often we idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 10 -- GOPHER.scr:72
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 10 -- GOPHER.scr:75
    ctx:state().g_IdleCheckMax = 10 -- GOPHER.scr:76
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 8 -- GOPHER.scr:79
    mm9.gosub(script, ctx, "WanderInit") -- GOPHER.scr:81
    ctx:addTrigger("SpecialAnim", "OnSpecial") -- GOPHER.scr:83
    do return ctx:exit("") end -- GOPHER.scr:85
end

return script
