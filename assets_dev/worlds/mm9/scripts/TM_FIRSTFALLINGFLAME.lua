-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_FIRSTFALLINGFLAME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }

-- TM_FirstFallingFlame.scr
-- kd
-- 11-6-01
-- Makes the flame fall to the ground.
-- Then starts the barrel exploding sequence.
script.labels["KillMe"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:23
    ctx:command("getmyhandle", "hDummy") -- TM_FIRSTFALLINGFLAME.scr:25
    ctx:command("removeobject", "hDummy") -- TM_FIRSTFALLINGFLAME.scr:26
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGFLAME.scr:27
end

script.labels["TurnMeOff"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:29
    ctx:trigger("hFire", "Off") -- TM_FIRSTFALLINGFLAME.scr:31
    ctx:command("wait", "0, 2, KillMe") -- TM_FIRSTFALLINGFLAME.scr:32
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGFLAME.scr:33
end

script.labels["StartSequence"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:35
    -- hBlocker = NULL
    ctx:command("getobjecthandle", "DustObject17, hFire") -- TM_FIRSTFALLINGFLAME.scr:39
    ctx:trigger("hFire", "On") -- TM_FIRSTFALLINGFLAME.scr:40
    ctx:command("getobjecthandle", "sDummy, hBlocker") -- TM_FIRSTFALLINGFLAME.scr:41
    -- playsound Sounds\Events\steam_burst04.wav DoNothing 500 2000 FALSE 100
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- TM_FIRSTFALLINGFLAME.scr:43
    ctx:command("playsound", "Sounds\\Events\\crate_smash.wav DoNothing 500 2000 FALSE 100") -- TM_FIRSTFALLINGFLAME.scr:44
    ctx:trigger("hBlocker", "Destroy") -- TM_FIRSTFALLINGFLAME.scr:47
    ctx:command("wait", "0, 1, TurnMeOff") -- TM_FIRSTFALLINGFLAME.scr:48
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGFLAME.scr:49
end

script.labels["StopHere"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:51
    ctx:command("playsound", "Sounds\\Events\\steam_burst04.wav DoNothing 100 2000 FALSE 100") -- TM_FIRSTFALLINGFLAME.scr:53
    ctx:command("wait", "0, 2, StartSequence") -- TM_FIRSTFALLINGFLAME.scr:54
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGFLAME.scr:55
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:57
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 250, StopHere") -- TM_FIRSTFALLINGFLAME.scr:59
    do return ctx:exit("") end -- TM_FIRSTFALLINGFLAME.scr:60
end

script.labels["Main2"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:62
    ctx:command("getobjecthandle", "FallingTorchMarker1, hFTMarker") -- TM_FIRSTFALLINGFLAME.scr:64
    ctx:command("getpos", "hFTMarker, nVarX, nVarY, nVarZ") -- TM_FIRSTFALLINGFLAME.scr:65
    ctx:addTrigger("Fall", "MoveToMarker") -- TM_FIRSTFALLINGFLAME.scr:66
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGFLAME.scr:67
end

script.labels["Main"] = function(ctx)
    -- TM_FIRSTFALLINGFLAME.scr:69
    ctx:getParam(0, "sDummy") -- TM_FIRSTFALLINGFLAME.scr:71
    ctx:command("wait", "0 .1 main2") -- TM_FIRSTFALLINGFLAME.scr:72
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGFLAME.scr:73
end

return script
