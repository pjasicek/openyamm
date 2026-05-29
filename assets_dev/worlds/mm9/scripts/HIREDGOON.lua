-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HIREDGOON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "FollowPlayer.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }

-- BaseGlobals.inc
-- by SJR
-- 11-12-01
-- Purpose:follow player and beat
-- things up
script.labels["Main"] = function(ctx)
    -- HIREDGOON.scr:19
    ctx:wait(0, 1, "InitHiredGoon") -- HIREDGOON.scr:21
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:23
end

script.labels["InitHiredGoon"] = function(ctx)
    -- HIREDGOON.scr:26
    ctx:self():addEnemy("AIBase") -- HIREDGOON.scr:28
    ctx:self():addFriend("Player") -- HIREDGOON.scr:29
    ctx:addTrigger("Hostile", "BecomeHostile") -- HIREDGOON.scr:31
    ctx:addTrigger("Friendly", "BecomeFriendly") -- HIREDGOON.scr:32
    ctx:addTrigger("Destroy", "Destroy") -- HIREDGOON.scr:33
    mm9.gosub(script, ctx, "BaseInit") -- HIREDGOON.scr:37
    mm9.gosub(script, ctx, "FollowInit") -- HIREDGOON.scr:38
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- HIREDGOON.scr:40
    ctx:onEvent("OnDamage", "OnDamage") -- HIREDGOON.scr:41
    ctx:onEvent("OnTargetDead", "BecomeFriendly") -- HIREDGOON.scr:42
    mm9.gosub(script, ctx, "BecomeFriendly") -- HIREDGOON.scr:44
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:46
end

script.labels["BecomeFriendly"] = function(ctx)
    -- HIREDGOON.scr:49
    ctx:self():setTarget(nil) -- HIREDGOON.scr:51
    ctx:state().hEnemy = nil -- HIREDGOON.scr:52
    ctx:state().g_hTarget = nil -- HIREDGOON.scr:53
    mm9.gosub(script, ctx, "FollowStart") -- HIREDGOON.scr:55
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:57
end

script.labels["BecomeHostile"] = function(ctx)
    -- HIREDGOON.scr:60
    mm9.gosub(script, ctx, "FollowStop") -- HIREDGOON.scr:62
    ctx:self():addFriend("AIBase") -- HIREDGOON.scr:64
    ctx:self():addEnemy("Player") -- HIREDGOON.scr:65
    ctx:playSound("sounds\\animsounds\\dragon\\fidget2.wav", "DoNothing", 1, 1000, "FALSE", 100) -- HIREDGOON.scr:67
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:69
end

script.labels["Destroy"] = function(ctx)
    -- HIREDGOON.scr:72
    mm9.gosub(script, ctx, "FollowStop") -- HIREDGOON.scr:74
    ctx:self():die() -- HIREDGOON.scr:75
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:76
end

script.labels["OnFoundTarget"] = function(ctx)
    -- HIREDGOON.scr:79
    ctx:getParam(0, "hEnemy") -- HIREDGOON.scr:81
    mm9.gosub(script, ctx, "FollowStop") -- HIREDGOON.scr:82
    mm9.gosub(script, ctx, "LinkToBaseMelee") -- HIREDGOON.scr:83
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:85
end

script.labels["LinkToBaseMelee"] = function(ctx)
    -- HIREDGOON.scr:88
    -- transfer control to baseMelee
    -- baseMelee needs this, since removed GetParam
    ctx:set("g_hTarget", "hEnemy") -- HIREDGOON.scr:92
    mm9.gosub(script, ctx, "SetupTarget") -- HIREDGOON.scr:94
    mm9.gosub(script, ctx, "AggressiveStop") -- HIREDGOON.scr:95
    ctx:randomInt(0, 100, "g_nRandom") -- HIREDGOON.scr:97
    if ctx:condition("g_nRandom < AWARE_CHANCE") then -- HIREDGOON.scr:99
        ctx:self():aware("AwareDone") -- HIREDGOON.scr:100
    else -- HIREDGOON.scr:101
        mm9.gosub(script, ctx, "AggressiveStart") -- HIREDGOON.scr:102
    end -- HIREDGOON.scr:103
    do return ctx:exit(1) end -- HIREDGOON.scr:105
end

script.labels["OnDamage"] = function(ctx)
    -- HIREDGOON.scr:111
    ctx:getParam(0, "hDummy") -- HIREDGOON.scr:113
    ctx:state().bIsPlayer = ctx:object("hDummy"):isPlayer() -- HIREDGOON.scr:114
    if ctx:condition("bIsPlayer==TRUE") then -- HIREDGOON.scr:116
        ctx:set("nCounter", "nCounter + 1") -- HIREDGOON.scr:117
    end -- HIREDGOON.scr:118
    if ctx:condition("nCounter>4") then -- HIREDGOON.scr:119
        mm9.gosub(script, ctx, "BecomeHostile") -- HIREDGOON.scr:120
    end -- HIREDGOON.scr:121
    do return ctx:exit("TRUE") end -- HIREDGOON.scr:123
end

return script
