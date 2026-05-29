-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "POLICEMAN.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 19, path = "basemelee.inc" }

-- PoliceMan.Inc
-- Jeff Leggett
-- 08/22/2001
-- Behavior
-- - Don't attack anyone unless someone calls for help
-- - If we get a call for help, if we have a path to
-- the target, then we'll go after it. Otherwise, we
-- won't...
-- - Just run the wander script until someone needs us.
-- (or attacks us!)
-- Max # of times we'll let the player hit us before we get pissed...
script.labels["SetupTarget"] = function(ctx)
    -- POLICEMAN.inc:28
    mm9.gosub(script, ctx, "SetupTarget") -- POLICEMAN.inc:30
    ctx:state().g_bTemp = ctx:object("g_hTarget"):isPlayer() -- POLICEMAN.inc:32
    if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:34
        ctx:self():addEnemy("Player") -- POLICEMAN.inc:35
    end -- POLICEMAN.inc:36
    do return ctx:exit("") end -- POLICEMAN.inc:38
end

script.labels["PoliceAlert"] = function(ctx)
    -- POLICEMAN.inc:41
    -- Make sure it's not a monster alert.  We don't protect monsters...
    -- p0	- Handle of AI who sent the alert
    -- p1	- Handle of that AI's target
    ctx:getParam(0, "g_hObject") -- POLICEMAN.inc:50
    ctx:state().g_bTemp = ctx:object("g_hObject"):getStat("IsMonster") -- POLICEMAN.inc:52
    if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:54
        do return ctx:exit("") end -- POLICEMAN.inc:55
    end -- POLICEMAN.inc:56
    ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("GuardBase") -- POLICEMAN.inc:58
    if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:60
        -- if a fellow guard is alerting me to this guy, then
        -- he's an enemy now...
        ctx:getParam(1, "g_hObject") -- POLICEMAN.inc:64
        ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- POLICEMAN.inc:66
        if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:67
            ctx:state().g_sTemp = ctx:object("g_hObject"):className() -- POLICEMAN.inc:68
            ctx:self():addEnemy("g_sTemp") -- POLICEMAN.inc:69
        end -- POLICEMAN.inc:70
    end -- POLICEMAN.inc:71
    mm9.gosub(script, ctx, "OnAlert") -- POLICEMAN.inc:74
    do return ctx:exit("") end -- POLICEMAN.inc:76
end

script.labels["OnHelp"] = function(ctx)
    -- POLICEMAN.inc:79
    -- Help is different then Alert.  If the call for help, then
    -- we'll see
    -- Todo: Do more extensive checks...
    -- Make who ever they are yelping about an enemy..
    ctx:getParam(0, "g_hObject") -- POLICEMAN.inc:91
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- POLICEMAN.inc:93
    if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:95
        -- a friend says to hate this guy, so lets hate 'em...
        ctx:getParam(1, "g_hObject") -- POLICEMAN.inc:97
        ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- POLICEMAN.inc:98
        if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:99
            ctx:state().g_sTemp = ctx:object("g_hObject"):className() -- POLICEMAN.inc:100
            ctx:self():removeFriend("g_sTemp") -- POLICEMAN.inc:101
            ctx:self():addEnemy("g_sTemp") -- POLICEMAN.inc:102
        end -- POLICEMAN.inc:103
    end -- POLICEMAN.inc:104
    mm9.gosub(script, ctx, "OnHelp") -- POLICEMAN.inc:106
    do return ctx:exit("") end -- POLICEMAN.inc:108
end

script.labels["OnDamage"] = function(ctx)
    -- POLICEMAN.inc:111
    ctx:getParam(0, "g_hObject") -- POLICEMAN.inc:114
    ctx:state().g_bTemp = ctx:object("g_hObject"):isPlayer() -- POLICEMAN.inc:116
    if ctx:condition("g_bTemp==TRUE") then -- POLICEMAN.inc:118
        -- If a player hits us too much, they are no longer a friend!
        ctx:state().playerHitCount = (tonumber(ctx:state().playerHitCount) or 0) + 1 -- POLICEMAN.inc:120
        if ctx:condition("playerHitCount==MAX_PLAYER_HIT_TOLERATION") then -- POLICEMAN.inc:122
            ctx:self():addEnemy("Player") -- POLICEMAN.inc:123
        end -- POLICEMAN.inc:124
    end -- POLICEMAN.inc:125
    mm9.gosub(script, ctx, "OnDamage") -- POLICEMAN.inc:127
    do return ctx:exit("") end -- POLICEMAN.inc:129
end

script.labels["PoliceManInit"] = function(ctx)
    -- POLICEMAN.inc:132
    mm9.gosub(script, ctx, "BaseInit") -- POLICEMAN.inc:135
    ctx:onEvent("OnAlert", "PoliceAlert") -- POLICEMAN.inc:137
    ctx:onEvent("OnHelp", "OnHelp") -- POLICEMAN.inc:138
    -- gosub BaseWanderForceStartUp
    ctx:self():removeEnemy("NPC") -- POLICEMAN.inc:141
    -- Guards don't like monsters....
    ctx:self():addEnemy("AIBase") -- POLICEMAN.inc:146
    ctx:self():addFriend("Player") -- POLICEMAN.inc:148
    ctx:self():addFriend("Cat") -- POLICEMAN.inc:149
    ctx:self():addFriend("NPC") -- POLICEMAN.inc:150
    ctx:self():addFriend("Animal") -- POLICEMAN.inc:151
    ctx:self():addFriend("GuardBase") -- POLICEMAN.inc:152
    do return ctx:exit("") end -- POLICEMAN.inc:154
end

return script
