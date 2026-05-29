-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIR_CAMERA.scr"
script.includes = {}
script.labels = {}


-- Yanmir_Camera.Scr
-- Jeff Leggett
-- 01/06/2002
script.labels["TurnOn"] = function(ctx)
    -- YANMIR_CAMERA.scr:16
    ctx:letterBox(1) -- YANMIR_CAMERA.scr:19
    ctx:state().hYanmir = ctx:objectOrNil("Yanmir0") -- YANMIR_CAMERA.scr:21
    ctx:self():setTarget(ctx:object("hYanmir")) -- YANMIR_CAMERA.scr:23
    ctx:self():link(ctx:object("hYanmir")) -- YANMIR_CAMERA.scr:24
    do return ctx:exit(0) end -- YANMIR_CAMERA.scr:26
end

script.labels["TurnOff"] = function(ctx)
    -- YANMIR_CAMERA.scr:29
    ctx:trigger("hMe", "OFF") -- YANMIR_CAMERA.scr:34
    do return ctx:exit("") end -- YANMIR_CAMERA.scr:36
end

script.labels["OnLinkBroken"] = function(ctx)
    -- YANMIR_CAMERA.scr:39
    ctx:getParam(0, "hTemp") -- YANMIR_CAMERA.scr:42
    if ctx:condition("hTemp==hYanmir") then -- YANMIR_CAMERA.scr:44
        ctx:self():setTarget(nil) -- YANMIR_CAMERA.scr:45
        ctx:state().hYanmir = nil -- YANMIR_CAMERA.scr:46
    end -- YANMIR_CAMERA.scr:47
    ctx:wait(0, 3, "TurnOff") -- YANMIR_CAMERA.scr:49
    do return ctx:exit("") end -- YANMIR_CAMERA.scr:50
end

script.labels["OnTurnOff"] = function(ctx)
    -- YANMIR_CAMERA.scr:54
    ctx:letterBox(0) -- YANMIR_CAMERA.scr:56
    do return ctx:exit(0) end -- YANMIR_CAMERA.scr:58
end

script.labels["Main"] = function(ctx)
    -- YANMIR_CAMERA.scr:61
    ctx:addTrigger("ON", "TurnOn") -- YANMIR_CAMERA.scr:63
    ctx:addTrigger("OFF", "OnTurnOff") -- YANMIR_CAMERA.scr:64
    ctx:onEvent("OnObjectLinkBroken", "OnLinkBroken") -- YANMIR_CAMERA.scr:65
    do return ctx:exit("") end -- YANMIR_CAMERA.scr:67
end

return script
