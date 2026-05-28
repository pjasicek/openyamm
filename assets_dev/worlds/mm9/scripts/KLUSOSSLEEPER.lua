-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "KLUSOSSLEEPER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "flags.inc" }

-- KlusosSleeper.scr
-- by SJR
-- 12-24-01 (yes 24)
-- Purpose:
script.labels["Main"] = function(ctx)
    -- KLUSOSSLEEPER.scr:13
    ctx:command("onpoststartworld", "InitKlusosHidden") -- KLUSOSSLEEPER.scr:15
    ctx:command("onpostminisaveload", "InitKlusosHidden") -- KLUSOSSLEEPER.scr:16
    ctx:command("oncachefiles", "CacheFiles") -- KLUSOSSLEEPER.scr:18
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:20
end

script.labels["CacheFiles"] = function(ctx)
    -- KLUSOSSLEEPER.scr:23
    ctx:command("cachescript", "\"baseMelee.scr\"") -- KLUSOSSLEEPER.scr:25
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:27
end

script.labels["InitKlusosHidden"] = function(ctx)
    -- KLUSOSSLEEPER.scr:30
    ctx:command("getobjecthandle", "Blackheart, hBlackheart") -- KLUSOSSLEEPER.scr:32
    if ctx:condition("hBlackheart!=0") then -- KLUSOSSLEEPER.scr:33
        ctx:command("createobjectlink", "hBlackheart") -- KLUSOSSLEEPER.scr:34
        ctx:command("onobjectlinkbroken", "OnObjectLinkBroken") -- KLUSOSSLEEPER.scr:35
    end -- KLUSOSSLEEPER.scr:36
    ctx:command("ondamage", "OnObjectLinkBroken") -- KLUSOSSLEEPER.scr:38
    ctx:command("loopanim", "sleep, 0") -- KLUSOSSLEEPER.scr:40
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:42
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- KLUSOSSLEEPER.scr:45
    ctx:command("playanim", "\"stand\", DoNothing") -- KLUSOSSLEEPER.scr:47
    ctx:command("hblackheart", "= NULL") -- KLUSOSSLEEPER.scr:49
    ctx:command("runscript", "\"baseMelee.scr\"") -- KLUSOSSLEEPER.scr:51
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:53
end

return script
