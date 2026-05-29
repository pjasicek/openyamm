-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BLACKHEART.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Blackheart.scr
-- 12/20
-- timmy
-- gives party specific item
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- BLACKHEART.scr:26
    ctx:giveItem(29) -- BLACKHEART.scr:33
    ctx:self():remove() -- BLACKHEART.scr:35
    ctx:giveKey(223) -- BLACKHEART.scr:36
    -- SJR(alarm sound)
    ctx:playSound("sounds\\events\\alarmbell.wav", "DoNothing", 1, 5000, "FALSE", 100) -- BLACKHEART.scr:39
    -- endSJR
    do return ctx:exit("") end -- BLACKHEART.scr:42
end

script.labels["Init"] = function(ctx)
    -- BLACKHEART.scr:47
    if ctx:hasKey(223) then -- BLACKHEART.scr:54-55
        ctx:self():remove() -- BLACKHEART.scr:57
        do return ctx:exit("") end -- BLACKHEART.scr:58
    end -- BLACKHEART.scr:59
    do return ctx:exit("") end -- BLACKHEART.scr:60
end

-- SJR(cache routine)
script.labels["CacheFiles"] = function(ctx)
    -- BLACKHEART.scr:64
    ctx:cacheSound("sounds\\events\\alarmbell.wav") -- BLACKHEART.scr:66
    do return ctx:exit("TRUE") end -- BLACKHEART.scr:68
end

-- endSJR
script.labels["Main"] = function(ctx)
    -- BLACKHEART.scr:72
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- BLACKHEART.scr:77
    -- SJR(cache the sound)
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- BLACKHEART.scr:80
    -- endSJR
    ctx:wait(1, 1, "Init") -- BLACKHEART.scr:83
    do return ctx:exit("") end -- BLACKHEART.scr:85
end

return script
