-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BANSHEE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "FlyRange.inc" }

-- Banshee.Scr
-- Jeff Leggett
-- 10/31/2001
-- Go UnDead when we melee attack and go back to normal after
-- attack is done.
script.labels["GoNormal"] = function(ctx)
    -- BANSHEE.scr:19
    ctx:wait("UNDEAD_WAIT", 0, "DoNothing") -- BANSHEE.scr:22
    ctx:self():setStat("Undead", "FALSE") -- BANSHEE.scr:24
    do return ctx:exit("") end -- BANSHEE.scr:26
end

script.labels["GoUndead"] = function(ctx)
    -- BANSHEE.scr:29
    ctx:self():setStat("Undead", "TRUE") -- BANSHEE.scr:32
    -- Make sure we don't stay undead....
    ctx:wait("UNDEAD_WAIT", 5, "GoNormal") -- BANSHEE.scr:36
    do return ctx:exit("") end -- BANSHEE.scr:38
end

script.labels["BaseFlyAttack"] = function(ctx)
    -- BANSHEE.scr:42
    ctx:state().g_bTemp = ctx:self():getStat("Undead") -- BANSHEE.scr:45
    if ctx:condition("g_bTemp==FALSE") then -- BANSHEE.scr:47
        mm9.gosub(script, ctx, "GoUndead") -- BANSHEE.scr:48
    end -- BANSHEE.scr:49
    mm9.gosub(script, ctx, "BaseFlyAttack") -- BANSHEE.scr:51
    do return ctx:exit("") end -- BANSHEE.scr:53
end

script.labels["BaseFlyAttackDone"] = function(ctx)
    -- BANSHEE.scr:56
    mm9.gosub(script, ctx, "GoNormal") -- BANSHEE.scr:59
    mm9.gosub(script, ctx, "BaseFlyAttackDone") -- BANSHEE.scr:60
    do return ctx:exit("") end -- BANSHEE.scr:62
end

script.labels["SwoopIn"] = function(ctx)
    -- BANSHEE.scr:65
    -- Don't want this functionality for the Banshee...
    mm9.gosub(script, ctx, "SwoopDone") -- BANSHEE.scr:69
    do return ctx:exit("") end -- BANSHEE.scr:71
end

script.labels["Main"] = function(ctx)
    -- BANSHEE.scr:74
    mm9.gosub(script, ctx, "FlyRangeInit") -- BANSHEE.scr:77
    ctx:set("g_backOffYVal", 0.2) -- BANSHEE.scr:79
    ctx:set("g_backOffTime", 0.6) -- BANSHEE.scr:80
    ctx:hidePiece("Cloth") -- BANSHEE.scr:82
    do return ctx:exit("") end -- BANSHEE.scr:84
end

return script
