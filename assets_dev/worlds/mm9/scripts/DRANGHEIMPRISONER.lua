-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMPRISONER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }

-- DrangheimPrisoner.scr
-- SJR
-- Purpose:
-- hardcode these later
script.labels["Main"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:21
    ctx:getParam(0, "sCellName") -- DRANGHEIMPRISONER.scr:23
    ctx:command("onpoststartworld", "InitDrangheimPrisoner") -- DRANGHEIMPRISONER.scr:25
    ctx:command("onpostminisaveload", "InitDrangheimPrisoner") -- DRANGHEIMPRISONER.scr:26
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:28
end

script.labels["InitDrangheimPrisoner"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:31
    ctx:command("getobjecthandle", "sCellName, hCell") -- DRANGHEIMPRISONER.scr:33
    ctx:addTrigger("followme", "StartFollowing") -- DRANGHEIMPRISONER.scr:35
    ctx:addTrigger("return", "EnterCell") -- DRANGHEIMPRISONER.scr:36
    ctx:addTrigger("leave", "LeaveCell") -- DRANGHEIMPRISONER.scr:37
    ctx:addTrigger("use", "OnPlayerRescue") -- DRANGHEIMPRISONER.scr:38
    ctx:command("ontargetdead", "OnTargetDead") -- DRANGHEIMPRISONER.scr:40
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:42
end

script.labels["OnTargetDead"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:45
    ctx:command("hguard", "= NULL") -- DRANGHEIMPRISONER.scr:47
    ctx:command("target", "NULL") -- DRANGHEIMPRISONER.scr:48
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:50
end

script.labels["EnterCell"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:53
    ctx:command("breturning", "= TRUE") -- DRANGHEIMPRISONER.scr:55
    ctx:command("target", "NULL") -- DRANGHEIMPRISONER.scr:56
    if ctx:condition("hCell!=0") then -- DRANGHEIMPRISONER.scr:57
        ctx:command("walkto", "hCell, 5, OnEnteredCell") -- DRANGHEIMPRISONER.scr:58
    end -- DRANGHEIMPRISONER.scr:59
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:61
end

script.labels["LeaveCell"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:64
    ctx:getParam(0, "hGuard") -- DRANGHEIMPRISONER.scr:66
    ctx:command("target", "NULL") -- DRANGHEIMPRISONER.scr:67
    ctx:command("createobjectlink", "hGuard") -- DRANGHEIMPRISONER.scr:68
    ctx:command("walkto", "hGuard, 5, OnLeftCell") -- DRANGHEIMPRISONER.scr:69
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:71
end

script.labels["OnEnteredCell"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:74
    ctx:command("stop", "") -- DRANGHEIMPRISONER.scr:76
    if ctx:condition("hGuard!=0") then -- DRANGHEIMPRISONER.scr:78
        ctx:trigger("hGuard", "inside") -- DRANGHEIMPRISONER.scr:79
        ctx:command("faceobject", "hGuard, 180, DoNothing") -- DRANGHEIMPRISONER.scr:80
    end -- DRANGHEIMPRISONER.scr:81
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:83
end

script.labels["OnLeftCell"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:86
    ctx:command("stop", "") -- DRANGHEIMPRISONER.scr:88
    ctx:command("playanim", "cower, OnPlayedAnim") -- DRANGHEIMPRISONER.scr:89
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:91
end

script.labels["OnPlayedAnim"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:94
    if ctx:condition("hGuard!=0") then -- DRANGHEIMPRISONER.scr:96
        ctx:trigger("hGuard", "outside") -- DRANGHEIMPRISONER.scr:97
    end -- DRANGHEIMPRISONER.scr:98
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:100
end

script.labels["StartFollowing"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:103
    ctx:getParam(0, "hGuard") -- DRANGHEIMPRISONER.scr:105
    ctx:command("target", "hGuard, TRUE") -- DRANGHEIMPRISONER.scr:106
    ctx:command("breturning", "= FALSE") -- DRANGHEIMPRISONER.scr:107
    mm9.gosub(script, ctx, "FollowLoop") -- DRANGHEIMPRISONER.scr:108
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:110
end

script.labels["FollowLoop"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:113
    ctx:command("stop", "") -- DRANGHEIMPRISONER.scr:115
    if ctx:condition("bReturning==TRUE") then -- DRANGHEIMPRISONER.scr:116
        ctx:command("playanim", "Fidget3, DoNothing") -- DRANGHEIMPRISONER.scr:117
    else -- DRANGHEIMPRISONER.scr:118
        if ctx:condition("hGuard!=0") then -- DRANGHEIMPRISONER.scr:119
            ctx:command("walkto", "hGuard, 32, StopMoving") -- DRANGHEIMPRISONER.scr:120
            ctx:command("wait", "0, 1, FollowLoop") -- DRANGHEIMPRISONER.scr:121
        end -- DRANGHEIMPRISONER.scr:122
    end -- DRANGHEIMPRISONER.scr:123
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:125
end

script.labels["OnPlayerRescue"] = function(ctx)
    -- DRANGHEIMPRISONER.scr:128
    ctx:hasKey(5007, "nTemp") -- DRANGHEIMPRISONER.scr:130
    if ctx:condition("nTemp==FALSE") then -- DRANGHEIMPRISONER.scr:131
        ctx:command("removetrigger", "use") -- DRANGHEIMPRISONER.scr:132
        ctx:command("rollovertext", "TEXT_RESCUE, 1, 7000, 6000") -- DRANGHEIMPRISONER.scr:133
        ctx:giveExp("EXP_RESCUE") -- DRANGHEIMPRISONER.scr:134
    end -- DRANGHEIMPRISONER.scr:135
    do return ctx:exit("TRUE") end -- DRANGHEIMPRISONER.scr:137
end

return script
