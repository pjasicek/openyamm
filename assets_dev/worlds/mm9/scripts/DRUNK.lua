-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRUNK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- Drunk.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
script.labels["InitDrunk"] = function(ctx)
    -- DRUNK.scr:18
    -- Set wander distance
    ctx:getParam(1, "g_nDistance") -- DRUNK.scr:21
    if ctx:condition("g_nDistance != 0") then -- DRUNK.scr:23
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- DRUNK.scr:24
    else -- DRUNK.scr:25
        ctx:state().MAX_DIST_FROM_STARTPOINT = 350 -- DRUNK.scr:26
    end -- DRUNK.scr:27
    -- Set how often we idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 0 -- DRUNK.scr:30
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 2 -- DRUNK.scr:33
    ctx:state().g_IdleCheckMax = 2 -- DRUNK.scr:34
    -- Set turn degree min max for more erratic movement
    ctx:state().g_TurnDegreeMin = 60 -- DRUNK.scr:37
    ctx:state().g_TurnDegreeMax = 90 -- DRUNK.scr:38
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 0 -- DRUNK.scr:41
    do return ctx:exit("") end -- DRUNK.scr:43
end

script.labels["Main"] = function(ctx)
    -- DRUNK.scr:46
    -- Init Wandering Behavior
    mm9.gosub(script, ctx, "WanderInit") -- DRUNK.scr:49
    do return ctx:exit("") end -- DRUNK.scr:51
end

return script
