-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAMPDIRECTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }

-- campdirector.inc
-- John Machin
-- This script keeps track of the goblins
-- and dwarfs.  Will respawn monsters as
-- needed to keep battle going.
script.labels["DirectorDwarfDeath"] = function(ctx)
    -- CAMPDIRECTOR.scr:28
    -- Report a dwarf death and respawn the bad boy
    mm9.gosub(script, ctx, "DirectorSpawnDwarf") -- CAMPDIRECTOR.scr:31
    do return ctx:exit("") end -- CAMPDIRECTOR.scr:33
end

script.labels["DirectorSpawnDwarf"] = function(ctx)
    -- CAMPDIRECTOR.scr:36
    -- first lets make sure we don't spawn too many
    ctx:command("getobjects", "Dwarf, 20000, 10, g_hDwarfArray, g_nObjects") -- CAMPDIRECTOR.scr:39
    if ctx:condition("g_nObjects >= 5") then -- CAMPDIRECTOR.scr:40
        do return ctx:exit("") end -- CAMPDIRECTOR.scr:41
    end -- CAMPDIRECTOR.scr:42
    ctx:command("arrayget", "g_sDwarfSpawn, g_nLastDwarfSpawn, g_sSpawn") -- CAMPDIRECTOR.scr:44
    ctx:command("add", "g_nLastDwarfSpawn, 1") -- CAMPDIRECTOR.scr:45
    if ctx:condition("g_nLastDwarfSpawn > 4") then -- CAMPDIRECTOR.scr:47
        ctx:command("set", "g_nLastDwarfSpawn, 0") -- CAMPDIRECTOR.scr:48
    end -- CAMPDIRECTOR.scr:49
    if ctx:condition("g_sDwarfSpawn != NULL") then -- CAMPDIRECTOR.scr:51
        ctx:command("getobjecthandle", ", g_sSpawn, g_hSpawn") -- CAMPDIRECTOR.scr:52
    end -- CAMPDIRECTOR.scr:53
    -- Trigger the spawn dot
    if ctx:condition("g_hSpawn != NULL") then -- CAMPDIRECTOR.scr:56
        ctx:trigger("g_hSpawn", "trigger") -- CAMPDIRECTOR.scr:57
    end -- CAMPDIRECTOR.scr:58
    do return ctx:exit("") end -- CAMPDIRECTOR.scr:60
end

script.labels["DirectorZombieDeath"] = function(ctx)
    -- CAMPDIRECTOR.scr:63
    -- Report a goblin death and respawn the bad boy
    mm9.gosub(script, ctx, "DirectorSpawnZombie") -- CAMPDIRECTOR.scr:66
    do return ctx:exit("") end -- CAMPDIRECTOR.scr:68
end

script.labels["DirectorSpawnZombie"] = function(ctx)
    -- CAMPDIRECTOR.scr:72
    -- first lets make sure we don't spawn too many
    ctx:command("getobjects", "Zombie, 20000, 10, g_hZombieArray, g_nObjects") -- CAMPDIRECTOR.scr:75
    if ctx:condition("g_nObjects >= 5") then -- CAMPDIRECTOR.scr:76
        do return ctx:exit("") end -- CAMPDIRECTOR.scr:77
    end -- CAMPDIRECTOR.scr:78
    ctx:command("arrayget", "g_sZombieSpawn, g_nLastZombieSpawn, g_sSpawn") -- CAMPDIRECTOR.scr:80
    ctx:command("add", "g_nLastZombieSpawn, 1") -- CAMPDIRECTOR.scr:81
    if ctx:condition("g_nLastZombieSpawn > 4") then -- CAMPDIRECTOR.scr:83
        ctx:command("set", "g_nLastZombieSpawn, 0") -- CAMPDIRECTOR.scr:84
    end -- CAMPDIRECTOR.scr:85
    if ctx:condition("g_sSpawn != NULL") then -- CAMPDIRECTOR.scr:87
        ctx:command("getobjecthandle", ", g_sSpawn, g_hSpawn") -- CAMPDIRECTOR.scr:88
    end -- CAMPDIRECTOR.scr:89
    -- Trigger the spawn dot
    if ctx:condition("g_hSpawn != NULL") then -- CAMPDIRECTOR.scr:92
        ctx:trigger("g_hSpawn", "trigger") -- CAMPDIRECTOR.scr:93
    end -- CAMPDIRECTOR.scr:94
    do return ctx:exit("") end -- CAMPDIRECTOR.scr:96
end

script.labels["DirectorSetupSpawns"] = function(ctx)
    -- CAMPDIRECTOR.scr:100
    -- Setup Goblins first
    ctx:command("arrayput", "g_sZombieSpawn, 0, AISpawn16") -- CAMPDIRECTOR.scr:103
    ctx:command("arrayput", "g_sZombieSpawn, 1, AISpawn17") -- CAMPDIRECTOR.scr:104
    ctx:command("arrayput", "g_sZombieSpawn, 2, AISpawn18") -- CAMPDIRECTOR.scr:105
    ctx:command("arrayput", "g_sZombieSpawn, 3, AISpawn19") -- CAMPDIRECTOR.scr:106
    ctx:command("arrayput", "g_sZombieSpawn, 4, AISpawn20") -- CAMPDIRECTOR.scr:107
    -- Setup Dwarfs
    ctx:command("arrayput", "g_sDwarfSpawn, 0, AISpawn11") -- CAMPDIRECTOR.scr:110
    ctx:command("arrayput", "g_sDwarfSpawn, 1, AISpawn12") -- CAMPDIRECTOR.scr:111
    ctx:command("arrayput", "g_sDwarfSpawn, 2, AISpawn13") -- CAMPDIRECTOR.scr:112
    ctx:command("arrayput", "g_sDwarfSpawn, 3, AISpawn14") -- CAMPDIRECTOR.scr:113
    ctx:command("arrayput", "g_sDwarfSpawn, 4, AISpawn15") -- CAMPDIRECTOR.scr:114
    do return ctx:exit("") end -- CAMPDIRECTOR.scr:116
end

script.labels["Main"] = function(ctx)
    -- CAMPDIRECTOR.scr:119
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "DirectorSetupSpawns") -- CAMPDIRECTOR.scr:124
    ctx:addTrigger("DwarfDeath", "DirectorDwarfDeath") -- CAMPDIRECTOR.scr:126
    ctx:addTrigger("ZombieDeath", "DirectorZombieDeath") -- CAMPDIRECTOR.scr:127
    do return ctx:exit("") end -- CAMPDIRECTOR.scr:129
end

return script
