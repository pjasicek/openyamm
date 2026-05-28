-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_BRIDGERESET.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- DarkP_BridgeReset.scr
-- kd
-- 1-14-02
-- Plays animation and then triggers ScriptObject
script.labels["StopHere"] = function(ctx)
    -- DARKP_BRIDGERESET.scr:16
    do return ctx:exit("TRUE") end -- DARKP_BRIDGERESET.scr:18
end

script.labels["TurnSwitchOff"] = function(ctx)
    -- DARKP_BRIDGERESET.scr:21
    ctx:command("removetrigger", "Use") -- DARKP_BRIDGERESET.scr:23
    do return ctx:exit("TRUE") end -- DARKP_BRIDGERESET.scr:24
end

script.labels["TriggerScrObj"] = function(ctx)
    -- DARKP_BRIDGERESET.scr:26
    ctx:trigger("hPuzzleManager", "Reset") -- DARKP_BRIDGERESET.scr:28
    do return ctx:exit("TRUE") end -- DARKP_BRIDGERESET.scr:29
end

script.labels["MoveMe"] = function(ctx)
    -- DARKP_BRIDGERESET.scr:31
    ctx:command("playanim", "fidget1, TriggerScrObj") -- DARKP_BRIDGERESET.scr:34
    ctx:command("playsound", "Sounds\\spells\\EnchantItem.wav DoNothing 500 1000 FALSE 100") -- DARKP_BRIDGERESET.scr:35
    do return ctx:exit("TRUE") end -- DARKP_BRIDGERESET.scr:36
end

script.labels["Main2"] = function(ctx)
    -- DARKP_BRIDGERESET.scr:38
    ctx:command("getobjecthandle", "sPuzzleManager, hPuzzleManager") -- DARKP_BRIDGERESET.scr:40
    ctx:addTrigger("Use", "MoveMe") -- DARKP_BRIDGERESET.scr:41
    ctx:addTrigger("Stop", "TurnSwitchOff") -- DARKP_BRIDGERESET.scr:42
    ctx:command("playanim", "fidget1, StopHere") -- DARKP_BRIDGERESET.scr:44
    do return ctx:exit("TRUE") end -- DARKP_BRIDGERESET.scr:46
end

script.labels["Main"] = function(ctx)
    -- DARKP_BRIDGERESET.scr:48
    ctx:getParam(0, "sPuzzleManager") -- DARKP_BRIDGERESET.scr:50
    ctx:command("wait", "0 .1 main2") -- DARKP_BRIDGERESET.scr:51
    do return ctx:exit("TRUE") end -- DARKP_BRIDGERESET.scr:52
end

return script
