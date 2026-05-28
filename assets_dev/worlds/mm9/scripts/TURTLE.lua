-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TURTLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- Turtle.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
script.labels["HandleOnAlert"] = function(ctx)
    -- TURTLE.scr:22
    ctx:getParam(0, "hAlertedBy") -- TURTLE.scr:25
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- TURTLE.scr:26
    do return ctx:exit("") end -- TURTLE.scr:28
end

script.labels["TurtleOnDamage"] = function(ctx)
    -- TURTLE.scr:31
    -- Figure out who hit us
    ctx:getParam(0, "hAttacker") -- TURTLE.scr:34
    -- Alert nearby AI
    ctx:command("sendalert", "hAttacker") -- TURTLE.scr:37
    do return ctx:exit("FALSE") end -- TURTLE.scr:39
end

script.labels["InitTurtle"] = function(ctx)
    -- TURTLE.scr:43
    -- Set Rooster wander distance
    ctx:getParam(1, "g_nDistance") -- TURTLE.scr:46
    if ctx:condition("g_nDistance != 0") then -- TURTLE.scr:48
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- TURTLE.scr:49
    else -- TURTLE.scr:50
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 350") -- TURTLE.scr:51
    end -- TURTLE.scr:52
    -- Set how often we stop at an obstacle
    ctx:command("set", "g_nStopAtObstacle, 2") -- TURTLE.scr:55
    -- Set how often we idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 4") -- TURTLE.scr:58
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 7") -- TURTLE.scr:61
    ctx:command("set", "g_IdleCheckMax, 7") -- TURTLE.scr:62
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 0") -- TURTLE.scr:65
    do return ctx:exit("") end -- TURTLE.scr:67
end

script.labels["Main"] = function(ctx)
    -- TURTLE.scr:70
    -- Monitor these callbacks
    ctx:command("ondamage", "TurtleOnDamage") -- TURTLE.scr:74
    -- Setup wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- TURTLE.scr:77
    do return ctx:exit("") end -- TURTLE.scr:79
end

return script
