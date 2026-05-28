-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "UNITED.inc"
script.includes = {}
script.labels = {}


-- United.inc
-- timmy
-- handles checking to see if 5 of the 6 clans are united and giving key 178
-- Keys:
-- Sven (3) 34
-- Kira (239) 82
-- Bjarni (45) 38
-- Sigmund (87) 51
-- Markel (127) 63
-- Tryygva (180) 74
-- 5 clans united 178
script.labels["United"] = function(ctx)
    -- UNITED.inc:34
    -- called in OnRudeExit
    -- gives reward for uniting the clans
    if not ctx:hasKey(179) then -- UNITED.inc:42-43
        -- checks to see if they already have got the reward.
        if ctx:hasKey(83) then -- UNITED.inc:45-46
            -- checks to see if they've United the clans
            ctx:giveKey(179) -- UNITED.inc:48
            ctx:giveExp(26500) -- UNITED.inc:49
            ctx:giveGold(6000) -- UNITED.inc:50
            -- gives reward
            do return ctx:exit("") end -- UNITED.inc:52
        end -- UNITED.inc:53
    end -- UNITED.inc:54
    do return ctx:exit("") end -- UNITED.inc:55
end

script.labels["OnCheck"] = function(ctx)
    -- UNITED.inc:58
    if not ctx:hasKey(178) then -- UNITED.inc:61-62
        ctx:command("g_ncounter", "= 0") -- UNITED.inc:64
        if ctx:hasKey("Key_1") then -- UNITED.inc:66-67
            ctx:command("g_ncounter", "= g_ncounter + 1") -- UNITED.inc:68
            -- ArrayPut ClanArray, 0, 1
        end -- UNITED.inc:70
        if ctx:hasKey("Key_2") then -- UNITED.inc:72-73
            ctx:command("g_ncounter", "= g_ncounter + 1") -- UNITED.inc:74
            -- ArrayPut ClanArray, 1, 1
        end -- UNITED.inc:76
        if ctx:hasKey("key_3") then -- UNITED.inc:78-79
            ctx:command("g_ncounter", "= g_ncounter + 1") -- UNITED.inc:80
            -- ArrayPut ClanArray, 2, 1
        end -- UNITED.inc:82
        if ctx:hasKey("Key_4") then -- UNITED.inc:84-85
            ctx:command("g_ncounter", "= g_ncounter + 1") -- UNITED.inc:86
            -- ArrayPut ClanArray, 3, 1
        end -- UNITED.inc:88
        if ctx:hasKey("key_5") then -- UNITED.inc:90-91
            ctx:command("g_ncounter", "= g_ncounter + 1") -- UNITED.inc:92
            -- ArrayPut ClanArray, 4, 1
        end -- UNITED.inc:94
        if ctx:condition("g_ncounter == 5") then -- UNITED.inc:97
            ctx:giveKey(178) -- UNITED.inc:98
            ctx:command("set", "BeenDone, true") -- UNITED.inc:99
            do return ctx:exit("") end -- UNITED.inc:100
        end -- UNITED.inc:101
        -- gosub checkallclans
    end -- UNITED.inc:104
    do return ctx:exit("") end -- UNITED.inc:105
end

script.labels["CheckAllClans"] = function(ctx)
    -- UNITED.inc:108
    if ctx:condition("BeenDone==true") then -- UNITED.inc:112
        do return ctx:exit("") end -- UNITED.inc:113
    end -- UNITED.inc:114
    ctx:command("set", "counter, 0") -- UNITED.inc:116
end

script.labels["CheckAllClansloop"] = function(ctx)
    -- UNITED.inc:120
    ctx:command("arrayget", "ClanArray, counter, ClanOn") -- UNITED.inc:126
    if ctx:condition("ClanOn==false") then -- UNITED.inc:127
        do return ctx:exit("") end -- UNITED.inc:128
    end -- UNITED.inc:129
    ctx:command("add", "Counter, 1") -- UNITED.inc:131
    if ctx:condition("counter<5") then -- UNITED.inc:133
        do return mm9.gotoLabel(script, ctx, "CheckAllClansloop") end -- UNITED.inc:134
    end -- UNITED.inc:135
    -- ...........success.............
    ctx:giveKey(178) -- UNITED.inc:140
    ctx:command("set", "BeenDone, true") -- UNITED.inc:142
    ctx:command("wait", "1 0.2, DoNothing") -- UNITED.inc:143
    do return ctx:exit("") end -- UNITED.inc:144
end

script.labels["SvenInit"] = function(ctx)
    -- UNITED.inc:147
    ctx:command("set", "Key_1, 82") -- UNITED.inc:150
    ctx:command("set", "Key_2, 38") -- UNITED.inc:151
    ctx:command("set", "Key_3, 51") -- UNITED.inc:152
    ctx:command("set", "Key_4, 63") -- UNITED.inc:153
    ctx:command("set", "Key_5, 74") -- UNITED.inc:154
    do return ctx:exit("") end -- UNITED.inc:155
end

script.labels["KiraInit"] = function(ctx)
    -- UNITED.inc:158
    ctx:command("set", "Key_1, 34") -- UNITED.inc:161
    ctx:command("set", "Key_2, 38") -- UNITED.inc:162
    ctx:command("set", "Key_3, 51") -- UNITED.inc:163
    ctx:command("set", "Key_4, 63") -- UNITED.inc:164
    ctx:command("set", "Key_5, 74") -- UNITED.inc:165
    do return ctx:exit("") end -- UNITED.inc:168
end

script.labels["BjarniInit"] = function(ctx)
    -- UNITED.inc:171
    ctx:command("set", "Key_1, 82") -- UNITED.inc:174
    ctx:command("set", "Key_2, 34") -- UNITED.inc:175
    ctx:command("set", "Key_3, 51") -- UNITED.inc:176
    ctx:command("set", "Key_4, 63") -- UNITED.inc:177
    ctx:command("set", "Key_5, 74") -- UNITED.inc:178
    do return ctx:exit("") end -- UNITED.inc:180
end

script.labels["MarkelInit"] = function(ctx)
    -- UNITED.inc:183
    ctx:command("set", "Key_1, 82") -- UNITED.inc:186
    ctx:command("set", "Key_2, 38") -- UNITED.inc:187
    ctx:command("set", "Key_3, 51") -- UNITED.inc:188
    ctx:command("set", "Key_4, 34") -- UNITED.inc:189
    ctx:command("set", "Key_5, 74") -- UNITED.inc:190
    do return ctx:exit("") end -- UNITED.inc:191
end

script.labels["SigmundInit"] = function(ctx)
    -- UNITED.inc:194
    ctx:command("set", "Key_1, 82") -- UNITED.inc:197
    ctx:command("set", "Key_2, 38") -- UNITED.inc:198
    ctx:command("set", "Key_3, 34") -- UNITED.inc:199
    ctx:command("set", "Key_4, 63") -- UNITED.inc:200
    ctx:command("set", "Key_5, 74") -- UNITED.inc:201
    do return ctx:exit("") end -- UNITED.inc:203
end

script.labels["TryygvaInit"] = function(ctx)
    -- UNITED.inc:206
    ctx:command("set", "Key_1, 82") -- UNITED.inc:209
    ctx:command("set", "Key_2, 38") -- UNITED.inc:210
    ctx:command("set", "Key_3, 51") -- UNITED.inc:211
    ctx:command("set", "Key_4, 63") -- UNITED.inc:212
    ctx:command("set", "Key_5, 34") -- UNITED.inc:213
    do return ctx:exit("") end -- UNITED.inc:214
end

script.labels["UnitedInit"] = function(ctx)
    -- UNITED.inc:217
    -- traceon
    -- Don't Forget to Delete this!
    if ctx:condition("Jarl==Sven") then -- UNITED.inc:223
        mm9.gosub(script, ctx, "SvenInit") -- UNITED.inc:224
        do return ctx:exit("") end -- UNITED.inc:225
    end -- UNITED.inc:226
    if ctx:condition("Jarl==Kira") then -- UNITED.inc:228
        mm9.gosub(script, ctx, "KiraInit") -- UNITED.inc:229
        do return ctx:exit("") end -- UNITED.inc:230
    end -- UNITED.inc:231
    if ctx:condition("Jarl==Bjarni") then -- UNITED.inc:233
        mm9.gosub(script, ctx, "BjarniInit") -- UNITED.inc:234
        do return ctx:exit("") end -- UNITED.inc:235
    end -- UNITED.inc:236
    if ctx:condition("Jarl==Markel") then -- UNITED.inc:238
        mm9.gosub(script, ctx, "MarkelInit") -- UNITED.inc:239
        do return ctx:exit("") end -- UNITED.inc:240
    end -- UNITED.inc:241
    if ctx:condition("Jarl==Sigmund") then -- UNITED.inc:243
        mm9.gosub(script, ctx, "SigmundInit") -- UNITED.inc:244
        do return ctx:exit("") end -- UNITED.inc:245
    end -- UNITED.inc:246
    if ctx:condition("Jarl==Tryygva") then -- UNITED.inc:248
        mm9.gosub(script, ctx, "TryygvaInit") -- UNITED.inc:249
        do return ctx:exit("") end -- UNITED.inc:250
    end -- UNITED.inc:251
    do return ctx:exit("") end -- UNITED.inc:254
end

return script
