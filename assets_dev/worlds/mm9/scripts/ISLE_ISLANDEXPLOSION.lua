-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_ISLANDEXPLOSION.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "flags.inc" }

-- Isle_IslandExplosion.scr
-- by SJR
-- 01-01-02
-- Purpose:explosions at the sinking
-- island during the cinema.
script.labels["Main"] = function(ctx)
    -- ISLE_ISLANDEXPLOSION.scr:19
    ctx:command("getmyhandle", "hMe") -- ISLE_ISLANDEXPLOSION.scr:21
    ctx:addTrigger("explode", "CreateExplosion") -- ISLE_ISLANDEXPLOSION.scr:23
    do return ctx:exit(1) end -- ISLE_ISLANDEXPLOSION.scr:25
end

script.labels["CreateExplosion"] = function(ctx)
    -- ISLE_ISLANDEXPLOSION.scr:28
    ctx:command("setflag", "hMe, FLAG_VISIBLE") -- ISLE_ISLANDEXPLOSION.scr:30
    ctx:command("doclientfx", "hMe, SPELL_ELEMBLAST, 0, 1") -- ISLE_ISLANDEXPLOSION.scr:32
    ctx:command("doclientfx", "hMe, SPELL_BLACKSMOKE, 0, 1") -- ISLE_ISLANDEXPLOSION.scr:33
    ctx:command("effects_counter", "= EFFECTS_COUNTER + 1") -- ISLE_ISLANDEXPLOSION.scr:35
    if ctx:condition("EFFECTS_COUNTER<5") then -- ISLE_ISLANDEXPLOSION.scr:37
        ctx:command("getrandomfloat", "1, 2, EFFECTS_WAIT") -- ISLE_ISLANDEXPLOSION.scr:38
        ctx:command("wait", "0, EFFECTS_WAIT, CreateExplosion") -- ISLE_ISLANDEXPLOSION.scr:39
    else -- ISLE_ISLANDEXPLOSION.scr:40
        ctx:command("effects_counter", "= 0") -- ISLE_ISLANDEXPLOSION.scr:41
        mm9.gosub(script, ctx, "CreateSteam") -- ISLE_ISLANDEXPLOSION.scr:42
    end -- ISLE_ISLANDEXPLOSION.scr:43
    do return ctx:exit(1) end -- ISLE_ISLANDEXPLOSION.scr:45
end

script.labels["CreateSteam"] = function(ctx)
    -- ISLE_ISLANDEXPLOSION.scr:48
    ctx:command("doclientfx", "hMe, SPELL_MIST, 1, 0") -- ISLE_ISLANDEXPLOSION.scr:50
    do return ctx:exit(1) end -- ISLE_ISLANDEXPLOSION.scr:52
end

return script
