-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 3, path = "globals.inc" }

-- spawntest.scr
script.labels["OnTest"] = function(ctx)
    -- SPAWNTEST.scr:5
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- SPAWNTEST.scr:7
    ctx:command("spawn", "g_hObject, g_posX, g_posY, g_posZ,Goblin PickRandomWeapon 1") -- SPAWNTEST.scr:8
    do return ctx:exit("") end -- SPAWNTEST.scr:10
end

script.labels["Main"] = function(ctx)
    -- SPAWNTEST.scr:13
    -- TraceOn
    ctx:command("getmyhandle", "g_hMyObject") -- SPAWNTEST.scr:16
    ctx:addTrigger("Test", "OnTest") -- SPAWNTEST.scr:17
    do return ctx:exit("") end -- SPAWNTEST.scr:20
end

return script
