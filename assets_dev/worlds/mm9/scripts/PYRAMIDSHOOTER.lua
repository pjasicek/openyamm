-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PYRAMIDSHOOTER.scr"
script.includes = {}
script.labels = {}


-- LameScript.scr
-- by SJR
-- Purpose:shoots player. for some
-- reason DEdit shooter
-- doesn't work, hence- script
script.labels["Main"] = function(ctx)
    -- PYRAMIDSHOOTER.scr:13
    ctx:self():setNumberProperty("ShootInterval", 3000) -- PYRAMIDSHOOTER.scr:17
    ctx:addTrigger("shoot", "ShootPlayer") -- PYRAMIDSHOOTER.scr:19
    do return ctx:exit(1) end -- PYRAMIDSHOOTER.scr:21
end

script.labels["ShootPlayer"] = function(ctx)
    -- PYRAMIDSHOOTER.scr:24
    if ctx:condition("hPlayer==0") then -- PYRAMIDSHOOTER.scr:26
        if ctx:condition("hPlayer==0") then -- PYRAMIDSHOOTER.scr:28
            do return ctx:exit(1) end -- PYRAMIDSHOOTER.scr:29
        end -- PYRAMIDSHOOTER.scr:30
    end -- PYRAMIDSHOOTER.scr:31
    ctx:self():faceObject(ctx:player(), 1440, "TurnOn") -- PYRAMIDSHOOTER.scr:33
    do return ctx:exit(1) end -- PYRAMIDSHOOTER.scr:35
end

script.labels["TurnOn"] = function(ctx)
    -- PYRAMIDSHOOTER.scr:38
    ctx:trigger("hMe", "on") -- PYRAMIDSHOOTER.scr:40
    ctx:wait(0, 1, "TurnOff") -- PYRAMIDSHOOTER.scr:41
    do return ctx:exit(1) end -- PYRAMIDSHOOTER.scr:42
end

script.labels["TurnOff"] = function(ctx)
    -- PYRAMIDSHOOTER.scr:45
    ctx:trigger("hMe", "off") -- PYRAMIDSHOOTER.scr:47
    do return ctx:exit(1) end -- PYRAMIDSHOOTER.scr:48
end

return script
