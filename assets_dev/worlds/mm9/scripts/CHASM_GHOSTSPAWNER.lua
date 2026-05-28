-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHASM_GHOSTSPAWNER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "ListMaker.inc" }

-- SpawnMgr.scr
-- by SJR
-- 09-21-01
-- Purpose:
-- ScriptParams are:
-- p0 = LISTNAME
-- p1 = LISTFIRST
-- p2 = LISTLAST
script.labels["Main"] = function(ctx)
    -- CHASM_GHOSTSPAWNER.scr:26
    ctx:getParam(0, "LISTNAME") -- CHASM_GHOSTSPAWNER.scr:28
    ctx:getParam(1, "LISTFIRST") -- CHASM_GHOSTSPAWNER.scr:29
    ctx:getParam(2, "LISTLAST") -- CHASM_GHOSTSPAWNER.scr:30
    ctx:command("oncachefiles", "CacheFiles") -- CHASM_GHOSTSPAWNER.scr:32
    ctx:command("listindex", "= LISTLAST") -- CHASM_GHOSTSPAWNER.scr:34
    ctx:addTrigger("spawn", "SpawnCreature") -- CHASM_GHOSTSPAWNER.scr:36
    do return ctx:exit("TRUE") end -- CHASM_GHOSTSPAWNER.scr:38
end

script.labels["CacheFiles"] = function(ctx)
    -- CHASM_GHOSTSPAWNER.scr:41
    ctx:command("cachescript", "\"ghost.scr\"") -- CHASM_GHOSTSPAWNER.scr:43
    ctx:command("cacheclientfx", "SPELL_BLUEFIRE") -- CHASM_GHOSTSPAWNER.scr:45
    do return ctx:exit("TRUE") end -- CHASM_GHOSTSPAWNER.scr:47
end

script.labels["SpawnCreature"] = function(ctx)
    -- CHASM_GHOSTSPAWNER.scr:50
    mm9.gosub(script, ctx, "GetNextObject") -- CHASM_GHOSTSPAWNER.scr:52
    ctx:command("getpos", "LISTOBJECT, x,y,z") -- CHASM_GHOSTSPAWNER.scr:54
    ctx:command("spawn", "hDummy, x,y,z, SPAWN_PARAM") -- CHASM_GHOSTSPAWNER.scr:55
    if ctx:condition("hDummy!=0") then -- CHASM_GHOSTSPAWNER.scr:57
        ctx:command("doclientfx", "hDummy, SPELL_BLUEFIRE, FALSE, TRUE") -- CHASM_GHOSTSPAWNER.scr:58
    end -- CHASM_GHOSTSPAWNER.scr:59
    if ctx:condition("LISTINDEX==LISTLAST") then -- CHASM_GHOSTSPAWNER.scr:61
        ctx:command("removetrigger", "spawn") -- CHASM_GHOSTSPAWNER.scr:62
    end -- CHASM_GHOSTSPAWNER.scr:63
    do return ctx:exit("TRUE") end -- CHASM_GHOSTSPAWNER.scr:65
end

return script
