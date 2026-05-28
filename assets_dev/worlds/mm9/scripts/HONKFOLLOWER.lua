-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKFOLLOWER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "ListTraverse.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "baseWander.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "HonkHostility.inc" }

-- HonkFollower.scr
-- by SJR
-- 10-06-01
-- Purpose:participate in the ceremony
-- started by HonkLeader.scr
-- ScriptParams are:
-- p0 = Base name of marker list
-- p1 = index of first marker
-- p2 = index of last marker
script.labels["Main"] = function(ctx)
    -- HONKFOLLOWER.scr:36
    ctx:getParam(0, "LISTNAME") -- HONKFOLLOWER.scr:38
    ctx:getParam(1, "LISTFIRST") -- HONKFOLLOWER.scr:39
    ctx:getParam(2, "LISTLAST") -- HONKFOLLOWER.scr:40
    ctx:command("onpoststartworld", "InitHonkFollower") -- HONKFOLLOWER.scr:42
    ctx:command("onpostminisaveload", "InitHonkFollower") -- HONKFOLLOWER.scr:43
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:45
end

script.labels["InitHonkFollower"] = function(ctx)
    -- HONKFOLLOWER.scr:48
    ctx:command("getmyhandle", "hPodium") -- HONKFOLLOWER.scr:50
    ctx:command("setstat", "hPodium, AutoDeactivate, FALSE") -- HONKFOLLOWER.scr:51
    ctx:command("hpodium", "= NULL") -- HONKFOLLOWER.scr:52
    mm9.gosub(script, ctx, "InitHonkHostility") -- HONKFOLLOWER.scr:54
    ctx:getConsoleStrVar("HONK_PASTOR", "sPastorName") -- HONKFOLLOWER.scr:56
    ctx:command("getobjecthandle", "sPastorName, hPodium") -- HONKFOLLOWER.scr:57
    if ctx:condition("hPodium!=0") then -- HONKFOLLOWER.scr:58
        ctx:command("createobjectlink", "hPodium") -- HONKFOLLOWER.scr:59
        ctx:command("onobjectlinkbroken", "OnObjectLinkBroken") -- HONKFOLLOWER.scr:60
    end -- HONKFOLLOWER.scr:61
    ctx:command("arrayput", "spAnims, 0, \"hattack2\"") -- HONKFOLLOWER.scr:63
    ctx:command("arrayput", "spAnims, 1, \"hattack1\"") -- HONKFOLLOWER.scr:64
    ctx:command("arrayput", "spAnims, 2, \"fidget1\"") -- HONKFOLLOWER.scr:65
    ctx:command("arrayput", "spAnims, 3, \"fidget2\"") -- HONKFOLLOWER.scr:66
    mm9.gosub(script, ctx, "SetTraverseWalk") -- HONKFOLLOWER.scr:68
    mm9.gosub(script, ctx, "SetTraverseOnce") -- HONKFOLLOWER.scr:69
    ctx:command("@m", "6 : 15, OnRingGong, DoNothing") -- HONKFOLLOWER.scr:71
    ctx:command("@m", "6 : 45, EndCeremony, DoNothing") -- HONKFOLLOWER.scr:72
    ctx:command("@m", "18 : 15, OnRingGong, DoNothing") -- HONKFOLLOWER.scr:74
    ctx:command("@m", "18 : 45, EndCeremony, DoNothing") -- HONKFOLLOWER.scr:75
    mm9.gosub(script, ctx, "BaseWanderInit") -- HONKFOLLOWER.scr:77
    mm9.gosub(script, ctx, "BaseWanderStartup") -- HONKFOLLOWER.scr:78
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:80
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- HONKFOLLOWER.scr:83
    ctx:getParam(0, "hLink") -- HONKFOLLOWER.scr:85
    if ctx:condition("hLink==hPodium") then -- HONKFOLLOWER.scr:86
        ctx:command("hpodium", "= NULL") -- HONKFOLLOWER.scr:87
    end -- HONKFOLLOWER.scr:88
    mm9.gosub(script, ctx, "BecomeHostile") -- HONKFOLLOWER.scr:90
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:92
end

script.labels["OnRingGong"] = function(ctx)
    -- HONKFOLLOWER.scr:95
    -- scheduled for beginning of ceremony
    mm9.gosub(script, ctx, "BaseWanderStop") -- HONKFOLLOWER.scr:98
    if ctx:condition("bAttended==TRUE") then -- HONKFOLLOWER.scr:100
        do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:101
    end -- HONKFOLLOWER.scr:102
    ctx:command("battended", "= TRUE") -- HONKFOLLOWER.scr:103
    if ctx:condition("hPodium!=0") then -- HONKFOLLOWER.scr:105
        ctx:command("faceobject", "hPodium, 180, TraverseBegin") -- HONKFOLLOWER.scr:106
    end -- HONKFOLLOWER.scr:107
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:109
end

script.labels["StartCeremony"] = function(ctx)
    -- HONKFOLLOWER.scr:112
    -- start anim\sound loop
    ctx:command("stop", "") -- HONKFOLLOWER.scr:115
    if ctx:condition("hPodium!=0") then -- HONKFOLLOWER.scr:116
        ctx:trigger("hPodium", "FollowerReady") -- HONKFOLLOWER.scr:117
        ctx:command("faceobject", "hPodium, 180, PlayRandomAnim") -- HONKFOLLOWER.scr:118
    end -- HONKFOLLOWER.scr:119
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:121
end

script.labels["OnTraverseDone"] = function(ctx)
    -- HONKFOLLOWER.scr:124
    -- do whatever when we're at each marker
    mm9.gosub(script, ctx, "TraversePause") -- HONKFOLLOWER.scr:127
    if ctx:condition("LISTINDEX==LISTLAST") then -- HONKFOLLOWER.scr:128
        mm9.gosub(script, ctx, "StartCeremony") -- HONKFOLLOWER.scr:129
    else -- HONKFOLLOWER.scr:130
        mm9.gosub(script, ctx, "TraverseResume") -- HONKFOLLOWER.scr:131
    end -- HONKFOLLOWER.scr:132
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:134
end

script.labels["EndCeremony"] = function(ctx)
    -- HONKFOLLOWER.scr:137
    -- reverse path, go back
    ctx:command("bceremonydone", "= TRUE") -- HONKFOLLOWER.scr:140
    mm9.gosub(script, ctx, "ReversePath") -- HONKFOLLOWER.scr:141
    ctx:command("wait", "1, 5, TraverseBegin") -- HONKFOLLOWER.scr:142
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:144
end

script.labels["PlayRandomAnim"] = function(ctx)
    -- HONKFOLLOWER.scr:147
    -- pick number, do that anim
    if ctx:condition("bCeremonyDone==TRUE") then -- HONKFOLLOWER.scr:150
        do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:151
    end -- HONKFOLLOWER.scr:152
    ctx:command("getrandomint", "1, 3, rand") -- HONKFOLLOWER.scr:154
    ctx:command("arrayget", "spAnims, rand, sAnim") -- HONKFOLLOWER.scr:155
    ctx:command("playanim", "sAnim, PlayRandomAnim") -- HONKFOLLOWER.scr:156
    do return ctx:exit("TRUE") end -- HONKFOLLOWER.scr:158
end

return script
