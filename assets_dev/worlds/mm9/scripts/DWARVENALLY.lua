-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DWARVENALLY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "ListTraverse.inc" }

-- DwarvenAlly.scr
-- by SJR
-- 10-03-01
-- Purpose:aid in staged
-- fights, guide player to
-- first shutoff area,
-- basically a plot device
-- ScriptParams:
-- p0 = name of tunnel to destroy for player
-- if omitted, will just fight
script.labels["Main"] = function(ctx)
    -- DWARVENALLY.scr:21
    ctx:getParam(0, "sTunnelName") -- DWARVENALLY.scr:23
    if ctx:condition("sTunnelName==\"0\"") then -- DWARVENALLY.scr:25
        ctx:onEvent("OnFoundTarget", "SetupMelee") -- DWARVENALLY.scr:26
    else -- DWARVENALLY.scr:27
        ctx:getParam(1, "LISTNAME") -- DWARVENALLY.scr:28
        ctx:getParam(2, "LISTFIRST") -- DWARVENALLY.scr:29
        ctx:getParam(3, "LISTLAST") -- DWARVENALLY.scr:30
        ctx:set("nTemp", "LISTFIRST + 1") -- DWARVENALLY.scr:31
        mm9.gosub(script, ctx, "SetTraverseOnce") -- DWARVENALLY.scr:32
        mm9.gosub(script, ctx, "SetTraverseRun") -- DWARVENALLY.scr:33
        ctx:onEvent("OnFoundPlayer", "TraverseBegin") -- DWARVENALLY.scr:34
        ctx:onEvent("OnDeath", "UnlockBin") -- DWARVENALLY.scr:35
    end -- DWARVENALLY.scr:36
    -- OnPostStartWorld InitDwarvenAlly
    ctx:wait(0, 5, "InitDwarvenAlly") -- DWARVENALLY.scr:39
    do return ctx:exit("TRUE") end -- DWARVENALLY.scr:41
end

script.labels["InitDwarvenAlly"] = function(ctx)
    -- DWARVENALLY.scr:44
    ctx:self():addEnemy("AIBase") -- DWARVENALLY.scr:46
    -- add the whole family
    ctx:self():addFriend("DwarvenSoldier") -- DWARVENALLY.scr:49
    ctx:self():addFriend("DwarvenGuard") -- DWARVENALLY.scr:50
    ctx:self():addFriend("DwarvenCommander") -- DWARVENALLY.scr:51
    ctx:self():addFriend("Player") -- DWARVENALLY.scr:52
    ctx:onEvent("OnStuck", "TraverseResume") -- DWARVENALLY.scr:54
    do return ctx:exit("TRUE") end -- DWARVENALLY.scr:56
end

script.labels["SetupMelee"] = function(ctx)
    -- DWARVENALLY.scr:59
    mm9.gosub(script, ctx, "BaseInit") -- DWARVENALLY.scr:61
    ctx:getParam(0, "g_hTarget") -- DWARVENALLY.scr:63
    mm9.gosub(script, ctx, "SetupTarget") -- DWARVENALLY.scr:65
    mm9.gosub(script, ctx, "AggressiveStart") -- DWARVENALLY.scr:66
    do return ctx:exit("TRUE") end -- DWARVENALLY.scr:68
end

script.labels["OnTraverseDone"] = function(ctx)
    -- DWARVENALLY.scr:75
    ctx:onEvent("OnFoundPlayer", "DoNothing") -- DWARVENALLY.scr:77
    if ctx:condition("LISTINDEX==LISTFIRST") then -- DWARVENALLY.scr:79
        ctx:rolloverText(100, "SCREEN_TYPE", 3000, 3000, "SCREEN_X", "SCREEN_Y") -- DWARVENALLY.scr:80
        -- play sound "follow me!"
        -- play animation
    end -- DWARVENALLY.scr:83
    if ctx:condition("LISTINDEX = nTemp") then -- DWARVENALLY.scr:85
        ctx:rolloverText(103, "SCREEN_TYPE", 3000, 3000, "SCREEN_X", "SCREEN_Y") -- DWARVENALLY.scr:86
    end -- DWARVENALLY.scr:87
    if ctx:condition("LISTINDEX==LISTLAST") then -- DWARVENALLY.scr:89
        mm9.gosub(script, ctx, "TraversePause") -- DWARVENALLY.scr:90
        ctx:rolloverText(101, "SCREEN_TYPE", 3000, 3000, "SCREEN_X", "SCREEN_Y") -- DWARVENALLY.scr:91
        ctx:state().hTunnel = ctx:objectOrNil("sTunnelName") -- DWARVENALLY.scr:92
        if ctx:condition("hTunnel!=0") then -- DWARVENALLY.scr:93
            ctx:trigger("hTunnel", "unlock") -- DWARVENALLY.scr:94
            ctx:trigger("hTunnel", "use") -- DWARVENALLY.scr:95
        end -- DWARVENALLY.scr:96
        ctx:onEvent("OnDeath", "DoNothing") -- DWARVENALLY.scr:97
        ctx:wait(0, 6, "InformPlayer") -- DWARVENALLY.scr:98
    end -- DWARVENALLY.scr:99
    do return ctx:exit("TRUE") end -- DWARVENALLY.scr:101
end

script.labels["InformPlayer"] = function(ctx)
    -- DWARVENALLY.scr:104
    ctx:rolloverText(102, "SCREEN_TYPE", 5000, 4000, "SCREEN_X", "SCREEN_Y") -- DWARVENALLY.scr:106
    ctx:onEvent("OnFoundTarget", "SetupMelee") -- DWARVENALLY.scr:108
    do return ctx:exit("TRUE") end -- DWARVENALLY.scr:110
end

script.labels["UnlockBin"] = function(ctx)
    -- DWARVENALLY.scr:113
    -- ondeath, make sure player can shut it
    -- if we die prematurely
    if ctx:condition("hTunnel==0") then -- DWARVENALLY.scr:117
        ctx:state().hTunnel = ctx:objectOrNil("sTunnelName") -- DWARVENALLY.scr:118
    end -- DWARVENALLY.scr:119
    if ctx:condition("hTunnel!=0") then -- DWARVENALLY.scr:120
        ctx:trigger("hTunnel", "unlock") -- DWARVENALLY.scr:121
    end -- DWARVENALLY.scr:122
    do return ctx:exit("TRUE") end -- DWARVENALLY.scr:124
end

return script
