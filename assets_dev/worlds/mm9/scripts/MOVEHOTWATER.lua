-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MOVEHOTWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- MoveHotWater.scr
-- Karl Drown 10-11-01
-- Super simple "Move My World Object" script.
script.labels["StopHere"] = function(ctx)
    -- MOVEHOTWATER.scr:23
    ctx:command("hmcmarker", "= NULL") -- MOVEHOTWATER.scr:25
    do return ctx:exit("TRUE") end -- MOVEHOTWATER.scr:27
end

script.labels["MoveToMarker"] = function(ctx)
    -- MOVEHOTWATER.scr:30
    ctx:command("getobjecthandle", "sMarker, hMCMarker") -- MOVEHOTWATER.scr:34
    ctx:command("getpos", "hMCMarker, nVarX, nVarY, nVarZ") -- MOVEHOTWATER.scr:36
    ctx:command("movetopos", "nVarX, nVarY, nVarZ, 10, StopHere") -- MOVEHOTWATER.scr:38
    do return ctx:exit("") end -- MOVEHOTWATER.scr:40
end

script.labels["Main"] = function(ctx)
    -- MOVEHOTWATER.scr:45
    ctx:getParam(0, "sMarker") -- MOVEHOTWATER.scr:48
    ctx:addTrigger("MoveMe", "MoveToMarker") -- MOVEHOTWATER.scr:49
    do return ctx:exit("") end -- MOVEHOTWATER.scr:51
end

return script
