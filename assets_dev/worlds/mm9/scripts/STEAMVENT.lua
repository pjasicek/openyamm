-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STEAMVENT.scr"
script.includes = {}
script.labels = {}


-- Steamvent.scr
-- Brett Yagi
-- This script is toggle the steam vents
-- Parameters
-- 0 - Damage Brush Name
-- 1 - amount of seconds the vent stays on
-- 2 - amount of seconds the vent stays off
script.labels["TurnItOff"] = function(ctx)
    -- STEAMVENT.scr:26
    ctx:trigger("hMyHandle", "off") -- STEAMVENT.scr:29
    ctx:trigger("hDamageBrush", "turnoff") -- STEAMVENT.scr:30
    ctx:wait(0, "nOffWait", "TurnItOn") -- STEAMVENT.scr:31
    do return ctx:exit(1) end -- STEAMVENT.scr:34
end

script.labels["TurnItOn"] = function(ctx)
    -- STEAMVENT.scr:37
    ctx:trigger("hMyHandle", "on") -- STEAMVENT.scr:40
    ctx:trigger("hDamageBrush", "turnon") -- STEAMVENT.scr:41
    ctx:wait(0, "nOnWait", "TurnItOff") -- STEAMVENT.scr:42
    do return ctx:exit(1) end -- STEAMVENT.scr:44
end

script.labels["main2"] = function(ctx)
    -- STEAMVENT.scr:48
    ctx:state().hMyHandle = ctx:self() -- STEAMVENT.scr:51
    ctx:state().hDamageBrush = ctx:objectOrNil("sDamageBrush") -- STEAMVENT.scr:52
    mm9.gosub(script, ctx, "TurnItOff") -- STEAMVENT.scr:53
    do return ctx:exit(1) end -- STEAMVENT.scr:56
end

script.labels["main"] = function(ctx)
    -- STEAMVENT.scr:59
    ctx:getParam(0, "sDamageBrush") -- STEAMVENT.scr:62
    ctx:getParam(1, "nOffWait") -- STEAMVENT.scr:63
    ctx:getParam(2, "nOnWait") -- STEAMVENT.scr:64
    ctx:wait(0, .1, "main2") -- STEAMVENT.scr:66
    do return ctx:exit(1) end -- STEAMVENT.scr:68
end

return script
