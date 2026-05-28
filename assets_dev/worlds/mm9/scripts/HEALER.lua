-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HEALER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 18, path = "healer.inc" }

-- Healer.scr
-- Jeff Leggett
-- This script is used by objects which heal players
-- one time.  That is, once a player is healed by this
-- object, it won't be able to be healed by it again.
-- (Unless it dies and comes back...)
-- Parameters:
-- p0	- Amount to heal players by (default=10)
-- p1  - Amount of times you can heal from this fountain
script.labels["Main"] = function(ctx)
    -- HEALER.scr:22
    mm9.gosub(script, ctx, "HealerInit") -- HEALER.scr:25
    ctx:getParam(0, "g_nTemp") -- HEALER.scr:27
    if ctx:condition("g_nTemp!=0") then -- HEALER.scr:29
        ctx:command("set", "g_nHealAmt, g_nTemp") -- HEALER.scr:30
    end -- HEALER.scr:31
    ctx:getParam(1, "g_nTemp") -- HEALER.scr:33
    if ctx:condition("g_nTemp!=0") then -- HEALER.scr:35
        ctx:command("set", "g_nHealCount, g_nTemp") -- HEALER.scr:36
    end -- HEALER.scr:37
    do return ctx:exit("") end -- HEALER.scr:39
end

return script
