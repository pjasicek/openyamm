-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BANKORB.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- BankOrb.inc
-- timmy
-- handles Fiachna A'Lanth for the Orb of Linking
-- edited by Bones 6/12/02
-- TELP Patch 1.3 -- prevents Fiachna from taking extra orbs
-- (except for one extra at quest completion)
-- flag variables
-- Parameters
-- p0 the key to CheckFor when player placed the orb
script.labels["OnRude"] = function(ctx)
    -- BANKORB.inc:30
    if ctx:hasKey(330) then -- BANKORB.inc:34-35
        ctx:takeKey(330) -- BANKORB.inc:36
        if ctx:hasKey("nKey") then -- BANKORB.inc:37-38
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- BANKORB.inc:39
            ctx:takeItem(252) -- BANKORB.inc:40
            ctx:giveKey("nKey2") -- BANKORB.inc:41
            mm9.gosub(script, ctx, "CheckAll") -- BANKORB.inc:42
        end -- BANKORB.inc:43
    end -- BANKORB.inc:44
    do return ctx:exit("") end -- BANKORB.inc:45
end

script.labels["CheckAll"] = function(ctx)
    -- BANKORB.inc:49
    if ctx:hasKey(337) then -- BANKORB.inc:52-53
        do return ctx:exit("") end -- BANKORB.inc:54
    end -- BANKORB.inc:55
    ctx:command("set", "g_ncounter, 0") -- BANKORB.inc:57
    if ctx:hasKey(331) then -- BANKORB.inc:59-60
        ctx:command("add", "g_ncounter, 1") -- BANKORB.inc:61
    end -- BANKORB.inc:62
    if ctx:hasKey(332) then -- BANKORB.inc:64-65
        ctx:command("add", "g_ncounter, 1") -- BANKORB.inc:66
    end -- BANKORB.inc:67
    if ctx:hasKey(333) then -- BANKORB.inc:69-70
        ctx:command("add", "g_ncounter, 1") -- BANKORB.inc:71
    end -- BANKORB.inc:72
    if ctx:hasKey(334) then -- BANKORB.inc:74-75
        ctx:command("add", "g_ncounter, 1") -- BANKORB.inc:76
    end -- BANKORB.inc:77
    if ctx:hasKey(335) then -- BANKORB.inc:79-80
        ctx:command("add", "g_ncounter, 1") -- BANKORB.inc:81
    end -- BANKORB.inc:82
    if ctx:hasKey(336) then -- BANKORB.inc:84-85
        ctx:command("add", "g_ncounter, 1") -- BANKORB.inc:86
    end -- BANKORB.inc:87
    if ctx:condition("g_ncounter==6") then -- BANKORB.inc:89
        ctx:giveKey(337) -- BANKORB.inc:90
        ctx:giveExp(20000) -- BANKORB.inc:91
        ctx:giveGold(15000) -- BANKORB.inc:92
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- BANKORB.inc:93
        ctx:takeItem(252) -- BANKORB.inc:94
        do return ctx:exit("") end -- BANKORB.inc:95
    end -- BANKORB.inc:96
    do return ctx:exit("") end -- BANKORB.inc:98
end

script.labels["Init"] = function(ctx)
    -- BANKORB.inc:101
    -- 331	Player placed orb in Thronheim
    -- 332	Player placed orb in guberland
    -- 333	Player placed orb in frosgard
    -- 334	Player placed orb in drangheim
    -- 335	player placed orb in thjorgard
    -- 336	player placed orb in sturmgard
    ctx:command("set", "nKey 333") -- BANKORB.inc:112
    ctx:command("set", "nKey2 327") -- BANKORB.inc:113
    do return ctx:exit("") end -- BANKORB.inc:115
end

return script
