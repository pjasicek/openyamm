-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_CHECKPASS.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }

-- DP_CheckPass.inc
-- by SJR
-- Purpose:routine for checking
-- the visitor's pass at
-- DrangheimPrison.
-- must gosub CheckPassInit
script.labels["InitCheckPass"] = function(ctx)
    -- DP_CHECKPASS.inc:22
    -- set up handlers etc
    mm9.gosub(script, ctx, "BaseInit") -- DP_CHECKPASS.inc:25
    -- gotta override BaseMelee.inc for these
    ctx:command("onfoundtarget", "OnFoundTarget") -- DP_CHECKPASS.inc:28
    ctx:command("ondamage", "OnDamage") -- DP_CHECKPASS.inc:29
    do return ctx:exit(1) end -- DP_CHECKPASS.inc:31
end

script.labels["OnFoundTarget"] = function(ctx)
    -- DP_CHECKPASS.inc:34
    -- override baseMelee handlers everywhere
    ctx:getParam(0, "checkpass_hObject") -- DP_CHECKPASS.inc:37
    ctx:command("isplayer", "checkpass_hObject, checkpass_bIsPlayer") -- DP_CHECKPASS.inc:38
    ctx:hasKey("DP_PASS_FRIENDLY", "checkpass_bIsVisitor") -- DP_CHECKPASS.inc:40
    -- IsFriendly actually used as IsHostile
    ctx:hasKey("DP_PASS_HOSTILE", "checkpass_bIsFriendly") -- DP_CHECKPASS.inc:43
    -- change to IsFriendly with IsFriendly=!IsHostile
    ctx:command("checkpass_bisfriendly", "= 1 - checkpass_bIsFriendly") -- DP_CHECKPASS.inc:46
    -- == 0 if notplayer OR notvisitor OR notfriendly
    ctx:command("checkpass_battackok", "= checkpass_bIsPlayer * checkpass_bIsVisitor * checkpass_bIsFriendly") -- DP_CHECKPASS.inc:49
    -- if == 0, attack
    if ctx:condition("checkpass_bAttackOk == 0") then -- DP_CHECKPASS.inc:52
        mm9.gosub(script, ctx, "LinkToBaseMelee") -- DP_CHECKPASS.inc:53
    end -- DP_CHECKPASS.inc:54
    do return ctx:exit(1) end -- DP_CHECKPASS.inc:56
end

script.labels["OnDamage"] = function(ctx)
    -- DP_CHECKPASS.inc:59
    -- override baseMelee handlers everywhere
    ctx:getParam(0, "checkpass_hObject") -- DP_CHECKPASS.inc:62
    ctx:command("isplayer", "checkpass_hObject, checkpass_bIsPlayer") -- DP_CHECKPASS.inc:63
    -- if player damages us, give them the hostile key
    if ctx:condition("checkpass_bIsPlayer==1") then -- DP_CHECKPASS.inc:66
        ctx:giveKey("DP_PASS_HOSTILE") -- DP_CHECKPASS.inc:67
        mm9.gosub(script, ctx, "LinkToBaseMelee") -- DP_CHECKPASS.inc:68
    end -- DP_CHECKPASS.inc:69
    ctx:hasKey("DP_PASS_FRIENDLY", "checkpass_bIsVisitor") -- DP_CHECKPASS.inc:71
    -- IsFriendly actually used as IsHostile
    ctx:hasKey("DP_PASS_HOSTILE", "checkpass_bIsFriendly") -- DP_CHECKPASS.inc:74
    -- change to IsFriendly with IsFriendly=!IsHostile
    ctx:command("checkpass_bisfriendly", "= 1 - checkpass_bIsFriendly") -- DP_CHECKPASS.inc:77
    -- == 0 if notplayer OR notvisitor OR notfriendly
    ctx:command("checkpass_battackok", "= checkpass_bIsPlayer * checkpass_bIsVisitor * checkpass_bIsFriendly") -- DP_CHECKPASS.inc:80
    -- if == 0, attack
    if ctx:condition("checkpass_bAttackOk == 0") then -- DP_CHECKPASS.inc:83
        mm9.gosub(script, ctx, "LinkToBaseMelee") -- DP_CHECKPASS.inc:84
    end -- DP_CHECKPASS.inc:85
    do return ctx:exit(1) end -- DP_CHECKPASS.inc:87
end

script.labels["LinkToBaseMelee"] = function(ctx)
    -- DP_CHECKPASS.inc:90
    -- transfer control to baseMelee
    -- baseMelee needs this, since removed GetParam
    ctx:command("g_htarget", "= checkpass_hObject") -- DP_CHECKPASS.inc:94
    mm9.gosub(script, ctx, "SetupTarget") -- DP_CHECKPASS.inc:96
    mm9.gosub(script, ctx, "AggressiveStop") -- DP_CHECKPASS.inc:97
    ctx:command("getrandomint", "0, 100, g_nRandom") -- DP_CHECKPASS.inc:99
    if ctx:condition("g_nRandom < AWARE_CHANCE") then -- DP_CHECKPASS.inc:101
        ctx:command("aware", "AwareDone") -- DP_CHECKPASS.inc:102
    else -- DP_CHECKPASS.inc:103
        mm9.gosub(script, ctx, "AggressiveStart") -- DP_CHECKPASS.inc:104
    end -- DP_CHECKPASS.inc:105
    do return ctx:exit(1) end -- DP_CHECKPASS.inc:107
end

return script
