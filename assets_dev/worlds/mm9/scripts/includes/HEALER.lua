-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HEALER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- Healer.inc
-- Jeff Leggett
-- This script is used by objects which heal players
-- one time.  That is, once a player is healed by this
-- object, it won't be able to be healed by it again.
-- (Unless it dies and comes back...)
-- Heal amount defaults to 10... Change this value in your
-- script if you want....
script.labels["HealerOnUse"] = function(ctx)
    -- HEALER.inc:26
    -- See if we should heal the object that triggered
    -- us..
    ctx:getParam(0, "g_hObject") -- HEALER.inc:33
    if ctx:condition("g_hObject==NULL") then -- HEALER.inc:35
        do return ctx:exit("FALSE") end -- HEALER.inc:36
    end -- HEALER.inc:37
    ctx:command("getplayerid", "g_hObject, g_nPlayerId") -- HEALER.inc:39
    ctx:command("getplayernbr", "g_hObject, g_nPlayerNbr") -- HEALER.inc:40
    if ctx:condition("g_nPlayerNbr==-1") then -- HEALER.inc:42
        -- Not a player!
        do return ctx:exit("FALSE") end -- HEALER.inc:44
    end -- HEALER.inc:45
    ctx:command("arrayget", "g_nPlayerHealedArray, g_nPlayerNbr, g_nTemp") -- HEALER.inc:47
    if ctx:condition("g_nTemp==g_nPlayerId") then -- HEALER.inc:49
        ctx:command("arrayget", "g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp") -- HEALER.inc:50
        if ctx:condition("g_nTemp>=g_nHealCount") then -- HEALER.inc:51
            -- they've already Used this item...
            -- Don't let them do it again...
            do return ctx:exit("FALSE") end -- HEALER.inc:55
        end -- HEALER.inc:56
    else -- HEALER.inc:57
        ctx:command("arrayput", "g_nPlayerHealedCountArray, g_nPlayerNbr, 0") -- HEALER.inc:58
    end -- HEALER.inc:60
    ctx:command("arrayget", "g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp") -- HEALER.inc:62
    ctx:command("add", "g_nTemp, 1") -- HEALER.inc:63
    ctx:command("arrayput", "g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp") -- HEALER.inc:64
    ctx:command("arrayput", "g_nPlayerHealedArray, g_nPlayerNbr, g_nPlayerId") -- HEALER.inc:65
    ctx:command("heal", "g_hObject, g_nHealAmt") -- HEALER.inc:67
    do return ctx:exit("") end -- HEALER.inc:69
end

script.labels["HealerInit"] = function(ctx)
    -- HEALER.inc:72
    -- You must gosub this routine from your :Main routine
    -- TraceOn
    ctx:addTrigger("Use", "HealerOnUse") -- HEALER.inc:79
    do return ctx:exit("") end -- HEALER.inc:81
end

return script
