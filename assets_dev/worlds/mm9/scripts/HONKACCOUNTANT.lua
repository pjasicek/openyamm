-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKACCOUNTANT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "ListTraverse.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "HonkHostility.inc" }

-- HonkAccountant.scr
-- by SJR
-- 10-08-01
-- Purpose:collect money from
-- honks, do puzzle
-- store money in room
-- ScriptParams are:
-- p0 = Base name of marker list
-- p1 = index of first marker
-- p2 = index of last marker
script.labels["Main"] = function(ctx)
    -- HONKACCOUNTANT.scr:25
    ctx:getParam(0, "LISTNAME") -- HONKACCOUNTANT.scr:27
    ctx:getParam(1, "LISTFIRST") -- HONKACCOUNTANT.scr:28
    ctx:getParam(2, "LISTLAST") -- HONKACCOUNTANT.scr:29
    ctx:getParam(3, "sChestName") -- HONKACCOUNTANT.scr:30
    ctx:getParam(4, "sKeyName") -- HONKACCOUNTANT.scr:31
    ctx:onEvent("OnPostStartWorld", "InitHonkAccountant") -- HONKACCOUNTANT.scr:33
    ctx:onEvent("OnPostMiniSaveLoad", "InitHonkAccountant") -- HONKACCOUNTANT.scr:34
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:36
end

script.labels["InitHonkAccountant"] = function(ctx)
    -- HONKACCOUNTANT.scr:39
    mm9.gosub(script, ctx, "InitHonkHostility") -- HONKACCOUNTANT.scr:41
    ctx:state().hChest = ctx:objectOrNil("sChestName") -- HONKACCOUNTANT.scr:43
    ctx:state().hKey = ctx:objectOrNil("sKeyName") -- HONKACCOUNTANT.scr:44
    if ctx:condition("hKey!=0") then -- HONKACCOUNTANT.scr:45
        ctx:self():link(ctx:object("hKey")) -- HONKACCOUNTANT.scr:46
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- HONKACCOUNTANT.scr:47
    end -- HONKACCOUNTANT.scr:48
    ctx:atTime(7, 0, "TraverseBegin", "DoNothing") -- HONKACCOUNTANT.scr:50
    ctx:atTime(19, 0, "TraverseBegin", "DoNothing") -- HONKACCOUNTANT.scr:51
    mm9.gosub(script, ctx, "BaseWanderInit") -- HONKACCOUNTANT.scr:53
    ctx:addTrigger("stolen", "KeyWasStolen") -- HONKACCOUNTANT.scr:55
    mm9.gosub(script, ctx, "SetTraversePace") -- HONKACCOUNTANT.scr:57
    mm9.gosub(script, ctx, "SetTraverseWalk") -- HONKACCOUNTANT.scr:58
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:60
end

script.labels["OnTraverseDone"] = function(ctx)
    -- HONKACCOUNTANT.scr:63
    -- do accountant things along
    -- the way: key stuff, money etc
    if ctx:condition("LISTINDEX==LISTFIRST") then -- HONKACCOUNTANT.scr:67
        if ctx:condition("bForward==FALSE") then -- HONKACCOUNTANT.scr:68
            mm9.gosub(script, ctx, "TraversePause") -- HONKACCOUNTANT.scr:69
            mm9.gosub(script, ctx, "ReplaceKey") -- HONKACCOUNTANT.scr:70
        else -- HONKACCOUNTANT.scr:71
            mm9.gosub(script, ctx, "TakeKey") -- HONKACCOUNTANT.scr:72
        end -- HONKACCOUNTANT.scr:73
    end -- HONKACCOUNTANT.scr:74
    if ctx:condition("LISTINDEX==LISTLAST") then -- HONKACCOUNTANT.scr:76
        mm9.gosub(script, ctx, "TraversePause") -- HONKACCOUNTANT.scr:77
        mm9.gosub(script, ctx, "DoPuzzle") -- HONKACCOUNTANT.scr:78
    end -- HONKACCOUNTANT.scr:79
    if ctx:condition("LISTINDEX==3") then -- HONKACCOUNTANT.scr:81
        if ctx:condition("bForward==TRUE") then -- HONKACCOUNTANT.scr:82
            mm9.gosub(script, ctx, "TraversePause") -- HONKACCOUNTANT.scr:83
            mm9.gosub(script, ctx, "CollectMoney") -- HONKACCOUNTANT.scr:84
        end -- HONKACCOUNTANT.scr:85
    end -- HONKACCOUNTANT.scr:86
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:88
end

script.labels["CollectMoney"] = function(ctx)
    -- HONKACCOUNTANT.scr:91
    -- Trigger hChest, open
    ctx:wait(0, 2, "CloseChest") -- HONKACCOUNTANT.scr:94
    mm9.gosub(script, ctx, "TraverseResume") -- HONKACCOUNTANT.scr:95
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:97
end

script.labels["CloseChest"] = function(ctx)
    -- HONKACCOUNTANT.scr:100
    -- Trigger hChest, close
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:104
end

script.labels["DoPuzzle"] = function(ctx)
    -- HONKACCOUNTANT.scr:107
    ctx:self():playAnimation("prop-fidget1", "TraverseResume") -- HONKACCOUNTANT.scr:109
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:111
end

script.labels["TakeKey"] = function(ctx)
    -- HONKACCOUNTANT.scr:114
    if ctx:condition("hKey==0") then -- HONKACCOUNTANT.scr:116
        mm9.gosub(script, ctx, "KeyWasStolen") -- HONKACCOUNTANT.scr:117
    else -- HONKACCOUNTANT.scr:118
        ctx:trigger("hKey", "getkey") -- HONKACCOUNTANT.scr:119
        mm9.gosub(script, ctx, "TraverseResume") -- HONKACCOUNTANT.scr:120
    end -- HONKACCOUNTANT.scr:121
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:123
end

script.labels["ReplaceKey"] = function(ctx)
    -- HONKACCOUNTANT.scr:126
    ctx:trigger("hKey", "putkey") -- HONKACCOUNTANT.scr:128
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:130
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- HONKACCOUNTANT.scr:133
    -- null it out, hostile when we
    -- actually see it
    ctx:getParam(0, "hLink") -- HONKACCOUNTANT.scr:137
    if ctx:condition("hLink==0") then -- HONKACCOUNTANT.scr:139
        ctx:state().hKey = nil -- HONKACCOUNTANT.scr:140
    else -- HONKACCOUNTANT.scr:141
        mm9.gosub(script, ctx, "BecomeHostile") -- HONKACCOUNTANT.scr:142
    end -- HONKACCOUNTANT.scr:143
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:145
end

script.labels["KeyWasStolen"] = function(ctx)
    -- HONKACCOUNTANT.scr:148
    -- either saw it stolen
    -- or found it stolen
    ctx:state().hKey = nil -- HONKACCOUNTANT.scr:152
    ctx:removeTrigger("stolen") -- HONKACCOUNTANT.scr:154
    mm9.gosub(script, ctx, "TraversePause") -- HONKACCOUNTANT.scr:156
    mm9.gosub(script, ctx, "TurnHostilityOn") -- HONKACCOUNTANT.scr:157
    do return ctx:exit("TRUE") end -- HONKACCOUNTANT.scr:159
end

return script
