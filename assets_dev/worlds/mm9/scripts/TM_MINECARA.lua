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
    ctx:exitScript() -- TM_MINECARA.scr:27
    do return ctx:exit("TRUE") end -- TM_MINECARA.scr:28
end

script.labels["StopHere"] = function(ctx)
    -- TM_MINECARA.scr:30
    ctx:killSound("hDummy") -- TM_MINECARA.scr:32
    ctx:playSound("Sounds\\Door\\doorslammetal01.wav", "DoNothing", "hDummy", 800, "FALSE", 100) -- TM_MINECARA.scr:33
    ctx:state().hBlocker = nil -- TM_MINECARA.scr:34
    ctx:object("ABMineBoards0"):trigger("Destroy") -- TM_MINECARA.scr:35-36
    ctx:wait(1, .5, "KillScript") -- TM_MINECARA.scr:38
    do return ctx:exit("TRUE") end -- TM_MINECARA.scr:40
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_MINECARA.scr:42
    -- SetFlag hMe, FLAG_GOTHRUWORLD
    ctx:playSoundHandle("Sounds\\Events\\Gears02.wav", "hDummy", 2500, "TRUE", 70) -- TM_MINECARA.scr:47
    ctx:state().hBlocker = ctx:objectOrNil("MCarBlocker1") -- TM_MINECARA.scr:48
    ctx:trigger("hBlocker", "Destroy") -- TM_MINECARA.scr:50
    ctx:state().hMCMarker = ctx:objectOrNil("MCarAMarker0") -- TM_MINECARA.scr:51
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("hMCMarker"):pos() -- TM_MINECARA.scr:53
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 100, "StopHere") -- TM_MINECARA.scr:54
    do return ctx:exit("") end -- TM_MINECARA.scr:55
end

script.labels["Main"] = function(ctx)
    -- TM_MINECARA.scr:57
    ctx:onEvent("OnDamage", "MoveToMarker") -- TM_MINECARA.scr:59
    do return ctx:exit("") end -- TM_MINECARA.scr:60
end

return script
