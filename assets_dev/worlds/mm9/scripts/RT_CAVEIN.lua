-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RT_CAVEIN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Flags.inc" }

-- RT_CaveIn.scr
-- Karl Drown 11-13-01
-- Super simple "Move My World Object" script.
script.labels["StopHere"] = function(ctx)
    -- RT_CAVEIN.scr:28
    ctx:command("getobjecthandle", "sDestFloor, hRock") -- RT_CAVEIN.scr:30
    ctx:command("playsound", "Sounds\\Weapons\\EQHammerImpact.wav DoNothing 500 2000 FALSE 100") -- RT_CAVEIN.scr:31
    ctx:trigger("hRock", "Destroy") -- RT_CAVEIN.scr:32
    do return ctx:exit("TRUE") end -- RT_CAVEIN.scr:34
end

script.labels["MoveToMarker"] = function(ctx)
    -- RT_CAVEIN.scr:36
    ctx:command("getmyhandle", "hMe") -- RT_CAVEIN.scr:38
    ctx:command("setflag", "hMe, FLAG_GOTHRUWORLD") -- RT_CAVEIN.scr:39
    ctx:command("getobjecthandle", "sDestBrush, hRock") -- RT_CAVEIN.scr:40
    ctx:trigger("hRock", "Destroy") -- RT_CAVEIN.scr:41
    -- playsound Sounds\Events\boulderroll.wav DoNothing hDummy 1000 TRUE 100
    ctx:command("getobjecthandle", "sMarker, hMarker") -- RT_CAVEIN.scr:43
    ctx:command("getpos", "hMarker, nVarX, nVarY, nVarZ") -- RT_CAVEIN.scr:44
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 220, StopHere") -- RT_CAVEIN.scr:45
    do return ctx:exit("") end -- RT_CAVEIN.scr:46
end

script.labels["Delay"] = function(ctx)
    -- RT_CAVEIN.scr:48
    ctx:command("wait", "0, nNum, MoveToMarker") -- RT_CAVEIN.scr:50
    do return ctx:exit("TRUE") end -- RT_CAVEIN.scr:52
end

script.labels["Main"] = function(ctx)
    -- RT_CAVEIN.scr:54
    ctx:getParam(0, "sMarker") -- RT_CAVEIN.scr:56
    ctx:getParam(1, "sDestBrush") -- RT_CAVEIN.scr:57
    ctx:getParam(2, "nNum") -- RT_CAVEIN.scr:58
    ctx:getParam(3, "sDestFloor") -- RT_CAVEIN.scr:59
    ctx:addTrigger("Fall", "Delay") -- RT_CAVEIN.scr:60
    do return ctx:exit("") end -- RT_CAVEIN.scr:61
end

return script
