-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOOKBATTLER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "baseMelee.inc" }

-- TO DO:
-- the combat has a problem with falling
-- off of the dooks castle bridges
-- DookBattler.scr
-- by SJR
-- Purpose:participate in the dooks
-- castle bridge fight
script.labels["Main"] = function(ctx)
    -- DOOKBATTLER.scr:13
    -- OnPostStartWorld InitDookBattler
    ctx:command("wait", "0, 5, InitDookBattler") -- DOOKBATTLER.scr:16
    do return ctx:exit("TRUE") end -- DOOKBATTLER.scr:18
end

script.labels["InitDookBattler"] = function(ctx)
    -- DOOKBATTLER.scr:21
    ctx:command("addfriend", "AIBase") -- DOOKBATTLER.scr:23
    ctx:command("addfriend", "Player") -- DOOKBATTLER.scr:24
    ctx:addTrigger("on", "SetupEnemies") -- DOOKBATTLER.scr:26
    ctx:command("getmyhandle", "g_hMyObject") -- DOOKBATTLER.scr:28
    ctx:command("setstat", "g_hMyObject, HitPoints, 700") -- DOOKBATTLER.scr:29
    mm9.gosub(script, ctx, "BaseInit") -- DOOKBATTLER.scr:31
    -- disable strafing, otherwise we'll fall off
    ctx:command("g_nevadechance", "= 0") -- DOOKBATTLER.scr:34
    ctx:command("g_nmaxevadedist", "= 0") -- DOOKBATTLER.scr:35
    ctx:command("g_nstrafeattackpct", "= 0") -- DOOKBATTLER.scr:36
    do return ctx:exit("TRUE") end -- DOOKBATTLER.scr:38
end

script.labels["SetupEnemies"] = function(ctx)
    -- DOOKBATTLER.scr:41
    ctx:command("addenemy", "AIBase") -- DOOKBATTLER.scr:43
    ctx:command("ontargetdead", "OnTargetDead") -- DOOKBATTLER.scr:45
    ctx:command("ondamage", "OnDamage") -- DOOKBATTLER.scr:46
    do return ctx:exit("TRUE") end -- DOOKBATTLER.scr:48
end

script.labels["OnTargetDead"] = function(ctx)
    -- DOOKBATTLER.scr:51
    ctx:command("addenemy", "Player") -- DOOKBATTLER.scr:53
    mm9.gosub(script, ctx, "OnTargetDead") -- DOOKBATTLER.scr:54
    do return ctx:exit("TRUE") end -- DOOKBATTLER.scr:56
end

script.labels["OnDamage"] = function(ctx)
    -- DOOKBATTLER.scr:59
    ctx:command("getliquidcontainer", "g_hMyObject, g_hObject") -- DOOKBATTLER.scr:61
    if ctx:condition("g_hObject!=0") then -- DOOKBATTLER.scr:62
        ctx:command("removeobject", "g_hMyObject") -- DOOKBATTLER.scr:63
    else -- DOOKBATTLER.scr:64
        ctx:command("addenemy", "Player") -- DOOKBATTLER.scr:65
        ctx:getParam(0, "g_hTarget") -- DOOKBATTLER.scr:66
        mm9.gosub(script, ctx, "OnDamage") -- DOOKBATTLER.scr:67
    end -- DOOKBATTLER.scr:68
    do return ctx:exit("TRUE") end -- DOOKBATTLER.scr:70
end

return script
