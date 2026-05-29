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
    ctx:onEvent("OnPostStartWorld", "InitKlusosHidden") -- KLUSOSSLEEPER.scr:15
    ctx:onEvent("OnPostMiniSaveLoad", "InitKlusosHidden") -- KLUSOSSLEEPER.scr:16
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- KLUSOSSLEEPER.scr:18
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:20
end

script.labels["CacheFiles"] = function(ctx)
    -- KLUSOSSLEEPER.scr:23
    ctx:cacheScript("baseMelee.scr") -- KLUSOSSLEEPER.scr:25
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:27
end

script.labels["InitKlusosHidden"] = function(ctx)
    -- KLUSOSSLEEPER.scr:30
    ctx:state().hBlackheart = ctx:objectOrNil("Blackheart") -- KLUSOSSLEEPER.scr:32
    if ctx:condition("hBlackheart!=0") then -- KLUSOSSLEEPER.scr:33
        ctx:self():link(ctx:object("hBlackheart")) -- KLUSOSSLEEPER.scr:34
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- KLUSOSSLEEPER.scr:35
    end -- KLUSOSSLEEPER.scr:36
    ctx:onEvent("OnDamage", "OnObjectLinkBroken") -- KLUSOSSLEEPER.scr:38
    ctx:self():loopAnimation("sleep", 0) -- KLUSOSSLEEPER.scr:40
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:42
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- KLUSOSSLEEPER.scr:45
    ctx:self():playAnimation("stand", "DoNothing") -- KLUSOSSLEEPER.scr:47
    ctx:state().hBlackheart = nil -- KLUSOSSLEEPER.scr:49
    ctx:runScript("baseMelee.scr") -- KLUSOSSLEEPER.scr:51
    do return ctx:exit("TRUE") end -- KLUSOSSLEEPER.scr:53
end

return script
