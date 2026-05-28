-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDDEMON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "range.inc" }

-- WizardDemon.scr
-- 01-01-02
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- WIZARDDEMON.scr:11
    ctx:command("wait", "0, .1, InitWizardDemon") -- WIZARDDEMON.scr:13
    do return ctx:exit(1) end -- WIZARDDEMON.scr:15
end

script.labels["InitWizardDemon"] = function(ctx)
    -- WIZARDDEMON.scr:18
    ctx:command("addenemy", "EvilGrandSorcerer") -- WIZARDDEMON.scr:20
    ctx:command("addenemy", "EvilApprentice") -- WIZARDDEMON.scr:21
    ctx:command("addenemy", "Player") -- WIZARDDEMON.scr:22
    mm9.gosub(script, ctx, "PlaySpawnAnim") -- WIZARDDEMON.scr:24
    ctx:addTrigger("finish", "PlayDeathAnims") -- WIZARDDEMON.scr:26
    do return ctx:exit(1) end -- WIZARDDEMON.scr:28
end

script.labels["PlaySpawnAnim"] = function(ctx)
    -- WIZARDDEMON.scr:31
    ctx:command("playanim", "spawn, PlayAngryAnim") -- WIZARDDEMON.scr:33
    do return ctx:exit(1) end -- WIZARDDEMON.scr:35
end

script.labels["PlayAngryAnim"] = function(ctx)
    -- WIZARDDEMON.scr:38
    ctx:command("playanim", "fidget1, SwitchScript") -- WIZARDDEMON.scr:40
    do return ctx:exit(1) end -- WIZARDDEMON.scr:42
end

script.labels["SwitchScript"] = function(ctx)
    -- WIZARDDEMON.scr:45
    mm9.gosub(script, ctx, "BaseInit") -- WIZARDDEMON.scr:47
    mm9.gosub(script, ctx, "RangeInit") -- WIZARDDEMON.scr:48
    do return ctx:exit(1) end -- WIZARDDEMON.scr:50
end

script.labels["PlayDeathAnims"] = function(ctx)
    -- WIZARDDEMON.scr:53
    ctx:command("stop", "") -- WIZARDDEMON.scr:55
    ctx:command("runscript", "\"WizardDemonDeath.scr\"") -- WIZARDDEMON.scr:57
    do return ctx:exit(1) end -- WIZARDDEMON.scr:59
end

return script
