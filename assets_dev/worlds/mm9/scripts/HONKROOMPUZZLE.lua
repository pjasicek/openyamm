-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKROOMPUZZLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseGlobals.inc" }

-- HonkRoomPuzzle.scr
-- by SJR
-- 10-08-01
-- Purpose:manager for the
-- secret room puzzle
-- -DEDIT NOTES-
-- ScriptParams are:
-- p0 = Name of object
-- to 'use'
script.labels["Main"] = function(ctx)
    -- HONKROOMPUZZLE.scr:22
    ctx:wait(0, .1, "InitHonkRoomPuzzle") -- HONKROOMPUZZLE.scr:24
    do return ctx:exit("TRUE") end -- HONKROOMPUZZLE.scr:25
end

script.labels["InitHonkRoomPuzzle"] = function(ctx)
    -- HONKROOMPUZZLE.scr:28
    ctx:state().hLamp1 = ctx:objectOrNil("Brazier23") -- HONKROOMPUZZLE.scr:30
    ctx:state().hLamp2 = ctx:objectOrNil("Brazier25") -- HONKROOMPUZZLE.scr:31
    ctx:state().hSecretDoor = ctx:objectOrNil("SecretDoor") -- HONKROOMPUZZLE.scr:32
    ctx:addTrigger("On", "TurnOn") -- HONKROOMPUZZLE.scr:34
    ctx:addTrigger("Off", "TurnOff") -- HONKROOMPUZZLE.scr:35
    do return ctx:exit("TRUE") end -- HONKROOMPUZZLE.scr:37
end

script.labels["TurnOn"] = function(ctx)
    -- HONKROOMPUZZLE.scr:40
    ctx:trigger("hLamp1", "On") -- HONKROOMPUZZLE.scr:42
    ctx:trigger("hLamp2", "On") -- HONKROOMPUZZLE.scr:43
    -- Wait 1, 5, OpenSecretDoor
    do return ctx:exit("TRUE") end -- HONKROOMPUZZLE.scr:45
end

script.labels["TurnOff"] = function(ctx)
    -- HONKROOMPUZZLE.scr:48
    ctx:trigger("hLamp1", "Off") -- HONKROOMPUZZLE.scr:50
    ctx:trigger("hLamp2", "Off") -- HONKROOMPUZZLE.scr:51
    ctx:wait(1, 5, "OpenSecretDoor") -- HONKROOMPUZZLE.scr:52
    do return ctx:exit("TRUE") end -- HONKROOMPUZZLE.scr:53
end

script.labels["OpenSecretDoor"] = function(ctx)
    -- HONKROOMPUZZLE.scr:56
    ctx:trigger("hSecretDoor", "Use") -- HONKROOMPUZZLE.scr:58
    do return ctx:exit("TRUE") end -- HONKROOMPUZZLE.scr:59
end

return script
