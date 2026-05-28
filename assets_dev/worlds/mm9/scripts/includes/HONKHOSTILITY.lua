-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKHOSTILITY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Range.inc" }

-- HonkHostility.inc
-- by SJR
-- 01-10-02
-- Purpose:if player kills honk,
-- hits honky, or steals,
-- attack mercilessly
script.labels["InitHonkHostility"] = function(ctx)
    -- HONKHOSTILITY.inc:15
    ctx:command("addfriend", "Player") -- HONKHOSTILITY.inc:17
    ctx:command("getobjecthandle", "HONK_FRIENDLY, hostile_hHONK_FRIENDLY") -- HONKHOSTILITY.inc:19
    if ctx:condition("hostile_hHONK_FRIENDLY!=0") then -- HONKHOSTILITY.inc:20
        ctx:command("createobjectlink", "hostile_hHONK_FRIENDLY") -- HONKHOSTILITY.inc:21
        ctx:command("onobjectlinkbroken", "BecomeHostile") -- HONKHOSTILITY.inc:22
        ctx:command("ondamage", "_OnDamage") -- HONKHOSTILITY.inc:23
        ctx:command("ondeath", "_OnDeath") -- HONKHOSTILITY.inc:24
        ctx:command("onalert", "_OnDamage") -- HONKHOSTILITY.inc:25
    else -- HONKHOSTILITY.inc:26
        mm9.gosub(script, ctx, "BecomeHostile") -- HONKHOSTILITY.inc:27
    end -- HONKHOSTILITY.inc:28
    do return ctx:exit("TRUE") end -- HONKHOSTILITY.inc:30
end

script.labels["BecomeHostile"] = function(ctx)
    -- HONKHOSTILITY.inc:33
    ctx:command("hostile_hhonk_friendly", "= NULL") -- HONKHOSTILITY.inc:35
    ctx:addTrigger("use", "BlockRude") -- HONKHOSTILITY.inc:37
    ctx:command("addenemy", "Player") -- HONKHOSTILITY.inc:39
    mm9.gosub(script, ctx, "BaseInit") -- HONKHOSTILITY.inc:41
    mm9.gosub(script, ctx, "RangeInit") -- HONKHOSTILITY.inc:42
    do return ctx:exit("TRUE") end -- HONKHOSTILITY.inc:44
end

script.labels["_OnDamage"] = function(ctx)
    -- HONKHOSTILITY.inc:47
    ctx:getParam(0, "g_hObject") -- HONKHOSTILITY.inc:49
    ctx:command("isplayer", "g_hObject, g_bTemp") -- HONKHOSTILITY.inc:50
    if ctx:condition("g_bTemp==TRUE") then -- HONKHOSTILITY.inc:51
        ctx:command("ondamage", "DoNothing") -- HONKHOSTILITY.inc:52
        ctx:command("ondeath", "DoNothing") -- HONKHOSTILITY.inc:53
        mm9.gosub(script, ctx, "TurnHostilityOn") -- HONKHOSTILITY.inc:54
    end -- HONKHOSTILITY.inc:55
    mm9.gosub(script, ctx, "OnDamage") -- HONKHOSTILITY.inc:57
    do return ctx:exit("TRUE") end -- HONKHOSTILITY.inc:59
end

script.labels["_OnDeath"] = function(ctx)
    -- HONKHOSTILITY.inc:62
    ctx:getParam(0, "g_hObject") -- HONKHOSTILITY.inc:64
    ctx:command("isplayer", "g_hObject, g_bTemp") -- HONKHOSTILITY.inc:65
    if ctx:condition("g_bTemp==TRUE") then -- HONKHOSTILITY.inc:66
        ctx:command("ondamage", "DoNothing") -- HONKHOSTILITY.inc:67
        ctx:command("ondeath", "DoNothing") -- HONKHOSTILITY.inc:68
        mm9.gosub(script, ctx, "TurnHostilityOn") -- HONKHOSTILITY.inc:69
    end -- HONKHOSTILITY.inc:70
    mm9.gosub(script, ctx, "OnDeath") -- HONKHOSTILITY.inc:72
    do return ctx:exit("TRUE") end -- HONKHOSTILITY.inc:74
end

script.labels["TurnHostilityOn"] = function(ctx)
    -- HONKHOSTILITY.inc:77
    if ctx:condition("hostile_hHONK_FRIENDLY!=0") then -- HONKHOSTILITY.inc:79
        ctx:command("playsound", "\"sounds\\ambient\\birds\\honkers.wav\", DoNothing, 1, 5000, FALSE, 100") -- HONKHOSTILITY.inc:80
        ctx:command("removeobject", "hostile_hHONK_FRIENDLY") -- HONKHOSTILITY.inc:81
    end -- HONKHOSTILITY.inc:82
    do return ctx:exit("TRUE") end -- HONKHOSTILITY.inc:84
end

script.labels["BlockRude"] = function(ctx)
    -- HONKHOSTILITY.inc:87
    do return ctx:exit("TRUE") end -- HONKHOSTILITY.inc:89
end

return script
