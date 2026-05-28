-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GIVERANDOM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "pickmon.inc" }

-- GiveRandom.inc
-- by SJR
-- 11-03-01
-- Purpose:give the player a random
-- bonus or detriment
-- Triggers:
-- 'use' = give out random thing
-- ScriptParams:
-- p0 = name of smoke to trigger
-- p1 = number of "wishes" (0=infinite)
script.labels["Main"] = function(ctx)
    -- GIVERANDOM.scr:38
    ctx:getParam(0, "sSmokeName") -- GIVERANDOM.scr:40
    -- OnPostStartWorld InitGiveRandom
    ctx:command("wait", "0, 5, InitGiveRandom") -- GIVERANDOM.scr:43
    mm9.gosub(script, ctx, "InitItemList") -- GIVERANDOM.scr:45
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:47
end

script.labels["InitGiveRandom"] = function(ctx)
    -- GIVERANDOM.scr:50
    ctx:addTrigger("use", "ProduceRandomEffect") -- GIVERANDOM.scr:52
    ctx:command("setcallback", "0, GiveRandomGold") -- GIVERANDOM.scr:54
    ctx:command("setcallback", "1, GiveRandomExp") -- GIVERANDOM.scr:55
    ctx:command("setcallback", "2, GiveRandomItem") -- GIVERANDOM.scr:56
    ctx:command("setcallback", "3, GiveRandomHealth") -- GIVERANDOM.scr:57
    ctx:command("setcallback", "4, GiveRandomAttribute") -- GIVERANDOM.scr:58
    ctx:command("getplayerhandle", "hPlayer") -- GIVERANDOM.scr:60
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:62
end

script.labels["ProduceRandomEffect"] = function(ctx)
    -- GIVERANDOM.scr:66
    ctx:command("removetrigger", "use") -- GIVERANDOM.scr:68
    if ctx:condition("hSmoke==0") then -- GIVERANDOM.scr:70
        ctx:command("getobjecthandle", "sSmokeName, hSmoke") -- GIVERANDOM.scr:71
    end -- GIVERANDOM.scr:72
    if ctx:condition("hSmoke!=0") then -- GIVERANDOM.scr:73
        ctx:trigger("hSmoke", "trigger") -- GIVERANDOM.scr:74
    end -- GIVERANDOM.scr:75
    ctx:command("getrandomint", "0, 5, nRandom") -- GIVERANDOM.scr:77
    ctx:command("docallback", "nRandom") -- GIVERANDOM.scr:79
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:81
end

-- private
script.labels["GetRandomQuantity"] = function(ctx)
    -- GIVERANDOM.scr:92
    ctx:command("getrandomint", "nMin, nMax, nQuantity") -- GIVERANDOM.scr:93
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:95
end

script.labels["GiveRandomGold"] = function(ctx)
    -- GIVERANDOM.scr:97
    ctx:command("nmin", "= MIN_GOLD") -- GIVERANDOM.scr:98
    ctx:command("nmax", "= MAX_GOLD") -- GIVERANDOM.scr:99
    mm9.gosub(script, ctx, "GetRandomQuantity") -- GIVERANDOM.scr:100
    ctx:giveGold("nQuantity") -- GIVERANDOM.scr:102
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:104
end

script.labels["GiveRandomExp"] = function(ctx)
    -- GIVERANDOM.scr:106
    ctx:command("nmin", "= MIN_EXP") -- GIVERANDOM.scr:107
    ctx:command("nmax", "= MAX_EXP") -- GIVERANDOM.scr:108
    mm9.gosub(script, ctx, "GetRandomQuantity") -- GIVERANDOM.scr:109
    ctx:giveExp("nQuantity") -- GIVERANDOM.scr:111
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:113
end

script.labels["GiveRandomHealth"] = function(ctx)
    -- GIVERANDOM.scr:115
    ctx:command("nmin", "= MIN_HEALTH") -- GIVERANDOM.scr:116
    ctx:command("nmax", "= MAX_HEALTH") -- GIVERANDOM.scr:117
    mm9.gosub(script, ctx, "GetRandomQuantity") -- GIVERANDOM.scr:118
    ctx:command("heal", "hPlayer, nQuantity") -- GIVERANDOM.scr:120
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:122
end

script.labels["GiveRandomAttribute"] = function(ctx)
    -- GIVERANDOM.scr:124
    ctx:command("nmin", "= MIN_ATTRIBUTE") -- GIVERANDOM.scr:125
    ctx:command("nmax", "= MAX_ATTRIBUTE") -- GIVERANDOM.scr:126
    mm9.gosub(script, ctx, "GetRandomQuantity") -- GIVERANDOM.scr:127
    ctx:command("getrandomint", "0, NUM_ATTRIBUTES, nTemp") -- GIVERANDOM.scr:129
    -- numattribute, howmuch, everyone, gameseconds (5 real mins)
    ctx:command("giveattribute", "nTemp, nQuantity, TRUE, 3000") -- GIVERANDOM.scr:131
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:133
end

script.labels["GiveRandomItem"] = function(ctx)
    -- GIVERANDOM.scr:135
    ctx:command("getrandomint", "0, NUM_ITEMS, nTemp") -- GIVERANDOM.scr:136
    ctx:command("arrayget", "npItems, nTemp, nQuantity") -- GIVERANDOM.scr:137
    ctx:giveItem("nQuantity") -- GIVERANDOM.scr:139
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:141
end

-- should be named "SuperFunToWriteRoutine"
script.labels["InitItemList"] = function(ctx)
    -- GIVERANDOM.scr:144
    ctx:command("arrayput", "npItems, 0 ,2") -- GIVERANDOM.scr:145
    ctx:command("arrayput", "npItems, 1 ,359") -- GIVERANDOM.scr:146
    ctx:command("arrayput", "npItems, 2 ,81") -- GIVERANDOM.scr:147
    ctx:command("arrayput", "npItems, 3 ,420") -- GIVERANDOM.scr:148
    ctx:command("arrayput", "npItems, 4 ,86") -- GIVERANDOM.scr:149
    ctx:command("arrayput", "npItems, 5 ,510") -- GIVERANDOM.scr:150
    ctx:command("arrayput", "npItems, 6 ,285") -- GIVERANDOM.scr:151
    ctx:command("arrayput", "npItems, 7 ,318") -- GIVERANDOM.scr:152
    ctx:command("arrayput", "npItems, 8 ,71") -- GIVERANDOM.scr:153
    ctx:command("arrayput", "npItems, 9 ,319") -- GIVERANDOM.scr:154
    ctx:command("arrayput", "npItems, 10,96") -- GIVERANDOM.scr:155
    ctx:command("arrayput", "npItems, 11,97") -- GIVERANDOM.scr:156
    ctx:command("arrayput", "npItems, 12,320") -- GIVERANDOM.scr:157
    ctx:command("arrayput", "npItems, 13,26") -- GIVERANDOM.scr:158
    ctx:command("arrayput", "npItems, 14,519") -- GIVERANDOM.scr:159
    ctx:command("arrayput", "npItems, 15,76") -- GIVERANDOM.scr:160
    ctx:command("arrayput", "npItems, 16,87") -- GIVERANDOM.scr:161
    ctx:command("arrayput", "npItems, 17,61") -- GIVERANDOM.scr:162
    ctx:command("arrayput", "npItems, 18,36") -- GIVERANDOM.scr:163
    ctx:command("arrayput", "npItems, 19,18") -- GIVERANDOM.scr:164
    ctx:command("arrayput", "npItems, 20,41") -- GIVERANDOM.scr:165
    ctx:command("arrayput", "npItems, 21,297") -- GIVERANDOM.scr:166
    ctx:command("arrayput", "npItems, 22,296") -- GIVERANDOM.scr:167
    ctx:command("arrayput", "npItems, 23,295") -- GIVERANDOM.scr:168
    ctx:command("arrayput", "npItems, 24,2") -- GIVERANDOM.scr:169
    ctx:command("arrayput", "npItems, 25,56") -- GIVERANDOM.scr:170
    ctx:command("arrayput", "npItems, 26,421") -- GIVERANDOM.scr:171
    ctx:command("arrayput", "npItems, 27,66") -- GIVERANDOM.scr:172
    ctx:command("arrayput", "npItems, 28,292") -- GIVERANDOM.scr:173
    ctx:command("arrayput", "npItems, 29,291") -- GIVERANDOM.scr:174
    ctx:command("arrayput", "npItems, 30,290") -- GIVERANDOM.scr:175
    ctx:command("arrayput", "npItems, 31,415") -- GIVERANDOM.scr:176
    ctx:command("arrayput", "npItems, 32,288") -- GIVERANDOM.scr:177
    ctx:command("arrayput", "npItems, 33,287") -- GIVERANDOM.scr:178
    ctx:command("arrayput", "npItems, 34,294") -- GIVERANDOM.scr:179
    ctx:command("arrayput", "npItems, 35,155") -- GIVERANDOM.scr:180
    ctx:command("arrayput", "npItems, 36,332") -- GIVERANDOM.scr:181
    ctx:command("arrayput", "npItems, 37,518") -- GIVERANDOM.scr:182
    ctx:command("arrayput", "npItems, 38,150") -- GIVERANDOM.scr:183
    ctx:command("arrayput", "npItems, 39,547") -- GIVERANDOM.scr:184
    ctx:command("arrayput", "npItems, 40,538") -- GIVERANDOM.scr:185
    ctx:command("arrayput", "npItems, 41,333") -- GIVERANDOM.scr:186
    ctx:command("arrayput", "npItems, 42,142") -- GIVERANDOM.scr:187
    ctx:command("arrayput", "npItems, 43,334") -- GIVERANDOM.scr:188
    ctx:command("arrayput", "npItems, 44,552") -- GIVERANDOM.scr:189
    ctx:command("arrayput", "npItems, 45,553") -- GIVERANDOM.scr:190
    ctx:command("arrayput", "npItems, 46,554") -- GIVERANDOM.scr:191
    ctx:command("arrayput", "npItems, 47,335") -- GIVERANDOM.scr:192
    ctx:command("arrayput", "npItems, 48,160") -- GIVERANDOM.scr:193
    ctx:command("arrayput", "npItems, 49,548") -- GIVERANDOM.scr:194
    ctx:command("arrayput", "npItems, 50,346") -- GIVERANDOM.scr:195
    ctx:command("arrayput", "npItems, 51,349") -- GIVERANDOM.scr:196
    ctx:command("arrayput", "npItems, 52,134") -- GIVERANDOM.scr:197
    ctx:command("arrayput", "npItems, 53,327") -- GIVERANDOM.scr:198
    ctx:command("arrayput", "npItems, 54,133") -- GIVERANDOM.scr:199
    ctx:command("arrayput", "npItems, 55,422") -- GIVERANDOM.scr:200
    ctx:command("arrayput", "npItems, 56,126") -- GIVERANDOM.scr:201
    ctx:command("arrayput", "npItems, 57,127") -- GIVERANDOM.scr:202
    ctx:command("arrayput", "npItems, 58,530") -- GIVERANDOM.scr:203
    ctx:command("arrayput", "npItems, 59,350") -- GIVERANDOM.scr:204
    ctx:command("arrayput", "npItems, 60,254") -- GIVERANDOM.scr:205
    do return ctx:exit("TRUE") end -- GIVERANDOM.scr:207
end

return script
