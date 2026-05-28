-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BANKORB.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- BankOrb.scr
-- timmy
-- handles the bankers for the Orb of Linking
-- edited by Bones 6/13/02
-- TELP Patch 1.3 -- Prevents bankers from offering Orb placement after Orb has been placed.
-- flag variables
-- Parameters
-- p0 the key to CheckFor when player placed the orb
script.labels["OnUse"] = function(ctx)
    -- BANKORB.scr:28
    if ctx:hasKey("nKey2") then -- BANKORB.scr:31-32
        do return ctx:exit("") end -- BANKORB.scr:33
    end -- BANKORB.scr:34
    if not ctx:hasKey(322) then -- BANKORB.scr:36-37
        do return ctx:exit("") end -- BANKORB.scr:38
    end -- BANKORB.scr:39
    if ctx:hasItem(252) then -- BANKORB.scr:41-42
        ctx:giveKey(330) -- BANKORB.scr:43
    end -- BANKORB.scr:44
    do return ctx:exit("") end -- BANKORB.scr:45
end

script.labels["OnRude"] = function(ctx)
    -- BANKORB.scr:48
    if ctx:hasKey(330) then -- BANKORB.scr:51-52
        ctx:takeKey(330) -- BANKORB.scr:53
        if ctx:hasKey("nKey") then -- BANKORB.scr:54-55
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- BANKORB.scr:56
            ctx:takeItem(252) -- BANKORB.scr:57
            ctx:giveKey("nKey2") -- BANKORB.scr:58
            mm9.gosub(script, ctx, "CheckAll") -- BANKORB.scr:59
        end -- BANKORB.scr:60
    end -- BANKORB.scr:61
    do return ctx:exit("") end -- BANKORB.scr:63
end

script.labels["CheckAll"] = function(ctx)
    -- BANKORB.scr:67
    if ctx:hasKey(337) then -- BANKORB.scr:70-71
        do return ctx:exit("") end -- BANKORB.scr:72
    end -- BANKORB.scr:73
    ctx:command("set", "g_ncounter, 0") -- BANKORB.scr:75
    if ctx:hasKey(331) then -- BANKORB.scr:77-78
        ctx:command("add", "g_ncounter, 1") -- BANKORB.scr:79
    end -- BANKORB.scr:80
    if ctx:hasKey(332) then -- BANKORB.scr:82-83
        ctx:command("add", "g_ncounter, 1") -- BANKORB.scr:84
    end -- BANKORB.scr:85
    if ctx:hasKey(333) then -- BANKORB.scr:87-88
        ctx:command("add", "g_ncounter, 1") -- BANKORB.scr:89
    end -- BANKORB.scr:90
    if ctx:hasKey(334) then -- BANKORB.scr:92-93
        ctx:command("add", "g_ncounter, 1") -- BANKORB.scr:94
    end -- BANKORB.scr:95
    if ctx:hasKey(335) then -- BANKORB.scr:97-98
        ctx:command("add", "g_ncounter, 1") -- BANKORB.scr:99
    end -- BANKORB.scr:100
    if ctx:hasKey(336) then -- BANKORB.scr:102-103
        ctx:command("add", "g_ncounter, 1") -- BANKORB.scr:104
    end -- BANKORB.scr:105
    if ctx:condition("g_ncounter==6") then -- BANKORB.scr:107
        ctx:giveKey(337) -- BANKORB.scr:108
        ctx:giveExp(20000) -- BANKORB.scr:109
        ctx:giveGold(15000) -- BANKORB.scr:110
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- BANKORB.scr:111
    end -- BANKORB.scr:112
    do return ctx:exit("") end -- BANKORB.scr:114
end

script.labels["Init"] = function(ctx)
    -- BANKORB.scr:117
    -- 331	Player placed orb in Thronheim
    -- 332	Player placed orb in guberland
    -- 333	Player placed orb in frosgard
    -- 334	Player placed orb in drangheim
    -- 335	player placed orb in thjorgard
    -- 336	player placed orb in sturmgard
    ctx:command("getmyhandle", "g_hmyobject") -- BANKORB.scr:128
    ctx:command("getstat", "g_hmyobject RudeID nRude") -- BANKORB.scr:129
    -- debugout nRude
    if ctx:condition("nRude==13") then -- BANKORB.scr:133
        ctx:command("set", "nKey 335") -- BANKORB.scr:134
        ctx:command("set", "nKey2 323") -- BANKORB.scr:135
        do return ctx:exit("") end -- BANKORB.scr:136
    end -- BANKORB.scr:137
    if ctx:condition("nRude==56") then -- BANKORB.scr:139
        ctx:command("set", "nKey 336") -- BANKORB.scr:140
        ctx:command("set", "nKey2 324") -- BANKORB.scr:141
        do return ctx:exit("") end -- BANKORB.scr:142
    end -- BANKORB.scr:143
    if ctx:condition("nRude==100") then -- BANKORB.scr:145
        ctx:command("set", "nKey 334") -- BANKORB.scr:146
        ctx:command("set", "nKey2 325") -- BANKORB.scr:147
        do return ctx:exit("") end -- BANKORB.scr:148
    end -- BANKORB.scr:149
    if ctx:condition("nRude==140") then -- BANKORB.scr:151
        ctx:command("set", "nKey 332") -- BANKORB.scr:152
        ctx:command("set", "nKey2 326") -- BANKORB.scr:153
        do return ctx:exit("") end -- BANKORB.scr:154
    end -- BANKORB.scr:155
    if ctx:condition("nRude==206") then -- BANKORB.scr:157
        ctx:command("set", "nKey 333") -- BANKORB.scr:158
        ctx:command("set", "nKey2 327") -- BANKORB.scr:159
        do return ctx:exit("") end -- BANKORB.scr:160
    end -- BANKORB.scr:161
    if ctx:condition("nRude==243") then -- BANKORB.scr:163
        ctx:command("set", "nKey 331") -- BANKORB.scr:164
        ctx:command("set", "nKey2 328") -- BANKORB.scr:165
        do return ctx:exit("") end -- BANKORB.scr:166
    end -- BANKORB.scr:167
    do return ctx:exit("") end -- BANKORB.scr:169
end

script.labels["Main"] = function(ctx)
    -- BANKORB.scr:174
    -- traceon ;Remove
    ctx:addTrigger("Use", "ONUse") -- BANKORB.scr:179
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- BANKORB.scr:180
    ctx:getParam(0, "sLocation") -- BANKORB.scr:181
    ctx:command("onpoststartworld", "Init") -- BANKORB.scr:182
    ctx:command("onpostminisaveload", "Init") -- BANKORB.scr:183
    ctx:command("onpostsaveload", "Init") -- BANKORB.scr:184
    ctx:command("onpostsaveload", "Init") -- BANKORB.scr:185
    ctx:command("wait", "1 .1 Init") -- BANKORB.scr:186
    do return ctx:exit("") end -- BANKORB.scr:187
end

return script
