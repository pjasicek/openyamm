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
    ctx:self():remove() -- YF_FALLINGFLOOR.scr:34
    -- Trigger hMe, Destroy
    do return ctx:exit("") end -- YF_FALLINGFLOOR.scr:37
end

script.labels["OnTouchNotify"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:40
    ctx:getParam(0, "hObject") -- YF_FALLINGFLOOR.scr:45
    ctx:state().name = ctx:object("hObject"):name() -- YF_FALLINGFLOOR.scr:47
    if ctx:condition("name==Planks0") then -- YF_FALLINGFLOOR.scr:49
        ctx:onEvent("OnTouchNotify") -- YF_FALLINGFLOOR.scr:50
        mm9.gosub(script, ctx, "StopHere") -- YF_FALLINGFLOOR.scr:51
    end -- YF_FALLINGFLOOR.scr:52
    do return ctx:exit("") end -- YF_FALLINGFLOOR.scr:55
end

script.labels["StopHere"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:58
    -- playsound Sounds\Door\doorslammetal01.wav DoNothing hDummy 400 FALSE 100
    -- RemoveObject hYanmir
    ctx:object("Planks0"):trigger("destroy") -- YF_FALLINGFLOOR.scr:63-64
    ctx:object("Xbeams0"):trigger("destroy") -- YF_FALLINGFLOOR.scr:66-67
    ctx:wait(0, 0.1, "RemoveMe") -- YF_FALLINGFLOOR.scr:69
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:71
end

script.labels["GoAway"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:73
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 1000, "StopHere") -- YF_FALLINGFLOOR.scr:75
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:76
end

script.labels["DelayAction"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:79
    -- Let us go thru world when we fall...
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- YF_FALLINGFLOOR.scr:82
    do return mm9.gotoLabel(script, ctx, "GoAway") end -- YF_FALLINGFLOOR.scr:83
    -- Wait 0, 1, GoAway
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:85
end

script.labels["Main2"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:89
    ctx:state().hYanmir = ctx:objectOrNil("Yanmir0") -- YF_FALLINGFLOOR.scr:92
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("CaveInMarker0"):pos() -- YF_FALLINGFLOOR.scr:93-94
    ctx:addTrigger("Disappear", "DelayAction") -- YF_FALLINGFLOOR.scr:95
    ctx:onEvent("OnTouchNotify", "OnTouchNotify") -- YF_FALLINGFLOOR.scr:96
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:97
end

script.labels["Main"] = function(ctx)
    -- YF_FALLINGFLOOR.scr:99
    ctx:wait(0, .1, "main2") -- YF_FALLINGFLOOR.scr:101
    do return ctx:exit("TRUE") end -- YF_FALLINGFLOOR.scr:102
end

return script
