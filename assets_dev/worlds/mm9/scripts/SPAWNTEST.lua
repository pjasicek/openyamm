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
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- SPAWNTEST.scr:7
    ctx:state().g_hObject = ctx:spawn("g_posX", "g_posY", "g_posZ", "Goblin", "PickRandomWeapon", 1) -- SPAWNTEST.scr:8
    do return ctx:exit("") end -- SPAWNTEST.scr:10
end

script.labels["Main"] = function(ctx)
    -- SPAWNTEST.scr:13
    -- TraceOn
    ctx:addTrigger("Test", "OnTest") -- SPAWNTEST.scr:17
    do return ctx:exit("") end -- SPAWNTEST.scr:20
end

return script
