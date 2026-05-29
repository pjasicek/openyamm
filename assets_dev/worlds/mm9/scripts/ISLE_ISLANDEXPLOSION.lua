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
    ctx:addTrigger("explode", "CreateExplosion") -- ISLE_ISLANDEXPLOSION.scr:23
    do return ctx:exit(1) end -- ISLE_ISLANDEXPLOSION.scr:25
end

script.labels["CreateExplosion"] = function(ctx)
    -- ISLE_ISLANDEXPLOSION.scr:28
    ctx:self():setFlag("FLAG_VISIBLE", true) -- ISLE_ISLANDEXPLOSION.scr:30
    ctx:self():doClientFx("SPELL_ELEMBLAST", 0, 1) -- ISLE_ISLANDEXPLOSION.scr:32
    ctx:self():doClientFx("SPELL_BLACKSMOKE", 0, 1) -- ISLE_ISLANDEXPLOSION.scr:33
    ctx:set("EFFECTS_COUNTER", "EFFECTS_COUNTER + 1") -- ISLE_ISLANDEXPLOSION.scr:35
    if ctx:condition("EFFECTS_COUNTER<5") then -- ISLE_ISLANDEXPLOSION.scr:37
        ctx:randomFloat(1, 2, "EFFECTS_WAIT") -- ISLE_ISLANDEXPLOSION.scr:38
        ctx:wait(0, "EFFECTS_WAIT", "CreateExplosion") -- ISLE_ISLANDEXPLOSION.scr:39
    else -- ISLE_ISLANDEXPLOSION.scr:40
        ctx:state().EFFECTS_COUNTER = 0 -- ISLE_ISLANDEXPLOSION.scr:41
        mm9.gosub(script, ctx, "CreateSteam") -- ISLE_ISLANDEXPLOSION.scr:42
    end -- ISLE_ISLANDEXPLOSION.scr:43
    do return ctx:exit(1) end -- ISLE_ISLANDEXPLOSION.scr:45
end

script.labels["CreateSteam"] = function(ctx)
    -- ISLE_ISLANDEXPLOSION.scr:48
    ctx:self():doClientFx("SPELL_MIST", 1, 0) -- ISLE_ISLANDEXPLOSION.scr:50
    do return ctx:exit(1) end -- ISLE_ISLANDEXPLOSION.scr:52
end

return script
