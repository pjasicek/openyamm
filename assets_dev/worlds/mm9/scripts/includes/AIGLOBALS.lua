-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AIGLOBALS.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- AIGLOBALS.INC
-- Put commonly used AI global variables here....
-- Handle to the current target
-- Updated using OnAttackReady and OnTargetOutOfRange
-- Handle to attacker that damaged us.
-- set to true when we are attacking...
-- Set to true when our attack wait is over....
-- set to true when we've taken damage, or we've attacked player..
-- Last time AI attacked its target...
script.labels["IsTargetMoving"] = function(ctx)
    -- AIGLOBALS.inc:49
    -- Returns TRUE or FALSE in g_bTemp
    ctx:state().g_bTemp = false -- AIGLOBALS.inc:54
    if ctx:condition("g_hTarget==NULL") then -- AIGLOBALS.inc:56
        do return ctx:exit("") end -- AIGLOBALS.inc:57
    end -- AIGLOBALS.inc:58
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:object("g_hTarget"):velocity() -- AIGLOBALS.inc:60
    ctx:state().g_nTemp = ctx:vecMag("g_velX", 0, "g_velZ") -- AIGLOBALS.inc:62
    if ctx:condition("g_nTemp > 20") then -- AIGLOBALS.inc:64
        ctx:state().g_bTemp = true -- AIGLOBALS.inc:65
    end -- AIGLOBALS.inc:66
    do return ctx:exit("") end -- AIGLOBALS.inc:68
end

return script
