-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_MINECARA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Flags.inc" }

-- TM_MineCarA.scr
-- Karl Drown 10-4-01
-- Super simple "Move My World Object" script.
script.labels["KillScript"] = function(ctx)
    -- TM_MINECARA.scr:25
    ctx:command("exitscript", "") -- TM_MINECARA.scr:27
    do return ctx:exit("TRUE") end -- TM_MINECARA.scr:28
end

script.labels["StopHere"] = function(ctx)
    -- TM_MINECARA.scr:30
    ctx:command("killsound", "hDummy") -- TM_MINECARA.scr:32
    ctx:command("playsound", "Sounds\\Door\\doorslammetal01.wav DoNothing hDummy 800 FALSE 100") -- TM_MINECARA.scr:33
    ctx:command("hblocker", "= NULL") -- TM_MINECARA.scr:34
    ctx:command("getobjecthandle", "ABMineBoards0, hBlocker") -- TM_MINECARA.scr:35
    ctx:trigger("hBlocker", "Destroy") -- TM_MINECARA.scr:36
    ctx:command("wait", "1, .5, KillScript") -- TM_MINECARA.scr:38
    do return ctx:exit("TRUE") end -- TM_MINECARA.scr:40
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_MINECARA.scr:42
    ctx:command("getmyhandle", "hMe") -- TM_MINECARA.scr:45
    -- SetFlag hMe, FLAG_GOTHRUWORLD
    ctx:command("playsoundhandle", "Sounds\\Events\\Gears02.wav hDummy 2500 TRUE 70") -- TM_MINECARA.scr:47
    ctx:command("getobjecthandle", "MCarBlocker1, hBlocker") -- TM_MINECARA.scr:48
    ctx:trigger("hBlocker", "Destroy") -- TM_MINECARA.scr:50
    ctx:command("getobjecthandle", "MCarAMarker0, hMCMarker") -- TM_MINECARA.scr:51
    ctx:command("getpos", "hMCMarker, nVarX, nVarY, nVarZ") -- TM_MINECARA.scr:53
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 100, StopHere") -- TM_MINECARA.scr:54
    do return ctx:exit("") end -- TM_MINECARA.scr:55
end

script.labels["Main"] = function(ctx)
    -- TM_MINECARA.scr:57
    ctx:command("ondamage", "MoveToMarker") -- TM_MINECARA.scr:59
    do return ctx:exit("") end -- TM_MINECARA.scr:60
end

return script
