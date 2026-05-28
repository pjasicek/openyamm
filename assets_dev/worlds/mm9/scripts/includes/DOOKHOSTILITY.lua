-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOOKHOSTILITY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "baseMelee.inc" }

-- DookHostility.scr
-- by SJR
-- 01-01-02
-- Purpose:refrain from attacking player
-- until they go through the tunnel
script.labels["InitDookHostility"] = function(ctx)
    -- DOOKHOSTILITY.inc:13
    ctx:command("addfriend", "Player") -- DOOKHOSTILITY.inc:15
    ctx:command("getobjecthandle", "DOOK_HOSTILITY, hostile_hDOOK_HOSTILITY") -- DOOKHOSTILITY.inc:17
    if ctx:condition("hostile_hDOOK_HOSTILITY!=0") then -- DOOKHOSTILITY.inc:18
        ctx:command("createobjectlink", "hostile_hDOOK_HOSTILITY") -- DOOKHOSTILITY.inc:19
        ctx:command("onobjectlinkbroken", "BecomeHostile") -- DOOKHOSTILITY.inc:20
        ctx:command("ondamage", "_OnDamage") -- DOOKHOSTILITY.inc:22
        ctx:command("ondeath", "_OnDeath") -- DOOKHOSTILITY.inc:23
        ctx:command("onalert", "_OnDamage") -- DOOKHOSTILITY.inc:24
    else -- DOOKHOSTILITY.inc:25
        mm9.gosub(script, ctx, "BecomeHostile") -- DOOKHOSTILITY.inc:26
    end -- DOOKHOSTILITY.inc:27
    do return ctx:exit("TRUE") end -- DOOKHOSTILITY.inc:29
end

script.labels["BecomeHostile"] = function(ctx)
    -- DOOKHOSTILITY.inc:32
    ctx:command("hostile_hdook_hostility", "= NULL") -- DOOKHOSTILITY.inc:34
    ctx:addTrigger("use", "BlockRude") -- DOOKHOSTILITY.inc:36
    ctx:command("addenemy", "Player") -- DOOKHOSTILITY.inc:38
    mm9.gosub(script, ctx, "BaseInit") -- DOOKHOSTILITY.inc:40
    do return ctx:exit("TRUE") end -- DOOKHOSTILITY.inc:42
end

script.labels["_OnDamage"] = function(ctx)
    -- DOOKHOSTILITY.inc:45
    ctx:getParam(0, "g_hPlayer") -- DOOKHOSTILITY.inc:47
    ctx:command("isplayer", "g_hPlayer, g_bTemp") -- DOOKHOSTILITY.inc:48
    if ctx:condition("g_bTemp==TRUE") then -- DOOKHOSTILITY.inc:49
        ctx:command("ondamage", "DoNothing") -- DOOKHOSTILITY.inc:50
        ctx:command("ondeath", "DoNothing") -- DOOKHOSTILITY.inc:51
        mm9.gosub(script, ctx, "TurnHostilityOn") -- DOOKHOSTILITY.inc:52
    end -- DOOKHOSTILITY.inc:53
    mm9.gosub(script, ctx, "OnDamage") -- DOOKHOSTILITY.inc:55
    do return ctx:exit("TRUE") end -- DOOKHOSTILITY.inc:57
end

script.labels["_OnDeath"] = function(ctx)
    -- DOOKHOSTILITY.inc:60
    ctx:getParam(0, "g_hPlayer") -- DOOKHOSTILITY.inc:62
    ctx:command("isplayer", "g_hPlayer, g_bTemp") -- DOOKHOSTILITY.inc:63
    if ctx:condition("g_bTemp==TRUE") then -- DOOKHOSTILITY.inc:64
        ctx:command("ondamage", "DoNothing") -- DOOKHOSTILITY.inc:65
        ctx:command("ondeath", "DoNothing") -- DOOKHOSTILITY.inc:66
        mm9.gosub(script, ctx, "TurnHostilityOn") -- DOOKHOSTILITY.inc:68
    end -- DOOKHOSTILITY.inc:69
    mm9.gosub(script, ctx, "OnDeath") -- DOOKHOSTILITY.inc:71
    do return ctx:exit("TRUE") end -- DOOKHOSTILITY.inc:73
end

script.labels["TurnHostilityOn"] = function(ctx)
    -- DOOKHOSTILITY.inc:76
    if ctx:condition("hostile_hDOOK_HOSTILITY!=0") then -- DOOKHOSTILITY.inc:78
        ctx:command("playsound", "\"sounds\\events\\alarmbell.wav\", DoNothing, 1, 5000, FALSE, 100") -- DOOKHOSTILITY.inc:79
        ctx:command("removeobject", "hostile_hDOOK_HOSTILITY") -- DOOKHOSTILITY.inc:80
    end -- DOOKHOSTILITY.inc:81
    do return ctx:exit("TRUE") end -- DOOKHOSTILITY.inc:83
end

script.labels["BlockRude"] = function(ctx)
    -- DOOKHOSTILITY.inc:86
    do return ctx:exit("TRUE") end -- DOOKHOSTILITY.inc:88
end

return script
