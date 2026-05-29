-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "KLUSOSHIDDEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "flags.inc" }

-- KlusosHidden.scr
-- by SJR
-- 12-24-01 (yes 24)
-- Purpose:
script.labels["Main"] = function(ctx)
    -- KLUSOSHIDDEN.scr:14
    ctx:onEvent("OnPostStartWorld", "InitKlusosHidden") -- KLUSOSHIDDEN.scr:16
    ctx:onEvent("OnPostMiniSaveLoad", "InitKlusosHidden") -- KLUSOSHIDDEN.scr:17
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- KLUSOSHIDDEN.scr:18
    do return ctx:exit("TRUE") end -- KLUSOSHIDDEN.scr:20
end

script.labels["CacheFiles"] = function(ctx)
    -- KLUSOSHIDDEN.scr:23
    ctx:cacheScript("baseMelee.scr") -- KLUSOSHIDDEN.scr:25
    do return ctx:exit("TRUE") end -- KLUSOSHIDDEN.scr:27
end

script.labels["InitKlusosHidden"] = function(ctx)
    -- KLUSOSHIDDEN.scr:30
    ctx:state().hBlackheart = ctx:objectOrNil("Blackheart") -- KLUSOSHIDDEN.scr:34
    if ctx:condition("hBlackheart!=0") then -- KLUSOSHIDDEN.scr:35
        ctx:self():link(ctx:object("hBlackheart")) -- KLUSOSHIDDEN.scr:36
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- KLUSOSHIDDEN.scr:37
    end -- KLUSOSHIDDEN.scr:38
    ctx:self():setFlag("FLAG_VISIBLE", false) -- KLUSOSHIDDEN.scr:40
    ctx:self():setFlag("FLAG_SOLID", false) -- KLUSOSHIDDEN.scr:41
    do return ctx:exit("TRUE") end -- KLUSOSHIDDEN.scr:43
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- KLUSOSHIDDEN.scr:46
    ctx:state().hBlackheart = nil -- KLUSOSHIDDEN.scr:48
    ctx:self():setFlag("FLAG_VISIBLE", true) -- KLUSOSHIDDEN.scr:50
    ctx:self():setFlag("FLAG_SOLID", true) -- KLUSOSHIDDEN.scr:51
    ctx:runScript("baseMelee.scr") -- KLUSOSHIDDEN.scr:53
    do return ctx:exit("TRUE") end -- KLUSOSHIDDEN.scr:55
end

return script
