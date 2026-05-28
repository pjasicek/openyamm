-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MONKHOSTILITY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "range.inc" }

-- MonkHostility.inc
-- by SJR
-- 01-01-02
-- Purpose:if player kills honk,
-- hits honky, or steals,
-- attack mercilessly
script.labels["InitMonkHostility"] = function(ctx)
    -- MONKHOSTILITY.inc:15
    ctx:command("addfriend", "Player") -- MONKHOSTILITY.inc:17
    ctx:command("getobjecthandle", "MONK_HOSTILITY, hostile_hMONK_HOSTILITY") -- MONKHOSTILITY.inc:19
    if ctx:condition("hostile_hMONK_HOSTILITY!=0") then -- MONKHOSTILITY.inc:20
        ctx:command("createobjectlink", "hostile_hMONK_HOSTILITY") -- MONKHOSTILITY.inc:21
        ctx:command("onobjectlinkbroken", "BecomeHostile") -- MONKHOSTILITY.inc:22
        ctx:command("ondamage", "_OnDamage") -- MONKHOSTILITY.inc:23
        ctx:command("ondeath", "_OnDeath") -- MONKHOSTILITY.inc:24
        ctx:command("onalert", "_OnDamage") -- MONKHOSTILITY.inc:25
    else -- MONKHOSTILITY.inc:26
        mm9.gosub(script, ctx, "BecomeHostile") -- MONKHOSTILITY.inc:27
    end -- MONKHOSTILITY.inc:28
    do return ctx:exit("TRUE") end -- MONKHOSTILITY.inc:30
end

script.labels["BecomeHostile"] = function(ctx)
    -- MONKHOSTILITY.inc:33
    ctx:command("hostile_hmonk_hostility", "= NULL") -- MONKHOSTILITY.inc:35
    ctx:addTrigger("use", "BlockRude") -- MONKHOSTILITY.inc:37
    ctx:command("addenemy", "Player") -- MONKHOSTILITY.inc:39
    mm9.gosub(script, ctx, "RangeInit") -- MONKHOSTILITY.inc:41
    mm9.gosub(script, ctx, "BaseInit") -- MONKHOSTILITY.inc:42
    do return ctx:exit("TRUE") end -- MONKHOSTILITY.inc:44
end

script.labels["_OnDamage"] = function(ctx)
    -- MONKHOSTILITY.inc:47
    ctx:getParam(0, "g_hObject") -- MONKHOSTILITY.inc:49
    ctx:command("isplayer", "g_hObject, g_bTemp") -- MONKHOSTILITY.inc:50
    if ctx:condition("g_bTemp==TRUE") then -- MONKHOSTILITY.inc:51
        ctx:command("ondamage", "DoNothing") -- MONKHOSTILITY.inc:52
        ctx:command("ondeath", "DoNothing") -- MONKHOSTILITY.inc:53
        mm9.gosub(script, ctx, "TurnHostilityOn") -- MONKHOSTILITY.inc:54
    end -- MONKHOSTILITY.inc:55
    mm9.gosub(script, ctx, "OnDamage") -- MONKHOSTILITY.inc:57
    do return ctx:exit("TRUE") end -- MONKHOSTILITY.inc:59
end

script.labels["_OnDeath"] = function(ctx)
    -- MONKHOSTILITY.inc:62
    ctx:getParam(0, "g_hObject") -- MONKHOSTILITY.inc:64
    ctx:command("isplayer", "g_hObject, g_bTemp") -- MONKHOSTILITY.inc:65
    if ctx:condition("g_bTemp==TRUE") then -- MONKHOSTILITY.inc:66
        ctx:command("ondamage", "DoNothing") -- MONKHOSTILITY.inc:67
        ctx:command("ondeath", "DoNothing") -- MONKHOSTILITY.inc:68
        mm9.gosub(script, ctx, "TurnHostilityOn") -- MONKHOSTILITY.inc:69
    end -- MONKHOSTILITY.inc:70
    mm9.gosub(script, ctx, "OnDeath") -- MONKHOSTILITY.inc:72
    do return ctx:exit("TRUE") end -- MONKHOSTILITY.inc:74
end

script.labels["TurnHostilityOn"] = function(ctx)
    -- MONKHOSTILITY.inc:77
    if ctx:condition("hostile_hMONK_HOSTILITY!=0") then -- MONKHOSTILITY.inc:79
        ctx:command("playsound", "\"sounds\\events\\alarmbell.wav\", DoNothing, 1, 5000, FALSE, 100") -- MONKHOSTILITY.inc:80
        ctx:command("removeobject", "hostile_hMONK_HOSTILITY") -- MONKHOSTILITY.inc:81
    end -- MONKHOSTILITY.inc:82
    do return ctx:exit("TRUE") end -- MONKHOSTILITY.inc:84
end

script.labels["BlockRude"] = function(ctx)
    -- MONKHOSTILITY.inc:87
    do return ctx:exit("TRUE") end -- MONKHOSTILITY.inc:89
end

return script
