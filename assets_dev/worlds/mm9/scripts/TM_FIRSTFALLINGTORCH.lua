-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_FIRSTFALLINGTORCH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Flags.inc" }

-- TM_FirstFallingTorch.scr
-- kd
-- 11-6-01
-- Makes the torch fall to the ground.
-- Nothing slick or fancy
script.labels["KillMe"] = function(ctx)
    -- TM_FIRSTFALLINGTORCH.scr:24
    ctx:command("removeobject", "hMe") -- TM_FIRSTFALLINGTORCH.scr:26
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGTORCH.scr:27
end

script.labels["StopHere"] = function(ctx)
    -- TM_FIRSTFALLINGTORCH.scr:29
    -- RemoveTrigger OnDamage
    -- RemoveTrigger KnockedLoose
    ctx:command("wait", "0, 3, KillMe") -- TM_FIRSTFALLINGTORCH.scr:33
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGTORCH.scr:34
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_FIRSTFALLINGTORCH.scr:36
    ctx:command("getmyhandle", "hMe") -- TM_FIRSTFALLINGTORCH.scr:38
    ctx:command("setflag", "hMe, FLAG_GOTHRUWORLD") -- TM_FIRSTFALLINGTORCH.scr:39
    ctx:command("getobjecthandle", "TorchHolder1, hBlocker") -- TM_FIRSTFALLINGTORCH.scr:40
    ctx:trigger("hBlocker", "Destroy") -- TM_FIRSTFALLINGTORCH.scr:41
    ctx:trigger("hFire", "Fall") -- TM_FIRSTFALLINGTORCH.scr:42
    ctx:command("rotate", "0, 0, 1, -90, 90, DoNothing") -- TM_FIRSTFALLINGTORCH.scr:43
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 180, StopHere") -- TM_FIRSTFALLINGTORCH.scr:44
    do return ctx:exit("") end -- TM_FIRSTFALLINGTORCH.scr:45
end

script.labels["ShortDelay"] = function(ctx)
    -- TM_FIRSTFALLINGTORCH.scr:47
    ctx:command("wait", "0, .6, MoveToMarker") -- TM_FIRSTFALLINGTORCH.scr:49
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGTORCH.scr:50
end

script.labels["Main2"] = function(ctx)
    -- TM_FIRSTFALLINGTORCH.scr:52
    ctx:command("getobjecthandle", "FallingTorchFire1, hFire") -- TM_FIRSTFALLINGTORCH.scr:54
    ctx:command("getobjecthandle", "FallingTorchMarker1, hFTMarker") -- TM_FIRSTFALLINGTORCH.scr:55
    ctx:command("getpos", "hFTMarker, nVarX, nVarY, nVarZ") -- TM_FIRSTFALLINGTORCH.scr:56
    ctx:addTrigger("KnockedLoose", "ShortDelay") -- TM_FIRSTFALLINGTORCH.scr:57
    ctx:command("ondamage", "MoveToMarker") -- TM_FIRSTFALLINGTORCH.scr:58
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGTORCH.scr:59
end

script.labels["Main"] = function(ctx)
    -- TM_FIRSTFALLINGTORCH.scr:61
    ctx:command("wait", "0 .1 main2") -- TM_FIRSTFALLINGTORCH.scr:63
    do return ctx:exit("TRUE") end -- TM_FIRSTFALLINGTORCH.scr:64
end

return script
