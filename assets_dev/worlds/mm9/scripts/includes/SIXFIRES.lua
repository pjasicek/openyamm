-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SIXFIRES.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "Svenshowtake.inc" }

-- SixFires.inc
-- timmy
-- handles the Six Fires of Penance stuff
-- flag variables
script.labels["Guilt"] = function(ctx)
    -- SIXFIRES.inc:51
    if ctx:hasKey(381) then -- SIXFIRES.inc:54-55
        do return ctx:exit("") end -- SIXFIRES.inc:56
    end -- SIXFIRES.inc:57
    ctx:command("screenfadeout", "1") -- SIXFIRES.inc:58
    ctx:command("wait", "1 1 FadeIn") -- SIXFIRES.inc:59
    do return ctx:exit("") end -- SIXFIRES.inc:61
end

script.labels["Spawn"] = function(ctx)
    -- SIXFIRES.inc:67
    ctx:command("getobjecthandle", "sBadGuys g_hobject") -- SIXFIRES.inc:76
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:77
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:78
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:79
    ctx:command("spawn", "hMonsterC Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:80
    ctx:command("spawn", "hMonsterD Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:81
    -- Spawn hMonsterB Xpos YPos ZPos sMonsterB
    ctx:command("getobjecthandle", "sGoodGuys g_hobject") -- SIXFIRES.inc:85
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:86
    ctx:command("spawn", "hGoodGuyA Xpos YPos ZPos sGoodGuyA") -- SIXFIRES.inc:89
    ctx:command("spawn", "hGoodGuyB Xpos YPos ZPos sGoodGuya") -- SIXFIRES.inc:90
    do return ctx:exit("") end -- SIXFIRES.inc:93
end

script.labels["FadeIn"] = function(ctx)
    -- SIXFIRES.inc:98
    ctx:command("letterbox", "true") -- SIXFIRES.inc:101
    ctx:command("getobjecthandle", "Camera9 g_hobject") -- SIXFIRES.inc:102
    ctx:trigger("g_hobject", "On") -- SIXFIRES.inc:103
    ctx:trigger("g_hobject", "play") -- SIXFIRES.inc:104
    ctx:command("screenfadein", "1") -- SIXFIRES.inc:105
    do return ctx:exit("") end -- SIXFIRES.inc:107
end

script.labels["GoodGuys"] = function(ctx)
    -- SIXFIRES.inc:110
    ctx:command("set", "SCRIPT \" ScriptName Hate.scr\"") -- SIXFIRES.inc:113
    ctx:command("sgoodguya", "= sGoodGuyA + Script") -- SIXFIRES.inc:115
    ctx:command("sgoodguyb", "= sGoodGuyB + Script") -- SIXFIRES.inc:116
    ctx:command("sgoodguyc", "= sGoodGuyc + Script") -- SIXFIRES.inc:117
    ctx:command("getobjecthandle", "sGoodGuys g_hobject") -- SIXFIRES.inc:121
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:122
    -- Spawn hMonsterC Xpos YPos ZPos sKira
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sGoodGuyA") -- SIXFIRES.inc:125
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyB") -- SIXFIRES.inc:126
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyB") -- SIXFIRES.inc:127
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyC") -- SIXFIRES.inc:128
    ctx:command("wait", "1 5 End") -- SIXFIRES.inc:130
    do return ctx:exit("") end -- SIXFIRES.inc:131
end

script.labels["End"] = function(ctx)
    -- SIXFIRES.inc:134
    ctx:command("screenfadeout", "2") -- SIXFIRES.inc:139
    ctx:command("wait", "1 2 FadeIn2") -- SIXFIRES.inc:140
    do return ctx:exit("") end -- SIXFIRES.inc:141
end

script.labels["FadeIn2"] = function(ctx)
    -- SIXFIRES.inc:144
    ctx:command("letterbox", "false") -- SIXFIRES.inc:147
    ctx:command("getobjecthandle", "Camera9 g_hobject") -- SIXFIRES.inc:148
    ctx:trigger("g_hobject", "Off") -- SIXFIRES.inc:149
    ctx:command("screenfadein", "1") -- SIXFIRES.inc:150
    ctx:command("onfoundplayer", "DoRude") -- SIXFIRES.inc:151
    do return ctx:exit("") end -- SIXFIRES.inc:152
end

script.labels["Confession"] = function(ctx)
    -- SIXFIRES.inc:155
    if ctx:hasKey(383) then -- SIXFIRES.inc:158-159
        ctx:command("getobjecthandle", "BjarniThorvaldssen0 g_hobject") -- SIXFIRES.inc:160
        ctx:command("clearflag", "g_hobject visible") -- SIXFIRES.inc:161
        ctx:command("getobjecthandle", "KiratheCold0 g_hobject") -- SIXFIRES.inc:162
        ctx:command("clearflag", "g_hobject visible") -- SIXFIRES.inc:163
        ctx:command("getobjecthandle", "MarkeltheGreat0 g_hobject") -- SIXFIRES.inc:164
        ctx:command("clearflag", "g_hobject visible") -- SIXFIRES.inc:165
        ctx:command("getobjecthandle", "SigmundtheStressed0 g_hobject") -- SIXFIRES.inc:166
        ctx:command("clearflag", "g_hobject visible") -- SIXFIRES.inc:167
        ctx:command("getobjecthandle", "SvenSvenssen0 g_hobject") -- SIXFIRES.inc:168
        ctx:command("clearflag", "g_hobject visible") -- SIXFIRES.inc:169
        ctx:command("getobjecthandle", "TryggvaRavenlocks0 g_hobject") -- SIXFIRES.inc:170
        ctx:command("clearflag", "g_hobject visible") -- SIXFIRES.inc:171
        do return ctx:exit("") end -- SIXFIRES.inc:172
        do return ctx:exit("") end -- SIXFIRES.inc:173
    end -- SIXFIRES.inc:174
    ctx:command("getobjecthandle", "BjarniThorvaldssen0 g_hobject") -- SIXFIRES.inc:176
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:177
    ctx:command("getobjecthandle", "KiratheCold0 g_hobject") -- SIXFIRES.inc:178
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:179
    ctx:command("getobjecthandle", "MarkeltheGreat0 g_hobject") -- SIXFIRES.inc:180
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:181
    ctx:command("getobjecthandle", "SigmundtheStressed0 g_hobject") -- SIXFIRES.inc:182
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:183
    ctx:command("getobjecthandle", "SvenSvenssen0 g_hobject") -- SIXFIRES.inc:184
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:185
    ctx:command("getobjecthandle", "TryggvaRavenlocks0 g_hobject") -- SIXFIRES.inc:186
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:187
    do return ctx:exit("") end -- SIXFIRES.inc:188
end

script.labels["Suffering"] = function(ctx)
    -- SIXFIRES.inc:191
    if ctx:hasKey(491) then -- SIXFIRES.inc:194-195
        do return ctx:exit("") end -- SIXFIRES.inc:196
    end -- SIXFIRES.inc:197
    if ctx:hasKey(385) then -- SIXFIRES.inc:200-201
        if not ctx:hasKey(491) then -- SIXFIRES.inc:202-203
            ctx:giveExp(52000) -- SIXFIRES.inc:204
        end -- SIXFIRES.inc:205
        ctx:giveKey(491) -- SIXFIRES.inc:206
        -- take poisoning and disease away
        ctx:command("clearcondition", "13") -- SIXFIRES.inc:208
        ctx:command("getobjecthandle", "sufferingFire g_hobject") -- SIXFIRES.inc:209
        ctx:trigger("g_hobject", "On") -- SIXFIRES.inc:210
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- SIXFIRES.inc:212
        do return ctx:exit("") end -- SIXFIRES.inc:213
    end -- SIXFIRES.inc:214
    ctx:command("wait", "1 5 Questioner") -- SIXFIRES.inc:216
    do return ctx:exit("") end -- SIXFIRES.inc:218
end

script.labels["Questioner"] = function(ctx)
    -- SIXFIRES.inc:221
    -- poison and disease player
    ctx:command("setcondition", "13") -- SIXFIRES.inc:226
    ctx:doRude(432) -- SIXFIRES.inc:227
    do return ctx:exit("") end -- SIXFIRES.inc:228
end

script.labels["Retribution"] = function(ctx)
    -- SIXFIRES.inc:232
    if ctx:hasKey(387) then -- SIXFIRES.inc:235-236
        do return ctx:exit("") end -- SIXFIRES.inc:237
    end -- SIXFIRES.inc:238
    if ctx:hasKey(5021) then -- SIXFIRES.inc:240-241
        do return ctx:exit("") end -- SIXFIRES.inc:242
    end -- SIXFIRES.inc:243
    ctx:giveKey(5021) -- SIXFIRES.inc:245
    ctx:command("getobjecthandle", "ForadDarre0 g_hobject") -- SIXFIRES.inc:247
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:248
    ctx:command("set", "sBadGuys BadGuys0") -- SIXFIRES.inc:250
    ctx:command("getobjecthandle", "sBadGuys g_hobject") -- SIXFIRES.inc:252
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:253
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:254
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:255
    ctx:command("spawn", "hMonsterC Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:256
    ctx:command("spawn", "hMonsterD Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:257
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:258
    ctx:command("set", "sBadGuys BadGuys1") -- SIXFIRES.inc:260
    ctx:command("getobjecthandle", "sBadGuys g_hobject") -- SIXFIRES.inc:262
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:263
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:264
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:265
    ctx:command("spawn", "hMonsterC Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:266
    ctx:command("spawn", "hMonsterD Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:267
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:268
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:269
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:270
    do return ctx:exit("") end -- SIXFIRES.inc:271
end

script.labels["Absolution"] = function(ctx)
    -- SIXFIRES.inc:274
    ctx:command("getobjecthandle", "retributionFire g_hobject") -- SIXFIRES.inc:277
    ctx:trigger("g_hobject", "On") -- SIXFIRES.inc:278
    if ctx:hasKey(492) then -- SIXFIRES.inc:281-282
        do return ctx:exit("") end -- SIXFIRES.inc:283
    end -- SIXFIRES.inc:284
    ctx:giveExp(52000) -- SIXFIRES.inc:286
    ctx:giveKey(492) -- SIXFIRES.inc:287
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- SIXFIRES.inc:289
    ctx:command("set", "ShowAll, TRUE") -- SIXFIRES.inc:291
    mm9.gosub(script, ctx, "removeall") -- SIXFIRES.inc:292
    ctx:command("getobjecthandle", "svensword g_hobject") -- SIXFIRES.inc:294
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:295
    ctx:command("getobjecthandle", "Bjarnisword g_hobject") -- SIXFIRES.inc:297
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:298
    ctx:command("getobjecthandle", "Sigmundsword g_hobject") -- SIXFIRES.inc:300
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:301
    ctx:command("getobjecthandle", "TryygvaSword g_hobject") -- SIXFIRES.inc:303
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:304
    ctx:command("getobjecthandle", "Kirasword g_hobject") -- SIXFIRES.inc:306
    ctx:command("setflag", "g_hobject visible") -- SIXFIRES.inc:307
    ctx:command("set", "sMonsterA Zombie") -- SIXFIRES.inc:309
    ctx:command("set", "sMonsterB Ghast") -- SIXFIRES.inc:310
    ctx:command("set", "sMonsterC Fright") -- SIXFIRES.inc:311
    ctx:command("getobjecthandle", "Badguys0 g_hobject") -- SIXFIRES.inc:313
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:314
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- SIXFIRES.inc:315
    ctx:command("getobjecthandle", "BadGuys1 g_hobject") -- SIXFIRES.inc:318
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:319
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:320
    ctx:command("getobjecthandle", "GoodGuys0 g_hobject") -- SIXFIRES.inc:323
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:324
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:325
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:326
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:327
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:328
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:329
    do return ctx:exit("") end -- SIXFIRES.inc:331
end

script.labels["Rebirth"] = function(ctx)
    -- SIXFIRES.inc:333
    ctx:command("getobjecthandle", "ExitTrigger1 g_hobject") -- SIXFIRES.inc:336
    ctx:trigger("g_hobject", "On") -- SIXFIRES.inc:337
    ctx:command("set", "sMonsterA Zombie") -- SIXFIRES.inc:339
    ctx:command("set", "sMonsterB Ghast") -- SIXFIRES.inc:340
    ctx:command("set", "sMonsterC Fright") -- SIXFIRES.inc:341
    ctx:command("getobjecthandle", "Badguys0 g_hobject") -- SIXFIRES.inc:343
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:344
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- SIXFIRES.inc:345
    ctx:command("getobjecthandle", "BadGuys1 g_hobject") -- SIXFIRES.inc:348
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:349
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterB") -- SIXFIRES.inc:350
    ctx:command("getobjecthandle", "GoodGuys0 g_hobject") -- SIXFIRES.inc:353
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- SIXFIRES.inc:354
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:355
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:356
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:357
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:358
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- SIXFIRES.inc:359
    do return ctx:exit("") end -- SIXFIRES.inc:361
end

return script
