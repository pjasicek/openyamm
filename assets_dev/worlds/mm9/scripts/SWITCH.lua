-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SWITCH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- Switch.scr
-- By Timmy
-- handles switch stuff
-- Parameters:
-- p0 Name of target you want triggered
-- p1 Message you want to send to target
script.labels["Onuse"] = function(ctx)
    -- SWITCH.scr:19
    if ctx:condition("bUp==FALSE") then -- SWITCH.scr:22
        ctx:self():playAnimation("up", "DoNothing") -- SWITCH.scr:23
        ctx:state().bUp = true -- SWITCH.scr:24
    else -- SWITCH.scr:25
        ctx:self():playAnimation("Down") -- SWITCH.scr:26
        ctx:state().bUp = false -- SWITCH.scr:27
    end -- SWITCH.scr:28
    ctx:object("sTarget"):trigger("sMessage") -- SWITCH.scr:30-31
    do return ctx:exit("") end -- SWITCH.scr:33
end

script.labels["Main"] = function(ctx)
    -- SWITCH.scr:40
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- SWITCH.scr:44
    ctx:getParam(0, "sTarget") -- SWITCH.scr:45
    ctx:getParam(1, "sMessage") -- SWITCH.scr:46
    do return ctx:exit("") end -- SWITCH.scr:48
end

return script
