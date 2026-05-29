-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RT_CRYPTBUTTON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Flags.inc" }

-- RT_CryptButton.scr
-- Karl Drown 11-13-01
-- Super simple "Move My World Object" script.
script.labels["StopHere"] = function(ctx)
    -- RT_CRYPTBUTTON.scr:26
    ctx:playSound("Sounds\\Weapons\\EQHammerImpact.wav", "DoNothing", 500, 2000, "FALSE", 100) -- RT_CRYPTBUTTON.scr:28
    do return ctx:exit("TRUE") end -- RT_CRYPTBUTTON.scr:30
end

script.labels["MoveToMarker"] = function(ctx)
    -- RT_CRYPTBUTTON.scr:32
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- RT_CRYPTBUTTON.scr:35
    ctx:object("sDestBrush"):trigger("Destroy") -- RT_CRYPTBUTTON.scr:36-37
    -- playsound Sounds\Events\boulderroll.wav DoNothing hDummy 1000 TRUE 100
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("sMarker"):pos() -- RT_CRYPTBUTTON.scr:39-40
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 220, "StopHere") -- RT_CRYPTBUTTON.scr:41
    do return ctx:exit("") end -- RT_CRYPTBUTTON.scr:42
end

script.labels["Main"] = function(ctx)
    -- RT_CRYPTBUTTON.scr:44
    ctx:getParam(0, "sMarker") -- RT_CRYPTBUTTON.scr:46
    ctx:getParam(1, "sDestBrush") -- RT_CRYPTBUTTON.scr:47
    ctx:addTrigger("Fall", "MoveToMarker") -- RT_CRYPTBUTTON.scr:48
    do return ctx:exit("") end -- RT_CRYPTBUTTON.scr:49
end

return script
