-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AK_IMPGATE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- AK_ImpGate.scr
-- by SJR
-- Purpose:spawn certain number of imps
-- and destroy self when done.
-- anskrammainline.scr passes out key.
-- Params:
-- p0 = creature name
-- p1 = number to spawn
-- p2 = anskrammainline.scr name
-- p3 = fire object to turn off
script.labels["Main"] = function(ctx)
    -- AK_IMPGATE.scr:39
    ctx:getParam(0, "sCreatureName") -- AK_IMPGATE.scr:41
    ctx:getParam(1, "nQuantity") -- AK_IMPGATE.scr:42
    ctx:getParam(2, "sSignalName") -- AK_IMPGATE.scr:43
    ctx:getParam(3, "sFireName") -- AK_IMPGATE.scr:44
    ctx:command("onpoststartworld", "InitImpGate") -- AK_IMPGATE.scr:46
    ctx:command("onpostminisaveload", "InitImpGate") -- AK_IMPGATE.scr:47
    do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:49
end

script.labels["InitKey"] = function(ctx)
    -- AK_IMPGATE.scr:54
    if ctx:condition("sFireName==ImpGateFire0") then -- AK_IMPGATE.scr:57
        ctx:command("nkey", "= 510") -- AK_IMPGATE.scr:58
        do return ctx:exit("") end -- AK_IMPGATE.scr:59
    end -- AK_IMPGATE.scr:60
    if ctx:condition("sFireName==ImpGateFire1") then -- AK_IMPGATE.scr:62
        ctx:command("nkey", "= 511") -- AK_IMPGATE.scr:63
        do return ctx:exit("") end -- AK_IMPGATE.scr:64
    end -- AK_IMPGATE.scr:65
    if ctx:condition("sFireName==ImpGateFire2") then -- AK_IMPGATE.scr:67
        ctx:command("nkey", "= 512") -- AK_IMPGATE.scr:68
        do return ctx:exit("") end -- AK_IMPGATE.scr:69
    end -- AK_IMPGATE.scr:70
    if ctx:condition("sFireName==ImpGateFire3") then -- AK_IMPGATE.scr:72
        ctx:command("nkey", "= 513") -- AK_IMPGATE.scr:73
        do return ctx:exit("") end -- AK_IMPGATE.scr:74
    end -- AK_IMPGATE.scr:75
    if ctx:condition("sFireName==ImpGateFire4") then -- AK_IMPGATE.scr:77
        ctx:command("nkey", "= 514") -- AK_IMPGATE.scr:78
        do return ctx:exit("") end -- AK_IMPGATE.scr:79
    end -- AK_IMPGATE.scr:80
    if ctx:condition("sFireName==ImpGateFire5") then -- AK_IMPGATE.scr:82
        ctx:command("nkey", "= 515") -- AK_IMPGATE.scr:83
        do return ctx:exit("") end -- AK_IMPGATE.scr:84
    end -- AK_IMPGATE.scr:85
    if ctx:condition("sFireName==ImpGateFire6") then -- AK_IMPGATE.scr:87
        ctx:command("nkey", "= 516") -- AK_IMPGATE.scr:88
        do return ctx:exit("") end -- AK_IMPGATE.scr:89
    end -- AK_IMPGATE.scr:90
    if ctx:condition("sFireName==ImpGateFire7") then -- AK_IMPGATE.scr:92
        ctx:command("nkey", "= 517") -- AK_IMPGATE.scr:93
        do return ctx:exit("") end -- AK_IMPGATE.scr:94
    end -- AK_IMPGATE.scr:95
    do return ctx:exit("") end -- AK_IMPGATE.scr:97
end

script.labels["ConsoleCheck"] = function(ctx)
    -- AK_IMPGATE.scr:100
    ctx:command("set", "g_nCounter, 0") -- AK_IMPGATE.scr:103
    if ctx:hasKey(510) then -- AK_IMPGATE.scr:105-106
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:107
    end -- AK_IMPGATE.scr:108
    if ctx:hasKey(511) then -- AK_IMPGATE.scr:110-111
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:112
    end -- AK_IMPGATE.scr:113
    if ctx:hasKey(512) then -- AK_IMPGATE.scr:115-116
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:117
    end -- AK_IMPGATE.scr:118
    if ctx:hasKey(513) then -- AK_IMPGATE.scr:120-121
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:122
    end -- AK_IMPGATE.scr:123
    if ctx:hasKey(514) then -- AK_IMPGATE.scr:125-126
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:127
    end -- AK_IMPGATE.scr:128
    if ctx:hasKey(515) then -- AK_IMPGATE.scr:130-131
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:132
    end -- AK_IMPGATE.scr:133
    if ctx:hasKey(516) then -- AK_IMPGATE.scr:135-136
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:137
    end -- AK_IMPGATE.scr:138
    if ctx:hasKey(517) then -- AK_IMPGATE.scr:140-141
        ctx:command("add", "g_nCounter, 1") -- AK_IMPGATE.scr:142
    end -- AK_IMPGATE.scr:143
    ctx:setConsoleNumVar("AK_IMP_TOTAL", "g_nCounter") -- AK_IMPGATE.scr:145
    do return ctx:exit("") end -- AK_IMPGATE.scr:147
end

script.labels["InitImpGate"] = function(ctx)
    -- AK_IMPGATE.scr:151
    mm9.gosub(script, ctx, "InitKey") -- AK_IMPGATE.scr:154
    ctx:hasKey("nKey", "bHasKey") -- AK_IMPGATE.scr:156
    if ctx:condition("bHasKey==TRUE") then -- AK_IMPGATE.scr:157
        ctx:command("getobjecthandle", "sFireName, hMe") -- AK_IMPGATE.scr:158
        if ctx:condition("hMe!=0") then -- AK_IMPGATE.scr:159
            ctx:command("removeobject", "hMe") -- AK_IMPGATE.scr:160
        end -- AK_IMPGATE.scr:161
        do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:162
    end -- AK_IMPGATE.scr:163
    if ctx:condition("nQuantity>5") then -- AK_IMPGATE.scr:165
        ctx:command("nquantity", "= 5") -- AK_IMPGATE.scr:166
    else -- AK_IMPGATE.scr:167
        if ctx:condition("nQuantity<1") then -- AK_IMPGATE.scr:168
            ctx:command("nquantity", "= 1") -- AK_IMPGATE.scr:169
        end -- AK_IMPGATE.scr:170
    end -- AK_IMPGATE.scr:171
    mm9.gosub(script, ctx, "ConsoleCheck") -- AK_IMPGATE.scr:174
    ctx:command("getmyhandle", "hMe") -- AK_IMPGATE.scr:176
    ctx:command("getpos", "hMe, xMe, yMe, zMe") -- AK_IMPGATE.scr:177
    ctx:addTrigger("spawn", "Spawn") -- AK_IMPGATE.scr:179
    ctx:command("ontargetdead", "Respawn") -- AK_IMPGATE.scr:180
    do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:182
end

script.labels["Respawn"] = function(ctx)
    -- AK_IMPGATE.scr:185
    -- keep an eye on creature, respawn if dead
    ctx:command("target", "NULL") -- AK_IMPGATE.scr:188
    ctx:command("hcreature", "= NULL") -- AK_IMPGATE.scr:189
    ctx:command("wait", "0, 3, Spawn") -- AK_IMPGATE.scr:190
    do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:192
end

script.labels["Spawn"] = function(ctx)
    -- AK_IMPGATE.scr:195
    -- keep an eye on creature, respawn if dead
    if ctx:condition("nQuantity<=0") then -- AK_IMPGATE.scr:198
        mm9.gosub(script, ctx, "Terminate") -- AK_IMPGATE.scr:199
        do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:200
    end -- AK_IMPGATE.scr:201
    ctx:command("nquantity", "= nQuantity - 1") -- AK_IMPGATE.scr:203
    ctx:command("spawn_param", "= sCreatureName + sScriptName") -- AK_IMPGATE.scr:204
    ctx:command("spawn", "hCreature, xMe, yMe, zMe, SPAWN_PARAM") -- AK_IMPGATE.scr:205
    if ctx:condition("hCreature!=0") then -- AK_IMPGATE.scr:207
        ctx:command("doclientfx", "hCreature, SPELL_BLUEFIRE, FALSE, TRUE") -- AK_IMPGATE.scr:208
        ctx:command("target", "hCreature") -- AK_IMPGATE.scr:209
    end -- AK_IMPGATE.scr:210
    do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:212
end

script.labels["Terminate"] = function(ctx)
    -- AK_IMPGATE.scr:215
    -- turn off, signal keygiver, disable stuff
    ctx:giveKey("nKey") -- AK_IMPGATE.scr:219
    ctx:getConsoleNumVar("AK_IMP_TOTAL", "xMe") -- AK_IMPGATE.scr:221
    ctx:command("xme", "= xMe + 1") -- AK_IMPGATE.scr:222
    ctx:command("hcreature", "= NULL") -- AK_IMPGATE.scr:223
    ctx:command("target", "NULL") -- AK_IMPGATE.scr:224
    if ctx:condition("xMe==NUM_GATES") then -- AK_IMPGATE.scr:226
        ctx:command("getobjecthandle", "sSignalName, hCreature") -- AK_IMPGATE.scr:227
        ctx:trigger("hCreature", "use") -- AK_IMPGATE.scr:228
        ctx:command("getobjecthandle", "TriggerGiantImp, hCreature") -- AK_IMPGATE.scr:229
        ctx:trigger("hCreature", "on") -- AK_IMPGATE.scr:230
        ctx:command("hcreature", "= NULL") -- AK_IMPGATE.scr:231
    else -- AK_IMPGATE.scr:232
        ctx:setConsoleNumVar("AK_IMP_TOTAL", "xMe") -- AK_IMPGATE.scr:233
    end -- AK_IMPGATE.scr:234
    ctx:command("getobjecthandle", "sFireName, hCreature") -- AK_IMPGATE.scr:236
    if ctx:condition("hCreature!=0") then -- AK_IMPGATE.scr:237
        ctx:command("removeobject", "hCreature") -- AK_IMPGATE.scr:238
    end -- AK_IMPGATE.scr:239
    ctx:command("removetrigger", "spawn") -- AK_IMPGATE.scr:241
    ctx:command("ontargetdead", "DoNothing") -- AK_IMPGATE.scr:242
    ctx:command("wait", "0, 1, RemoveObject") -- AK_IMPGATE.scr:243
    do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:245
end

script.labels["RemoveObject"] = function(ctx)
    -- AK_IMPGATE.scr:248
    ctx:command("removeobject", "hMe") -- AK_IMPGATE.scr:250
    do return ctx:exit("TRUE") end -- AK_IMPGATE.scr:252
end

return script
