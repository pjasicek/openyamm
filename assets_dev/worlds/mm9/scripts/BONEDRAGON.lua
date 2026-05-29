-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BONEDRAGON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "ListMaker.inc" }

-- BoneDragon.scr
-- by SJR
-- 11-06-01
-- Purpose:build and animate a dragon-shaped
-- creature, made entirely out of
-- Skeletons.
script.labels["Main"] = function(ctx)
    -- BONEDRAGON.scr:20
    ctx:getParam(0, "LISTNAME") -- BONEDRAGON.scr:22
    ctx:getParam(1, "LISTFIRST") -- BONEDRAGON.scr:23
    ctx:getParam(2, "LISTLAST") -- BONEDRAGON.scr:24
    ctx:wait(0, 1, "InitBoneDragon") -- BONEDRAGON.scr:26
    do return ctx:exit("TRUE") end -- BONEDRAGON.scr:28
end

script.labels["InitBoneDragon"] = function(ctx)
    -- BONEDRAGON.scr:31
    do return ctx:exit("TRUE") end -- BONEDRAGON.scr:34
end

return script
