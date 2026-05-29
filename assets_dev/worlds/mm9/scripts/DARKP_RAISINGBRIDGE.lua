-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_RAISINGBRIDGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Flags.inc" }

-- DarkP_RaisingBridge.scr
-- kd
-- 11-8-01
-- Moves Bridge Section to markers
-- Trigger activated
script.labels["StopHere"] = function(ctx)
    -- DARKP_RAISINGBRIDGE.scr:24
    ctx:state().hMarker = nil -- DARKP_RAISINGBRIDGE.scr:26
    do return ctx:exit("TRUE") end -- DARKP_RAISINGBRIDGE.scr:27
end

script.labels["DownMarker"] = function(ctx)
    -- DARKP_RAISINGBRIDGE.scr:29
    ctx:state().nDown = 1 -- DARKP_RAISINGBRIDGE.scr:31
    ctx:playSound("Sounds\\Spells\\eshield.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_RAISINGBRIDGE.scr:32
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("sDownMarker"):pos() -- DARKP_RAISINGBRIDGE.scr:33-34
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 180, "StopHere") -- DARKP_RAISINGBRIDGE.scr:35
    do return ctx:exit("TRUE") end -- DARKP_RAISINGBRIDGE.scr:36
end

script.labels["UpMarker"] = function(ctx)
    -- DARKP_RAISINGBRIDGE.scr:38
    ctx:state().nDown = 0 -- DARKP_RAISINGBRIDGE.scr:40
    ctx:playSound("Sounds\\Spells\\eshield.wav", "DoNothing", 500, 1000, "FALSE", 100) -- DARKP_RAISINGBRIDGE.scr:41
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("sTopMarker"):pos() -- DARKP_RAISINGBRIDGE.scr:42-43
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 180, "StopHere") -- DARKP_RAISINGBRIDGE.scr:44
    do return ctx:exit("TRUE") end -- DARKP_RAISINGBRIDGE.scr:45
end

script.labels["MoveMe"] = function(ctx)
    -- DARKP_RAISINGBRIDGE.scr:47
    if ctx:condition("nDown==1") then -- DARKP_RAISINGBRIDGE.scr:49
        mm9.gosub(script, ctx, "UpMarker") -- DARKP_RAISINGBRIDGE.scr:50
    else -- DARKP_RAISINGBRIDGE.scr:51
        mm9.gosub(script, ctx, "DownMarker") -- DARKP_RAISINGBRIDGE.scr:52
    end -- DARKP_RAISINGBRIDGE.scr:53
    do return ctx:exit("") end -- DARKP_RAISINGBRIDGE.scr:54
end

script.labels["Main2"] = function(ctx)
    -- DARKP_RAISINGBRIDGE.scr:57
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- DARKP_RAISINGBRIDGE.scr:60
    ctx:addTrigger("Move", "MoveMe") -- DARKP_RAISINGBRIDGE.scr:61
    do return ctx:exit("TRUE") end -- DARKP_RAISINGBRIDGE.scr:62
end

script.labels["Main"] = function(ctx)
    -- DARKP_RAISINGBRIDGE.scr:64
    ctx:getParam(0, "sTopMarker") -- DARKP_RAISINGBRIDGE.scr:66
    ctx:getParam(1, "sDownMarker") -- DARKP_RAISINGBRIDGE.scr:67
    ctx:getParam(2, "nDown") -- DARKP_RAISINGBRIDGE.scr:68
    ctx:wait(0, .1, "main2") -- DARKP_RAISINGBRIDGE.scr:69
    do return ctx:exit("TRUE") end -- DARKP_RAISINGBRIDGE.scr:70
end

return script
