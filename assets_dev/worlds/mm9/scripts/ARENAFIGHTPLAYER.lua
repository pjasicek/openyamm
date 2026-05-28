-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENAFIGHTPLAYER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- ArenaFightPlayer.scr
-- timmy
-- handles arena monsters fighting player stuff
script.labels["GetOutThere"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:16
    ctx:command("getobjecthandle", "marker2 g_hobject") -- ARENAFIGHTPLAYER.scr:18
    ctx:command("runto", "g_hobject 128 OnArrive") -- ARENAFIGHTPLAYER.scr:19
    ctx:command("onfoundtarget", "OnFoundTarget") -- ARENAFIGHTPLAYER.scr:20
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:22
end

script.labels["Startup"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:25
    ctx:command("getstat", "g_hmyobject HitPoints g_ntemp") -- ARENAFIGHTPLAYER.scr:28
    ctx:command("nminhp", "= g_ntemp * .7") -- ARENAFIGHTPLAYER.scr:29
    ctx:command("nmaxhp", "= g_ntemp * 1.5") -- ARENAFIGHTPLAYER.scr:30
    ctx:command("getrandomint", "nMinHP, nMaxHP, nHitPoints") -- ARENAFIGHTPLAYER.scr:31
    ctx:command("setstat", "g_hmyobject Hitpoints nHitPoints") -- ARENAFIGHTPLAYER.scr:32
    ctx:command("setstat", "g_hmyobject GaveTreasure TRUE") -- ARENAFIGHTPLAYER.scr:33
    ctx:command("getobjecthandle", "RotatingDoor2,g_hObject") -- ARENAFIGHTPLAYER.scr:35
    ctx:trigger("g_hObject", "Use") -- ARENAFIGHTPLAYER.scr:36
    ctx:command("getobjecthandle", "RotatingDoor4,g_hObject") -- ARENAFIGHTPLAYER.scr:38
    ctx:trigger("g_hObject", "Use") -- ARENAFIGHTPLAYER.scr:39
    ctx:command("wait", "24,0.2,GetOutThere") -- ARENAFIGHTPLAYER.scr:41
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:43
end

script.labels["OnArrive"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:46
    ctx:command("getplayerhandle", "g_hObject") -- ARENAFIGHTPLAYER.scr:50
    ctx:command("target", "g_hObject,TRUE") -- ARENAFIGHTPLAYER.scr:52
    ctx:command("getstatstr", "g_hMyObject,ScriptName,sScript") -- ARENAFIGHTPLAYER.scr:54
    ctx:command("runscript", "sScript") -- ARENAFIGHTPLAYER.scr:55
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:56
end

script.labels["OnFoundTarget"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:59
    do return mm9.gotoLabel(script, ctx, "OnArrive") end -- ARENAFIGHTPLAYER.scr:61
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:63
end

script.labels["WaitForSignal"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:66
    ctx:getConsoleNumVar("WaitingForPlayer", "bWaitingForPlayer") -- ARENAFIGHTPLAYER.scr:70
    if ctx:condition("bWaitingForPlayer==FALSE") then -- ARENAFIGHTPLAYER.scr:72
        do return mm9.gotoLabel(script, ctx, "Startup") end -- ARENAFIGHTPLAYER.scr:73
        do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:74
    end -- ARENAFIGHTPLAYER.scr:75
    ctx:command("wait", "24,1.5,WaitForSignal") -- ARENAFIGHTPLAYER.scr:77
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:79
end

script.labels["Main"] = function(ctx)
    -- ARENAFIGHTPLAYER.scr:82
    ctx:command("getmyhandle", "g_hMyObject") -- ARENAFIGHTPLAYER.scr:85
    ctx:command("addfriend", "AIBase") -- ARENAFIGHTPLAYER.scr:87
    ctx:command("addenemy", "Player") -- ARENAFIGHTPLAYER.scr:88
    -- traceon
    -- Don't Forget to Delete this!
    ctx:giveKey(1011) -- ARENAFIGHTPLAYER.scr:92
    ctx:command("setpropstring", "DeathTriggerTarget,ArenaFight") -- ARENAFIGHTPLAYER.scr:94
    ctx:command("setpropstring", "DeathTriggerMessage,Dead") -- ARENAFIGHTPLAYER.scr:95
    ctx:command("getstatstr", "g_hmyobject,ScriptName,g_sTemp") -- ARENAFIGHTPLAYER.scr:97
    ctx:command("cachescript", "g_sTemp") -- ARENAFIGHTPLAYER.scr:98
    mm9.gosub(script, ctx, "WaitForSignal") -- ARENAFIGHTPLAYER.scr:100
    do return ctx:exit("") end -- ARENAFIGHTPLAYER.scr:104
end

return script
