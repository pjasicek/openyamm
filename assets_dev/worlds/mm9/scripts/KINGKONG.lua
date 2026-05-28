-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "KINGKONG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 19, path = "baseMelee.inc" }

-- KingKong.scr
-- by SJR
-- 09-08-01
-- Purpose: Creature busting
-- out of his cage etc
-- ScriptParams are:
-- p0 = Name of Destructable brush
-- Triggers:
-- "ForceBreak" = smash through brush and attack
-- "ForceFall"  = fall through brush and initbase
-- "ForceAttack"= runs to player and starts attack
-- edited by Bones -- 6/10/03
-- TELP Patch 1.3 -- will work reliably with saves and minisaves
script.labels["Main"] = function(ctx)
    -- KINGKONG.scr:27
    ctx:getParam(0, "sCageName") -- KINGKONG.scr:29
    ctx:getParam(1, "ANIM_NAME") -- KINGKONG.scr:30
    ctx:command("onpoststartworld", "InitKingKong") -- KINGKONG.scr:32
    do return ctx:exit("TRUE") end -- KINGKONG.scr:34
end

script.labels["InitKingKong"] = function(ctx)
    -- KINGKONG.scr:37
    ctx:command("getobjecthandle", "sCageName, hCage") -- KINGKONG.scr:39
    ctx:addTrigger("ForceBreak", "RushCage") -- KINGKONG.scr:41
    ctx:addTrigger("ForceFall", "FallThrough") -- KINGKONG.scr:42
    ctx:addTrigger("ForceAttack", "TurnOff") -- KINGKONG.scr:43
    if ctx:condition("ANIM_NAME!=\"\"") then -- KINGKONG.scr:45
        ctx:command("loopanim", "ANIM_NAME, 0") -- KINGKONG.scr:46
    end -- KINGKONG.scr:47
    do return ctx:exit("TRUE") end -- KINGKONG.scr:49
end

script.labels["RushCage"] = function(ctx)
    -- KINGKONG.scr:52
    -- play angry sound, break through wall
    ctx:command("playsound", "\"sounds\\animsounds\\dragonredrattack3.wav\", DoNothing, 1, 500, FALSE, 100") -- KINGKONG.scr:55
    mm9.gosub(script, ctx, "BreakCage") -- KINGKONG.scr:57
    do return ctx:exit("TRUE") end -- KINGKONG.scr:59
end

script.labels["BreakCage"] = function(ctx)
    -- KINGKONG.scr:62
    -- trigger-destroy the wall
    ctx:command("getobjecthandle", "sCageName, hCage") -- KINGKONG.scr:65
    if ctx:condition("hCage!=NULL") then -- KINGKONG.scr:66
        ctx:trigger("hCage", "destroy") -- KINGKONG.scr:67
    end -- KINGKONG.scr:68
    ctx:command("playanim", "hattack1, turnoff") -- KINGKONG.scr:70
    mm9.gosub(script, ctx, "TurnOff") -- KINGKONG.scr:72
    do return ctx:exit("TRUE") end -- KINGKONG.scr:74
end

script.labels["FallThrough"] = function(ctx)
    -- KINGKONG.scr:77
    -- trigger-destroy the floor
    ctx:command("getobjecthandle", "sCageName, hCage") -- KINGKONG.scr:80
    if ctx:condition("hCage!=NULL") then -- KINGKONG.scr:81
        ctx:trigger("hCage", "destroy") -- KINGKONG.scr:82
    end -- KINGKONG.scr:83
    mm9.gosub(script, ctx, "TurnOff") -- KINGKONG.scr:85
    do return ctx:exit("TRUE") end -- KINGKONG.scr:87
end

script.labels["TurnOff"] = function(ctx)
    -- KINGKONG.scr:90
    -- remove trigs, hunt player
    ctx:command("removetrigger", "ForceBreak") -- KINGKONG.scr:93
    ctx:command("removetrigger", "ForceFall") -- KINGKONG.scr:94
    ctx:command("removetrigger", "ForceAttack") -- KINGKONG.scr:95
    mm9.gosub(script, ctx, "BaseInit") -- KINGKONG.scr:97
    ctx:command("getplayerhandle", "g_hTarget") -- KINGKONG.scr:98
    mm9.gosub(script, ctx, "SetupTarget") -- KINGKONG.scr:99
    mm9.gosub(script, ctx, "AggressiveStart") -- KINGKONG.scr:100
    do return ctx:exit("TRUE") end -- KINGKONG.scr:102
end

return script
