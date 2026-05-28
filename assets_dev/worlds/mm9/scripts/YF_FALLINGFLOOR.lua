-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YF_FALLINGFLOOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "flags.inc" }

-- YF_FallingFloor.scr
-- kd 11-2-01
-- Parameters
-- CaveIn Trap: Move large floor chunks to marker below.
script.labels["dn"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:26
    do return ctx:exit(1) end -- YF_FALLINGFLOOR.scr:28
end

script.labels["RemoveMe"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:31
    ctx:command("removeobject", "hMe") -- YF_FALLINGFLOOR.scr:34
    -- Trigger hMe, Destroy
    do return ctx:exit("") end -- YF_FALLINGFLOOR.scr:37
end

script.labels["OnTouchNotify"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:40
    ctx:getParam(0, "hObject") -- YF_FALLINGFLOOR.scr:45
    ctx:command("getobjectname", "hObject,name") -- YF_FALLINGFLOOR.scr:47
    if ctx:condition("name==Planks0") then -- YF_FALLINGFLOOR.scr:49
        ctx:command("ontouchnotify", "") -- YF_FALLINGFLOOR.scr:50
        mm9.gosub(script, ctx, "StopHere") -- YF_FALLINGFLOOR.scr:51
    end -- YF_FALLINGFLOOR.scr:52
    do return ctx:exit("") end -- YF_FALLINGFLOOR.scr:55
end

script.labels["StopHere"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:58
    -- playsound Sounds\Door\doorslammetal01.wav DoNothing hDummy 400 FALSE 100
    -- RemoveObject hYanmir
    ctx:command("getobjecthandle", "Planks0,hObject") -- YF_FALLINGFLOOR.scr:63
    ctx:trigger("hObject", "destroy") -- YF_FALLINGFLOOR.scr:64
    ctx:command("getobjecthandle", "Xbeams0,g_hObject") -- YF_FALLINGFLOOR.scr:66
    ctx:trigger("g_hObject", "destroy") -- YF_FALLINGFLOOR.scr:67
    ctx:command("wait", "0,0.1,RemoveMe") -- YF_FALLINGFLOOR.scr:69
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:71
end

script.labels["GoAway"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:73
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 1000, StopHere") -- YF_FALLINGFLOOR.scr:75
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:76
end

script.labels["DelayAction"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:79
    -- Let us go thru world when we fall...
    ctx:command("setflag", "hMe,FLAG_GOTHRUWORLD") -- YF_FALLINGFLOOR.scr:82
    do return mm9.gotoLabel(script, ctx, "GoAway") end -- YF_FALLINGFLOOR.scr:83
    -- Wait 0, 1, GoAway
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:85
end

script.labels["Main2"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:89
    ctx:command("getmyhandle", "hMe") -- YF_FALLINGFLOOR.scr:91
    ctx:command("getobjecthandle", "Yanmir0, hYanmir") -- YF_FALLINGFLOOR.scr:92
    ctx:command("getobjecthandle", "CaveInMarker0, hMarker") -- YF_FALLINGFLOOR.scr:93
    ctx:command("getpos", "hMarker, nVarX, nVarY, nVarZ") -- YF_FALLINGFLOOR.scr:94
    ctx:addTrigger("Disappear", "DelayAction") -- YF_FALLINGFLOOR.scr:95
    ctx:command("ontouchnotify", "OnTouchNotify") -- YF_FALLINGFLOOR.scr:96
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:97
end

script.labels["Main"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:99
    ctx:command("wait", "0 .1 main2") -- YF_FALLINGFLOOR.scr:101
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:102
end

return script
