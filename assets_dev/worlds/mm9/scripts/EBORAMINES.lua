-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EBORAMINES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "flags.inc" }

-- EboraMines.scr
-- By L. Dean Gibson II
-- Ebora busts out of the mines!
-- edited by Bones 5/26/03
-- TELP Patch 1.3 -- Prevents lockup if in TB mode.
script.labels["FreeAtLast"] = function(ctx)
    -- EBORAMINES.scr:22
    -- turn letterbox on
    -- turn our camera on
    -- look around
    -- onarrival kill the whole thing
    -- TraceOn
    ctx:command("getobjecthandle", "EboraCam g_hObject") -- EBORAMINES.scr:31
    ctx:command("letterbox", "1") -- EBORAMINES.scr:33
    ctx:trigger("g_hObject", "On") -- EBORAMINES.scr:34
    -- turn to target point
    ctx:command("faceobject", "g_hObject, 180") -- EBORAMINES.scr:37
    ctx:command("playanim", "fidget2") -- EBORAMINES.scr:40
    ctx:command("wait", "1 3 OnFidgetDone") -- EBORAMINES.scr:41
    do return ctx:exit("") end -- EBORAMINES.scr:43
end

script.labels["OnFidgetDone"] = function(ctx)
    -- EBORAMINES.scr:47
    ctx:command("playanim", "Taunt") -- EBORAMINES.scr:50
    ctx:command("rollovertext", "8, 2, 7000, 3000, 100, 500") -- EBORAMINES.scr:51
    ctx:command("wait", "1 5 Disappear") -- EBORAMINES.scr:52
    do return ctx:exit("") end -- EBORAMINES.scr:54
end

script.labels["Disappear"] = function(ctx)
    -- EBORAMINES.scr:57
    ctx:command("playanim", "Rattack1") -- EBORAMINES.scr:60
    ctx:command("wait", "1 2 SpellDone") -- EBORAMINES.scr:61
    do return ctx:exit("") end -- EBORAMINES.scr:63
end

script.labels["SpellDone"] = function(ctx)
    -- EBORAMINES.scr:66
    -- play sound and vanish
    ctx:command("getmyhandle", "g_hMyObject") -- EBORAMINES.scr:69
    ctx:command("doclientfx", "g_hMyObject, SPELL_COLUMNOFFIRE, FALSE, TRUE") -- EBORAMINES.scr:71
    ctx:command("playsound", "\"sounds\\spells\\column03.wav\", DoNothing, 1, 1000, FALSE, 100") -- EBORAMINES.scr:72
    ctx:command("wait", "1 3 EboraDone") -- EBORAMINES.scr:75
    do return ctx:exit("") end -- EBORAMINES.scr:76
end

script.labels["EboraDone"] = function(ctx)
    -- EBORAMINES.scr:81
    ctx:command("getmyhandle", "g_hMyObject") -- EBORAMINES.scr:83
    ctx:command("removeobject", "g_hMyObject") -- EBORAMINES.scr:85
    ctx:command("letterbox", "0") -- EBORAMINES.scr:86
    ctx:command("getobjecthandle", "EboraCam g_hObject") -- EBORAMINES.scr:87
    ctx:trigger("g_hObject", "Off") -- EBORAMINES.scr:88
    do return ctx:exit("") end -- EBORAMINES.scr:90
end

script.labels["Main"] = function(ctx)
    -- EBORAMINES.scr:95
    ctx:addTrigger("FreeAtLast", "FreeAtLast") -- EBORAMINES.scr:98
    ctx:command("ondamage", "FreeAtLast") -- EBORAMINES.scr:99
    ctx:command("setidle", "") -- EBORAMINES.scr:100
    do return ctx:exit("") end -- EBORAMINES.scr:102
end

script.labels["FreeAtLast"] = function(ctx)
    -- EBORAMINES.scr:105
    -- overloaded -- Bones
    ctx:command("isturnbased", "g_nTemp") -- EBORAMINES.scr:109
    if ctx:condition("g_nTemp == TRUE") then -- EBORAMINES.scr:110
        ctx:command("screenfadeout", "1") -- EBORAMINES.scr:111
        ctx:command("rollovertext", "18 0") -- EBORAMINES.scr:112
        ctx:command("wait", "0 1 FreeAtLast") -- EBORAMINES.scr:113
        do return ctx:exit("") end -- EBORAMINES.scr:114
    end -- EBORAMINES.scr:115
    ctx:command("screenfadein", "1") -- EBORAMINES.scr:117
    do return mm9.gotoLabel(script, ctx, "FreeAtLast") end -- EBORAMINES.scr:118
end

return script
