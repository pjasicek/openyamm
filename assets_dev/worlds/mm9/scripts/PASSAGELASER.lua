-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PASSAGELASER.scr"
script.includes = {}
script.labels = {}


-- PassageLaser.scr
-- by SJR
-- 11-06-01
-- Purpose:puzzle reflector
-- mirrors in desert
script.labels["Main"] = function(ctx)
    -- PASSAGELASER.scr:17
    -- OnPostStartWorld InitPassageLaser
    ctx:wait(0, 5, "InitPassageLaser") -- PASSAGELASER.scr:20
    do return ctx:exit(1) end -- PASSAGELASER.scr:22
end

script.labels["InitPassageLaser"] = function(ctx)
    -- PASSAGELASER.scr:25
    ctx:addTrigger("rotate", "Rotate") -- PASSAGELASER.scr:29
    do return ctx:exit(1) end -- PASSAGELASER.scr:31
end

script.labels["Rotate"] = function(ctx)
    -- PASSAGELASER.scr:34
    ctx:getParam(0, "hMirror") -- PASSAGELASER.scr:36
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:object("hMirror"):rotation() -- PASSAGELASER.scr:37
    ctx:self():faceDir("dx", 0, "dz", 720, "Shoot") -- PASSAGELASER.scr:38
    do return ctx:exit(1) end -- PASSAGELASER.scr:40
end

script.labels["Shoot"] = function(ctx)
    -- PASSAGELASER.scr:43
    ctx:trigger("hMe", "shoot") -- PASSAGELASER.scr:45
    ctx:wait(0, .5, "Reset") -- PASSAGELASER.scr:47
    do return ctx:exit(1) end -- PASSAGELASER.scr:49
end

script.labels["Reset"] = function(ctx)
    -- PASSAGELASER.scr:52
    -- have to do this or else the real
    -- facedir wont happen if 0 deg.
    ctx:self():faceDir(0, -1, 0, 720) -- PASSAGELASER.scr:56
    do return ctx:exit(1) end -- PASSAGELASER.scr:58
end

return script
