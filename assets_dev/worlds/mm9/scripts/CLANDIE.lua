-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CLANDIE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- ClanDie.scr
-- timmy
-- Makes things hate things and then runs BaseMelee
script.labels["OnDamage"] = function(ctx)
    -- CLANDIE.scr:12
    ctx:command("getmyhandle", "g_hmyobject") -- CLANDIE.scr:14
    ctx:trigger("g_hmyobject", "destroy") -- CLANDIE.scr:15
    mm9.gosub(script, ctx, "OnDamage") -- CLANDIE.scr:16
    do return ctx:exit("") end -- CLANDIE.scr:17
end

script.labels["Main"] = function(ctx)
    -- CLANDIE.scr:20
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("addfriend", "NPC") -- CLANDIE.scr:25
    ctx:command("addfriend", "Player") -- CLANDIE.scr:26
    ctx:command("addenemy", "Horde") -- CLANDIE.scr:27
    ctx:command("ondamage", "OnDamage") -- CLANDIE.scr:28
    mm9.gosub(script, ctx, "BaseInit") -- CLANDIE.scr:29
    do return ctx:exit("") end -- CLANDIE.scr:30
end

return script
