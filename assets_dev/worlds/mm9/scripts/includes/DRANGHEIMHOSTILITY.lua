-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMHOSTILITY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }

-- DrangheimHostility.inc
-- by SJR
-- Purpose:routine for checking
-- the visitor's pass at
-- DrangheimPrison.
-- must gosub CheckPassInit
script.labels["InitDrangheimHostility"] = function(ctx)
    -- DRANGHEIMHOSTILITY.inc:22
    -- set up handlers etc
    mm9.gosub(script, ctx, "BaseInit") -- DRANGHEIMHOSTILITY.inc:25
    ctx:command("checkpass_bhostile", "= FALSE") -- DRANGHEIMHOSTILITY.inc:27
    ctx:command("onfoundplayer", "OnFoundPlayer") -- DRANGHEIMHOSTILITY.inc:29
    ctx:command("ondamage", "OnDamage") -- DRANGHEIMHOSTILITY.inc:30
    ctx:command("ondeath", "OnDeath") -- DRANGHEIMHOSTILITY.inc:31
    ctx:command("addfriend", "Player") -- DRANGHEIMHOSTILITY.inc:33
    ctx:addTrigger("hostile", "TurnHostilityOn") -- DRANGHEIMHOSTILITY.inc:35
    do return ctx:exit("TRUE") end -- DRANGHEIMHOSTILITY.inc:37
end

script.labels["OnFoundPlayer"] = function(ctx)
    -- DRANGHEIMHOSTILITY.inc:40
    -- override baseMelee handlers everywhere
    ctx:hasKey("DP_PASS_FRIENDLY", "checkpass_bIsVisitor") -- DRANGHEIMHOSTILITY.inc:43
    ctx:hasKey("DP_PASS_HOSTILE", "checkpass_bIsFriendly") -- DRANGHEIMHOSTILITY.inc:44
    ctx:command("checkpass_bisfriendly", "= 1 - checkpass_bIsFriendly") -- DRANGHEIMHOSTILITY.inc:45
    ctx:command("checkpass_battackok", "= checkpass_bIsVisitor * checkpass_bIsFriendly") -- DRANGHEIMHOSTILITY.inc:47
    if ctx:condition("checkpass_bAttackOk==0") then -- DRANGHEIMHOSTILITY.inc:49
        ctx:command("checkpass_bhostile", "= TRUE") -- DRANGHEIMHOSTILITY.inc:50
        ctx:command("onfoundplayer", "DoNothing") -- DRANGHEIMHOSTILITY.inc:51
        ctx:command("getplayerhandle", "g_hTarget") -- DRANGHEIMHOSTILITY.inc:52
        mm9.gosub(script, ctx, "SetupTarget") -- DRANGHEIMHOSTILITY.inc:53
        mm9.gosub(script, ctx, "AggressiveStart") -- DRANGHEIMHOSTILITY.inc:54
    end -- DRANGHEIMHOSTILITY.inc:55
    do return ctx:exit("TRUE") end -- DRANGHEIMHOSTILITY.inc:57
end

script.labels["OnDamage"] = function(ctx)
    -- DRANGHEIMHOSTILITY.inc:60
    -- override baseMelee handlers everywhere
    if ctx:condition("checkpass_bHostile==FALSE") then -- DRANGHEIMHOSTILITY.inc:63
        ctx:getParam(0, "g_hTarget") -- DRANGHEIMHOSTILITY.inc:64
        ctx:command("isplayer", "g_hTarget, checkpass_bIsPlayer") -- DRANGHEIMHOSTILITY.inc:65
        if ctx:condition("checkpass_bIsPlayer==TRUE") then -- DRANGHEIMHOSTILITY.inc:67
            mm9.gosub(script, ctx, "TurnHostilityOn") -- DRANGHEIMHOSTILITY.inc:68
        end -- DRANGHEIMHOSTILITY.inc:69
    end -- DRANGHEIMHOSTILITY.inc:70
    mm9.gosub(script, ctx, "OnDamage") -- DRANGHEIMHOSTILITY.inc:72
    do return ctx:exit("TRUE") end -- DRANGHEIMHOSTILITY.inc:74
end

script.labels["OnDeath"] = function(ctx)
    -- DRANGHEIMHOSTILITY.inc:77
    -- override baseMelee handlers everywhere
    if ctx:condition("checkpass_bHostile==FALSE") then -- DRANGHEIMHOSTILITY.inc:80
        ctx:getParam(0, "g_hTarget") -- DRANGHEIMHOSTILITY.inc:81
        ctx:command("isplayer", "g_hTarget, checkpass_bIsPlayer") -- DRANGHEIMHOSTILITY.inc:82
        if ctx:condition("checkpass_bIsPlayer==TRUE") then -- DRANGHEIMHOSTILITY.inc:84
            mm9.gosub(script, ctx, "TurnHostilityOn") -- DRANGHEIMHOSTILITY.inc:85
        end -- DRANGHEIMHOSTILITY.inc:86
    end -- DRANGHEIMHOSTILITY.inc:87
    mm9.gosub(script, ctx, "OnDeath") -- DRANGHEIMHOSTILITY.inc:89
    do return ctx:exit("TRUE") end -- DRANGHEIMHOSTILITY.inc:91
end

script.labels["TurnHostilityOn"] = function(ctx)
    -- DRANGHEIMHOSTILITY.inc:94
    ctx:command("addenemy", "Player") -- DRANGHEIMHOSTILITY.inc:96
    ctx:addTrigger("use", "BlockRude") -- DRANGHEIMHOSTILITY.inc:98
    ctx:giveKey("DP_PASS_HOSTILE") -- DRANGHEIMHOSTILITY.inc:100
    ctx:command("playsound", "\"sounds\\events\\alarmbell.wav\", DoNothing, 1, 5000, FALSE, 100") -- DRANGHEIMHOSTILITY.inc:102
    do return ctx:exit("TRUE") end -- DRANGHEIMHOSTILITY.inc:104
end

script.labels["BlockRude"] = function(ctx)
    -- DRANGHEIMHOSTILITY.inc:107
    do return ctx:exit("TRUE") end -- DRANGHEIMHOSTILITY.inc:109
end

return script
