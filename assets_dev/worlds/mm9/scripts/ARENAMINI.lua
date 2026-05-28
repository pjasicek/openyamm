-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENAMINI.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- ArenaCreature.scr
-- timmy
-- handles scholar promo stuff
script.labels["Face"] = function(ctx)
    -- ARENAMINI.scr:13
    ctx:setPropNumber("CanDamage", "FALSE") -- ARENAMINI.scr:16
    ctx:command("getobjecthandle", "marker5 g_hobject") -- ARENAMINI.scr:17
    ctx:command("faceobject", "g_hobject 0 DoNothing") -- ARENAMINI.scr:18
    ctx:command("getobjecthandle", "ArenaFight g_hobject") -- ARENAMINI.scr:19
    ctx:trigger("g_hobject", "Hello") -- ARENAMINI.scr:20
    do return ctx:exit("") end -- ARENAMINI.scr:21
end

script.labels["OnUse"] = function(ctx)
    -- ARENAMINI.scr:24
    if ctx:hasKey(1017) then -- ARENAMINI.scr:27-28
        if ctx:hasKey(1019) then -- ARENAMINI.scr:29-30
            do return ctx:exit("") end -- ARENAMINI.scr:31
        end -- ARENAMINI.scr:32
        ctx:command("getobjecthandle", "ShopkeeperElfMaleB0 g_hobject") -- ARENAMINI.scr:33
        ctx:trigger("g_hobject", "sMonster_ID") -- ARENAMINI.scr:34
        ctx:giveKey(1019) -- ARENAMINI.scr:35
        ctx:command("attack", ", DoNothing") -- ARENAMINI.scr:36
        ctx:command("wait", "1 3 Fight") -- ARENAMINI.scr:37
        do return ctx:exit("") end -- ARENAMINI.scr:38
    end -- ARENAMINI.scr:39
    do return ctx:exit("") end -- ARENAMINI.scr:40
end

script.labels["Fight"] = function(ctx)
    -- ARENAMINI.scr:43
    ctx:command("getobjecthandle", "ShopkeeperElfMaleB0 g_hobject") -- ARENAMINI.scr:46
    ctx:trigger("g_hobject", "Fight") -- ARENAMINI.scr:47
    do return ctx:exit("") end -- ARENAMINI.scr:49
end

script.labels["OnAttack"] = function(ctx)
    -- ARENAMINI.scr:52
    do return ctx:exit("TRUE") end -- ARENAMINI.scr:54
end

script.labels["Main"] = function(ctx)
    -- ARENAMINI.scr:57
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("wait", "1 1 Face") -- ARENAMINI.scr:63
    ctx:getParam(0, "sMonster_ID") -- ARENAMINI.scr:64
    ctx:addTrigger("use", "OnUse") -- ARENAMINI.scr:65
    ctx:command("ondamage", "OnUse") -- ARENAMINI.scr:66
    ctx:command("ondeath", ", OnUse") -- ARENAMINI.scr:67
    ctx:command("addmodelkey", "rAttack,OnAttack") -- ARENAMINI.scr:69
    ctx:command("addmodelkey", "lAttack,OnAttack") -- ARENAMINI.scr:70
    ctx:command("addmodelkey", "RangeAttack,OnAttack") -- ARENAMINI.scr:71
    ctx:command("addmodelkey", "Bite,OnAttack") -- ARENAMINI.scr:72
    do return ctx:exit("") end -- ARENAMINI.scr:74
end

return script
