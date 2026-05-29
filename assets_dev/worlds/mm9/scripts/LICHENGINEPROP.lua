-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHENGINEPROP.scr"
script.includes = {}
script.labels = {}


-- LichEngineProp
-- by SJR
-- Purpose:have the prop play its
-- anims
script.labels["Main"] = function(ctx)
    -- LICHENGINEPROP.scr:9
    ctx:addTrigger("start", "PowerUp") -- LICHENGINEPROP.scr:11
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:13
end

script.labels["PowerUp"] = function(ctx)
    -- LICHENGINEPROP.scr:16
    ctx:removeTrigger("start") -- LICHENGINEPROP.scr:18
    ctx:self():playAnimation("startup", "Spin") -- LICHENGINEPROP.scr:20
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:22
end

script.labels["Spin"] = function(ctx)
    -- LICHENGINEPROP.scr:25
    ctx:self():loopAnimation("spincycle", 0) -- LICHENGINEPROP.scr:27
    ctx:addTrigger("finish", "PowerDown") -- LICHENGINEPROP.scr:29
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:31
end

script.labels["PowerDown"] = function(ctx)
    -- LICHENGINEPROP.scr:34
    ctx:removeTrigger("finish") -- LICHENGINEPROP.scr:36
    ctx:self():playAnimation("shutdown", "Stop") -- LICHENGINEPROP.scr:38
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:40
end

script.labels["Stop"] = function(ctx)
    -- LICHENGINEPROP.scr:43
    ctx:self():loopAnimation("static_model", 0) -- LICHENGINEPROP.scr:45
    ctx:addTrigger("start", "PowerUp") -- LICHENGINEPROP.scr:47
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:49
end

return script
