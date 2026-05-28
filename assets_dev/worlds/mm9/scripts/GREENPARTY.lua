-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GREENPARTY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "Globals.inc" }

-- GreenParty.scr
-- Karl
-- 10-15-01
-- Simply kill creatures at level launch.
script.labels["KillThem"] = function(ctx)
    -- GREENPARTY.scr:18
    ctx:command("getobjecthandle", "sDeadGuy, hKillMe") -- GREENPARTY.scr:21
    ctx:command("die", "") -- GREENPARTY.scr:22
end

script.labels["Main"] = function(ctx)
    -- GREENPARTY.scr:25
    ctx:getParam(0, "sDeadGuy") -- GREENPARTY.scr:27
    ctx:command("wait", "0, .1, KillThem") -- GREENPARTY.scr:29
    do return ctx:exit("TRUE") end -- GREENPARTY.scr:30
end

return script
