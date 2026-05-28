-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAMCHASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "njam1000.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "basedoor.inc" }

-- NjamChase.scr
-- By Timmy
-- 1/16
-- Manager for Njam's chasing stuff
-- flag variables
script.labels["OnChase"] = function(ctx)
    -- NJAMCHASE.scr:22
    if ctx:hasKey(470) then -- NJAMCHASE.scr:27-28
        do return ctx:exit("") end -- NJAMCHASE.scr:29
    end -- NJAMCHASE.scr:30
    if ctx:hasKey(108) then -- NJAMCHASE.scr:33-34
        ctx:command("getobjecthandle", "Njamdoor g_hobject") -- NJAMCHASE.scr:35
        ctx:trigger("g_hobject", "Unlock") -- NJAMCHASE.scr:36
        -- trigger door to unlock and him to go through it.
        ctx:giveKey(470) -- NJAMCHASE.scr:38
        ctx:giveExp(226000) -- NJAMCHASE.scr:39
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMCHASE.scr:40
        mm9.gosub(script, ctx, "Chase") -- NJAMCHASE.scr:41
        do return ctx:exit("") end -- NJAMCHASE.scr:42
    end -- NJAMCHASE.scr:43
    do return ctx:exit("") end -- NJAMCHASE.scr:46
end

script.labels["Chase"] = function(ctx)
    -- NJAMCHASE.scr:48
    ctx:command("getplayerhandle", "g_hplayer") -- NJAMCHASE.scr:52
    ctx:command("target", "g_hplayer") -- NJAMCHASE.scr:53
    ctx:command("addenemy", "player") -- NJAMCHASE.scr:54
    mm9.gosub(script, ctx, "BaseInit") -- NJAMCHASE.scr:56
    do return ctx:exit("") end -- NJAMCHASE.scr:57
end

script.labels["Init"] = function(ctx)
    -- NJAMCHASE.scr:60
    if ctx:hasKey(470) then -- NJAMCHASE.scr:64-65
        ctx:command("getmyhandle", "g_hobject") -- NJAMCHASE.scr:66
        ctx:command("removeobject", "g_hobject") -- NJAMCHASE.scr:67
    else -- NJAMCHASE.scr:68
        mm9.gosub(script, ctx, "init") -- NJAMCHASE.scr:69
    end -- NJAMCHASE.scr:70
    do return ctx:exit("") end -- NJAMCHASE.scr:72
end

script.labels["Main"] = function(ctx)
    -- NJAMCHASE.scr:75
    -- TraceOn ;delete me!!
    ctx:addTrigger("Chase", "OnChase") -- NJAMCHASE.scr:79
    ctx:command("ondamage", "Chase") -- NJAMCHASE.scr:80
    -- Gosub Init
    mm9.gosub(script, ctx, "BaseDoorInit") -- NJAMCHASE.scr:82
    ctx:command("onpoststartworld", "Init") -- NJAMCHASE.scr:83
    ctx:command("onpostminisaveload", "Init") -- NJAMCHASE.scr:84
    ctx:command("onpostsaveload", "Init") -- NJAMCHASE.scr:85
    ctx:command("wait", "1 .1 Init") -- NJAMCHASE.scr:86
    do return ctx:exit("") end -- NJAMCHASE.scr:87
end

return script
