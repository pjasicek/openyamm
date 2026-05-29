-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FIREBREATHER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "FireBreather.inc" }

-- FireBreather.inc
-- by SJR
-- Purpose:fire eater at a
-- carnival.
script.labels["Main"] = function(ctx)
    -- FIREBREATHER.scr:10
    ctx:getParam(0, "fire_sShooterName") -- FIREBREATHER.scr:12
    ctx:wait(0, 1, "InitFireBreather") -- FIREBREATHER.scr:14
    ctx:addTrigger("use", "BreatheFire") -- FIREBREATHER.scr:16
    do return ctx:exit("TRUE") end -- FIREBREATHER.scr:18
end

return script
