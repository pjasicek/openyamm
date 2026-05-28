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
    ctx:command("removetrigger", "start") -- LICHENGINEPROP.scr:18
    ctx:command("playanim", "\"startup\", Spin") -- LICHENGINEPROP.scr:20
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:22
end

script.labels["Spin"] = function(ctx)
    -- LICHENGINEPROP.scr:25
    ctx:command("loopanim", "\"spincycle\", 0") -- LICHENGINEPROP.scr:27
    ctx:addTrigger("finish", "PowerDown") -- LICHENGINEPROP.scr:29
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:31
end

script.labels["PowerDown"] = function(ctx)
    -- LICHENGINEPROP.scr:34
    ctx:command("removetrigger", "finish") -- LICHENGINEPROP.scr:36
    ctx:command("playanim", "\"shutdown\", Stop") -- LICHENGINEPROP.scr:38
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:40
end

script.labels["Stop"] = function(ctx)
    -- LICHENGINEPROP.scr:43
    ctx:command("loopanim", "\"static_model\", 0") -- LICHENGINEPROP.scr:45
    ctx:addTrigger("start", "PowerUp") -- LICHENGINEPROP.scr:47
    do return ctx:exit(1) end -- LICHENGINEPROP.scr:49
end

return script
