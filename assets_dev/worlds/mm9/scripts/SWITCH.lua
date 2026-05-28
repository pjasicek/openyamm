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
        ctx:command("playanim", "up DoNothing") -- SWITCH.scr:23
        ctx:command("set", "bUp TRUE") -- SWITCH.scr:24
    else -- SWITCH.scr:25
        ctx:command("playanim", "Down") -- SWITCH.scr:26
        ctx:command("set", "bUp FALSE") -- SWITCH.scr:27
    end -- SWITCH.scr:28
    ctx:command("getobjecthandle", "sTarget g_hobject") -- SWITCH.scr:30
    ctx:trigger("g_hobject", "sMessage") -- SWITCH.scr:31
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
