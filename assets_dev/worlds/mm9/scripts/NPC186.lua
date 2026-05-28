-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC186.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

-- NPC186.scr
-- timmy
-- handles Atli Sigmundssen voice and quest stuff
-- checks to see if player has completed promo quest
-- and gives completion key and reward.
-- Thorfinn's RudeID is 240
-- Atli's RudeID is 186
-- key 125 = player has got Atli
-- Key 126 = player has taken atli where he belongs
-- key 127 = player has completed the quest
-- flag variables
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC186.scr:46
    mm9.gosub(script, ctx, "mercpromo") -- NPC186.scr:49
    do return ctx:exit("") end -- NPC186.scr:52
end

script.labels["Mercpromo"] = function(ctx)
    -- NPC186.scr:56
    -- merc promo Quest
    if ctx:hasKey(126) then -- NPC186.scr:63-64
        -- checks to see if player took atli where he goes
        if not ctx:hasKey(127) then -- NPC186.scr:66-67
            -- checks to see if player has already completed quest
            ctx:giveKey(127) -- NPC186.scr:69
            ctx:giveGold(1000) -- NPC186.scr:70
            ctx:giveExp(24000) -- NPC186.scr:71
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC186.scr:72
            mm9.gosub(script, ctx, "PromoteMerc") -- NPC186.scr:73
            -- gives key and reward.
            do return ctx:exit("") end -- NPC186.scr:75
        end -- NPC186.scr:76
    end -- NPC186.scr:77
    do return ctx:exit("") end -- NPC186.scr:78
    -- End merc promo quest
    do return ctx:exit("") end -- NPC186.scr:84
end

script.labels["PromoteMerc"] = function(ctx)
    -- NPC186.scr:89
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(401) then -- NPC186.scr:95-96
        ctx:command("givepromo", "Mercenary Char1") -- NPC186.scr:97
        ctx:takeKey(401) -- NPC186.scr:98
    end -- NPC186.scr:99
    if ctx:hasKey(402) then -- NPC186.scr:101-102
        ctx:command("givepromo", "Mercenary Char2") -- NPC186.scr:103
        ctx:takeKey(402) -- NPC186.scr:104
    end -- NPC186.scr:105
    if ctx:hasKey(403) then -- NPC186.scr:107-108
        ctx:command("givepromo", "Mercenary Char3") -- NPC186.scr:109
        ctx:takeKey(403) -- NPC186.scr:110
    end -- NPC186.scr:111
    if ctx:hasKey(404) then -- NPC186.scr:113-114
        ctx:command("givepromo", "Mercenary Char4") -- NPC186.scr:115
        ctx:takeKey(404) -- NPC186.scr:116
    end -- NPC186.scr:117
    do return ctx:exit("") end -- NPC186.scr:118
end

script.labels["OnUse"] = function(ctx)
    -- NPC186.scr:123
    ctx:command("playsound", "voices\\NPC\\NPC_186.wav, Onexit, 100, 240, FALSE, 100") -- NPC186.scr:126
    do return ctx:exit("") end -- NPC186.scr:127
end

script.labels["OnExit"] = function(ctx)
    -- NPC186.scr:130
    do return ctx:exit("") end -- NPC186.scr:133
end

script.labels["OnSummon"] = function(ctx)
    -- NPC186.scr:136
    ctx:command("getmyhandle", "g_hobject") -- NPC186.scr:139
    ctx:command("setflag", "g_hobject, visible") -- NPC186.scr:140
    ctx:command("setflag", "g_hobject, solid") -- NPC186.scr:141
    ctx:command("setflag", "g_hobject, gravity") -- NPC186.scr:142
    ctx:command("getobjecthandle", "Atlimarker0 g_hobject") -- NPC186.scr:143
    ctx:command("walkto", "g_hobject 256, DoNothing") -- NPC186.scr:144
    ctx:command("getobjecthandle", "AtliGuard g_hobject") -- NPC186.scr:145
    ctx:trigger("g_hobject", "Return") -- NPC186.scr:146
    ctx:command("getobjecthandle", "atlidaughter g_hobject") -- NPC186.scr:147
    ctx:trigger("g_hobject", "return") -- NPC186.scr:148
    do return ctx:exit("") end -- NPC186.scr:149
end

script.labels["OnArrive"] = function(ctx)
    -- NPC186.scr:152
    if ctx:hasKey(197) then -- NPC186.scr:155-156
        ctx:command("getobjecthandle", "AtliMarker g_hobject") -- NPC186.scr:157
        ctx:command("walkto", "g_hobject 256, DoNothing") -- NPC186.scr:158
        do return ctx:exit("") end -- NPC186.scr:159
    end -- NPC186.scr:160
    do return ctx:exit("") end -- NPC186.scr:161
end

script.labels["Init"] = function(ctx)
    -- NPC186.scr:164
    if ctx:hasKey(127) then -- NPC186.scr:167-168
        ctx:command("getmyhandle", "g_hobject") -- NPC186.scr:170
        ctx:command("clearflag", "g_hobject, visible") -- NPC186.scr:171
        ctx:command("clearflag", "g_hobject, solid") -- NPC186.scr:172
        ctx:command("clearflag", "g_hobject, gravity") -- NPC186.scr:173
        do return ctx:exit("") end -- NPC186.scr:174
    end -- NPC186.scr:176
    do return ctx:exit("") end -- NPC186.scr:179
end

script.labels["Main"] = function(ctx)
    -- NPC186.scr:182
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC186.scr:190
    ctx:addTrigger("Summon", "OnSummon") -- NPC186.scr:191
    ctx:addTrigger("Use", "OnUse") -- NPC186.scr:192
    ctx:command("onpoststartworld", "Init") -- NPC186.scr:193
    ctx:command("onpostminisaveload", "Init") -- NPC186.scr:194
    ctx:command("onpostsaveload", "Init") -- NPC186.scr:195
    ctx:command("wait", "1 .1 Init") -- NPC186.scr:196
    do return ctx:exit("") end -- NPC186.scr:197
end

return script
