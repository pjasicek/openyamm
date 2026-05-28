-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDSUMMONER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "range.inc" }

-- WizardSummoner.scr
-- 01-01-02
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- WIZARDSUMMONER.scr:22
    ctx:getParam(0, "sShooterName") -- WIZARDSUMMONER.scr:24
    ctx:getParam(1, "sLocationName") -- WIZARDSUMMONER.scr:25
    ctx:getParam(2, "sNextName") -- WIZARDSUMMONER.scr:26
    ctx:command("onpoststartworld", "InitWizardSummoner") -- WIZARDSUMMONER.scr:28
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:30
end

script.labels["InitWizardSummoner"] = function(ctx)
    -- WIZARDSUMMONER.scr:33
    ctx:command("addfriend", "Player") -- WIZARDSUMMONER.scr:35
    ctx:command("getobjecthandle", "sShooterName, hShooter") -- WIZARDSUMMONER.scr:37
    ctx:command("getobjecthandle", "sLocationName, hLocation") -- WIZARDSUMMONER.scr:38
    ctx:command("getobjecthandle", "sNextName, hNext") -- WIZARDSUMMONER.scr:39
    ctx:command("faceobject", "hLocation, 180, DoNothing") -- WIZARDSUMMONER.scr:41
    ctx:addTrigger("start", "ConjureSpell") -- WIZARDSUMMONER.scr:43
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:45
end

script.labels["ConjureSpell"] = function(ctx)
    -- WIZARDSUMMONER.scr:48
    ctx:command("playsound", "\"sounds\\ambient\\thunder\\thunderlong.wav\", DoNothing, 1, 500, FALSE, 100") -- WIZARDSUMMONER.scr:50
    ctx:command("playanim", "fidget2, DoNothing") -- WIZARDSUMMONER.scr:51
    ctx:trigger("hShooter", "play") -- WIZARDSUMMONER.scr:52
    ctx:command("wait", "0, 1.5, CastSpell") -- WIZARDSUMMONER.scr:53
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:55
end

script.labels["CastSpell"] = function(ctx)
    -- WIZARDSUMMONER.scr:58
    ctx:command("playanim", "rattack1, DoNothing") -- WIZARDSUMMONER.scr:60
    ctx:command("wait", "0, 1, FinishSpell") -- WIZARDSUMMONER.scr:61
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:63
end

script.labels["FinishSpell"] = function(ctx)
    -- WIZARDSUMMONER.scr:66
    ctx:command("addenemy", "GreaterDemon") -- WIZARDSUMMONER.scr:68
    ctx:command("onfoundtarget", "LinkToBaseRange") -- WIZARDSUMMONER.scr:69
    ctx:trigger("hShooter", "shoot") -- WIZARDSUMMONER.scr:70
    ctx:trigger("hNext", "start") -- WIZARDSUMMONER.scr:71
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:73
end

script.labels["OnDamage"] = function(ctx)
    -- WIZARDSUMMONER.scr:76
    ctx:getParam(0, "g_hObject") -- WIZARDSUMMONER.scr:78
    ctx:command("isplayer", "g_hObject, g_bTemp") -- WIZARDSUMMONER.scr:79
    if ctx:condition("g_bTemp==TRUE") then -- WIZARDSUMMONER.scr:80
        ctx:command("addenemy", "Player") -- WIZARDSUMMONER.scr:81
        ctx:setConsoleNumVar("PLAYER_FRIEND", "FALSE") -- WIZARDSUMMONER.scr:82
    else -- WIZARDSUMMONER.scr:83
        ctx:command("playsound", "\"sounds\\animsounds\\evilsorcerer\\die1.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDSUMMONER.scr:84
        ctx:command("getmyhandle", "hShooter") -- WIZARDSUMMONER.scr:86
        ctx:command("doclientfx", "hShooter, SPELL_BLUEDOTS, FALSE, TRUE") -- WIZARDSUMMONER.scr:87
        ctx:command("getobjecthandle", "SummoningGuy3, hShooter") -- WIZARDSUMMONER.scr:88
        ctx:trigger("hShooter", "finish") -- WIZARDSUMMONER.scr:89
        ctx:command("die", "") -- WIZARDSUMMONER.scr:91
    end -- WIZARDSUMMONER.scr:92
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:94
end

script.labels["OnDeath"] = function(ctx)
    -- WIZARDSUMMONER.scr:97
    ctx:getParam(0, "g_hObject") -- WIZARDSUMMONER.scr:99
    ctx:command("isplayer", "g_hObject, g_bTemp") -- WIZARDSUMMONER.scr:100
    if ctx:condition("g_bTemp==TRUE") then -- WIZARDSUMMONER.scr:101
        ctx:setConsoleNumVar("PLAYER_FRIEND", "FALSE") -- WIZARDSUMMONER.scr:102
    end -- WIZARDSUMMONER.scr:103
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:105
end

script.labels["LinkToBaseRange"] = function(ctx)
    -- WIZARDSUMMONER.scr:108
    mm9.gosub(script, ctx, "BaseInit") -- WIZARDSUMMONER.scr:110
    mm9.gosub(script, ctx, "RangeInit") -- WIZARDSUMMONER.scr:111
    ctx:command("g_rangeattacktype", "= RANGE_TYPE2") -- WIZARDSUMMONER.scr:113
    mm9.gosub(script, ctx, "SetupRangeAttackType") -- WIZARDSUMMONER.scr:114
    mm9.gosub(script, ctx, "StartRangeAttack") -- WIZARDSUMMONER.scr:115
    ctx:command("ondamage", "OnDamage") -- WIZARDSUMMONER.scr:117
    do return ctx:exit("TRUE") end -- WIZARDSUMMONER.scr:119
end

return script
