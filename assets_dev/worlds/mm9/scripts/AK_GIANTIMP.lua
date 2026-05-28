-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AK_GIANTIMP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "flags.inc" }

-- AK_GiantImp.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- AK_GIANTIMP.scr:12
    ctx:command("oncachefiles", "CacheFiles") -- AK_GIANTIMP.scr:14
    ctx:command("getmyhandle", "g_hMyObject") -- AK_GIANTIMP.scr:16
    ctx:command("setstat", "g_hMyObject, gravity, FALSE") -- AK_GIANTIMP.scr:18
    ctx:command("clearflag", "g_hMyObject, FLAG_SOLID") -- AK_GIANTIMP.scr:19
    ctx:command("clearflag", "g_hMyObject, FLAG_VISIBLE") -- AK_GIANTIMP.scr:20
    ctx:addTrigger("appear", "Appear") -- AK_GIANTIMP.scr:22
    mm9.gosub(script, ctx, "IncreaseStats") -- AK_GIANTIMP.scr:24
    do return ctx:exit("TRUE") end -- AK_GIANTIMP.scr:26
end

script.labels["CacheFiles"] = function(ctx)
    -- AK_GIANTIMP.scr:29
    ctx:command("cacheclientfx", "SPELL_BLACKSMOKE") -- AK_GIANTIMP.scr:31
    ctx:command("cachesound", "\"sounds\\animsounds\\gezzampt\\aware.wav\"") -- AK_GIANTIMP.scr:32
    do return ctx:exit("TRUE") end -- AK_GIANTIMP.scr:34
end

script.labels["Appear"] = function(ctx)
    -- AK_GIANTIMP.scr:37
    ctx:command("playsound", "\"sounds\\animsounds\\gezzampt\\aware.wav\", StartScene, 1, 1000, 0, 100") -- AK_GIANTIMP.scr:39
    do return ctx:exit("TRUE") end -- AK_GIANTIMP.scr:41
end

script.labels["StartScene"] = function(ctx)
    -- AK_GIANTIMP.scr:44
    ctx:command("doclientfx", "g_hMyObject, SPELL_BLACKSMOKE, TRUE, TRUE") -- AK_GIANTIMP.scr:46
    ctx:command("setflag", "g_hMyObject, FLAG_SOLID") -- AK_GIANTIMP.scr:48
    ctx:command("setflag", "g_hMyObject, FLAG_VISIBLE") -- AK_GIANTIMP.scr:49
    ctx:command("setstat", "g_hMyObject, Gravity, TRUE") -- AK_GIANTIMP.scr:50
    mm9.gosub(script, ctx, "BaseInit") -- AK_GIANTIMP.scr:52
    ctx:command("getplayerhandle", "g_hTarget") -- AK_GIANTIMP.scr:53
    mm9.gosub(script, ctx, "SetupTarget") -- AK_GIANTIMP.scr:54
    mm9.gosub(script, ctx, "AggressiveStart") -- AK_GIANTIMP.scr:55
    do return ctx:exit("TRUE") end -- AK_GIANTIMP.scr:57
end

script.labels["IncreaseStats"] = function(ctx)
    -- AK_GIANTIMP.scr:60
    ctx:command("setstat", "g_hMyObject, HitPoints, 100") -- AK_GIANTIMP.scr:62
    ctx:command("setstat", "g_hMyObject, AC, 15") -- AK_GIANTIMP.scr:63
    do return ctx:exit("TRUE") end -- AK_GIANTIMP.scr:65
end

return script
