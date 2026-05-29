-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COFFINRAISE.scr"
script.includes = {}
script.labels = {}


-- CoffinRaise.scr
-- by SJR
-- 11-08-01
-- Purpose:
script.labels["Main"] = function(ctx)
    -- COFFINRAISE.scr:13
    ctx:getParam(0, "sMonsterName") -- COFFINRAISE.scr:15
    ctx:addTrigger("raise", "OnRaise") -- COFFINRAISE.scr:17
    ctx:addTrigger("open", "OnRaise") -- COFFINRAISE.scr:18
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- COFFINRAISE.scr:20
    do return ctx:exit(1) end -- COFFINRAISE.scr:22
end

script.labels["DoNothing"] = function(ctx)
    -- COFFINRAISE.scr:25
end

script.labels["CacheFiles"] = function(ctx)
    -- COFFINRAISE.scr:29
    ctx:cacheSound("Sounds\\Door\\stone_door02.wav") -- COFFINRAISE.scr:31
    do return ctx:exit("") end -- COFFINRAISE.scr:32
end

script.labels["OnRaise"] = function(ctx)
    -- COFFINRAISE.scr:35
    ctx:removeTrigger("raise") -- COFFINRAISE.scr:37
    ctx:removeTrigger("open") -- COFFINRAISE.scr:38
    ctx:self():playAnimation("open", "TriggerMonster") -- COFFINRAISE.scr:40
    ctx:playSound("Sounds\\Door\\stone_door02.wav", "DoNothing", 500, 1000) -- COFFINRAISE.scr:41
    do return ctx:exit(1) end -- COFFINRAISE.scr:43
end

script.labels["TriggerMonster"] = function(ctx)
    -- COFFINRAISE.scr:46
    ctx:state().hMonster = ctx:objectOrNil("sMonsterName") -- COFFINRAISE.scr:48
    if ctx:condition("hMonster!=0") then -- COFFINRAISE.scr:49
        ctx:trigger("hMonster", "Awaken") -- COFFINRAISE.scr:50
    end -- COFFINRAISE.scr:51
    do return ctx:exit(1) end -- COFFINRAISE.scr:53
end

return script
