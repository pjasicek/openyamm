-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "OFFRAILTRIGGER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- OffRailTrigger.scr
-- 1/12/02
-- timmy
-- Sends itself a message when player is not on a rail
-- Parameters
-- P0 The object name of the target
-- P1 the trigger message to send
script.labels["Check"] = function(ctx)
    -- OFFRAILTRIGGER.scr:24
    ctx:command("target", "null") -- OFFRAILTRIGGER.scr:26
    ctx:command("getplayerhandle", "g_hPlayer") -- OFFRAILTRIGGER.scr:28
    ctx:command("getcontainercount", "g_hplayer g_ntemp") -- OFFRAILTRIGGER.scr:29
    if ctx:condition("g_ntemp==0") then -- OFFRAILTRIGGER.scr:30
        ctx:command("target", "g_hplayer") -- OFFRAILTRIGGER.scr:31
        ctx:command("getmyhandle", "g_hmyobject") -- OFFRAILTRIGGER.scr:32
        ctx:trigger("g_hmyobject", "sMessage") -- OFFRAILTRIGGER.scr:33
        do return ctx:exit("") end -- OFFRAILTRIGGER.scr:34
    end -- OFFRAILTRIGGER.scr:35
    -- getmyhandle g_hmyobject
    -- trigger g_hmyobject sMessage2
    ctx:command("wait", "1 .5 Check") -- OFFRAILTRIGGER.scr:39
    do return ctx:exit("") end -- OFFRAILTRIGGER.scr:40
end

script.labels["Main"] = function(ctx)
    -- OFFRAILTRIGGER.scr:43
    -- traceon
    ctx:getParam(0, "sMessage") -- OFFRAILTRIGGER.scr:49
    ctx:getParam(1, "sMessage2") -- OFFRAILTRIGGER.scr:50
    mm9.gosub(script, ctx, "check") -- OFFRAILTRIGGER.scr:51
    do return ctx:exit("") end -- OFFRAILTRIGGER.scr:52
end

return script
