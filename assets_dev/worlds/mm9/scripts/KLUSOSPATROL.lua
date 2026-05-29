-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "KLUSOSPATROL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "ListTraverse.inc" }

-- KlusosPatrol.scr
-- by SJR
-- 12-24-01 (yes 24)
-- Purpose:walk around KlusosHouse
-- guarding stuff
script.labels["Main"] = function(ctx)
    -- KLUSOSPATROL.scr:17
    ctx:getParam(0, "LISTNAME") -- KLUSOSPATROL.scr:19
    ctx:getParam(1, "LISTFIRST") -- KLUSOSPATROL.scr:20
    ctx:getParam(2, "LISTLAST") -- KLUSOSPATROL.scr:21
    ctx:getParam(3, "sBuddyName") -- KLUSOSPATROL.scr:22
    ctx:onEvent("OnPostStartWorld", "InitKlusosPatrol") -- KLUSOSPATROL.scr:24
    ctx:onEvent("OnPostMiniSaveLoad", "InitKlusosPatrol") -- KLUSOSPATROL.scr:25
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- KLUSOSPATROL.scr:26
    do return ctx:exit("TRUE") end -- KLUSOSPATROL.scr:28
end

script.labels["CacheFiles"] = function(ctx)
    -- KLUSOSPATROL.scr:31
    ctx:cacheSound("sounds\\animsounds\\guard\\aware2.wav") -- KLUSOSPATROL.scr:33
    do return ctx:exit("TRUE") end -- KLUSOSPATROL.scr:35
end

script.labels["InitKlusosPatrol"] = function(ctx)
    -- KLUSOSPATROL.scr:38
    ctx:state().hTrigger = ctx:objectOrNil("GuardTrigger") -- KLUSOSPATROL.scr:40
    ctx:state().hBuddy = ctx:objectOrNil("sBuddyName") -- KLUSOSPATROL.scr:41
    ctx:self():addFriend("AIBase") -- KLUSOSPATROL.scr:43
    ctx:self():addEnemy("Player") -- KLUSOSPATROL.scr:44
    mm9.gosub(script, ctx, "SetTraverseLoop") -- KLUSOSPATROL.scr:46
    mm9.gosub(script, ctx, "SetTraverseWalk") -- KLUSOSPATROL.scr:47
    mm9.gosub(script, ctx, "BaseWanderInit") -- KLUSOSPATROL.scr:49
    mm9.gosub(script, ctx, "BaseDoorInit") -- KLUSOSPATROL.scr:50
    ctx:state().TRAVERSERADIUS = 10 -- KLUSOSPATROL.scr:52
    ctx:addTrigger("start", "TraverseBegin") -- KLUSOSPATROL.scr:54
    ctx:addTrigger("charge", "HuntPlayer") -- KLUSOSPATROL.scr:55
    ctx:onEvent("OnFoundTarget", "AlertOthers") -- KLUSOSPATROL.scr:57
    mm9.gosub(script, ctx, "TraverseBegin") -- KLUSOSPATROL.scr:59
    do return ctx:exit("TRUE") end -- KLUSOSPATROL.scr:61
end

script.labels["AlertOthers"] = function(ctx)
    -- KLUSOSPATROL.scr:64
    -- messages trigger to alert all guards
    if ctx:condition("hTrigger!=0") then -- KLUSOSPATROL.scr:67
        ctx:trigger("hTrigger", "trigger") -- KLUSOSPATROL.scr:68
    end -- KLUSOSPATROL.scr:69
    ctx:playSound("sounds\\animsounds\\guard\\aware2.wav", "DoNothing", 1, 100, "FALSE", 100) -- KLUSOSPATROL.scr:71
    mm9.gosub(script, ctx, "HuntPlayer") -- KLUSOSPATROL.scr:73
    do return ctx:exit("TRUE") end -- KLUSOSPATROL.scr:75
end

script.labels["HuntPlayer"] = function(ctx)
    -- KLUSOSPATROL.scr:78
    -- runs if foundplayer or alerted
    mm9.gosub(script, ctx, "BaseInit") -- KLUSOSPATROL.scr:81
    ctx:state().g_hTarget = ctx:player() -- KLUSOSPATROL.scr:82
    mm9.gosub(script, ctx, "SetupTarget") -- KLUSOSPATROL.scr:83
    mm9.gosub(script, ctx, "AggressiveStart") -- KLUSOSPATROL.scr:84
    do return ctx:exit("TRUE") end -- KLUSOSPATROL.scr:86
end

script.labels["OnTraverseDone"] = function(ctx)
    -- KLUSOSPATROL.scr:89
    -- indices: 0-24
    -- midpoint 12,13
    -- rooms: 4,7,10,13,15,18,21
    if ctx:condition("LISTINDEX==38") then -- KLUSOSPATROL.scr:95
        if ctx:condition("hBuddy!=0") then -- KLUSOSPATROL.scr:96
            ctx:trigger("hBuddy", "start") -- KLUSOSPATROL.scr:97
        end -- KLUSOSPATROL.scr:98
    end -- KLUSOSPATROL.scr:99
    do return ctx:exit("TRUE") end -- KLUSOSPATROL.scr:101
end

return script
