-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONTEST.scr"
script.includes = {}
script.labels = {}


-- dragontest.scr
script.labels["Init"] = function(ctx)
    -- DRAGONTEST.scr:8
    ctx:command("stop", "") -- DRAGONTEST.scr:11
    do return ctx:exit("") end -- DRAGONTEST.scr:12
end

script.labels["OnDamageDone"] = function(ctx)
    -- DRAGONTEST.scr:15
    -- Jump
    do return ctx:exit("") end -- DRAGONTEST.scr:20
end

script.labels["OnUse"] = function(ctx)
    -- DRAGONTEST.scr:23
    ctx:getParam(0, "g_hObject") -- DRAGONTEST.scr:25
    ctx:command("faceobject", "g_hObject, 180") -- DRAGONTEST.scr:26
    do return ctx:exit("") end -- DRAGONTEST.scr:28
end

script.labels["OnDamage"] = function(ctx)
    -- DRAGONTEST.scr:31
    ctx:command("jump", "") -- DRAGONTEST.scr:34
    do return ctx:exit(1) end -- DRAGONTEST.scr:35
end

script.labels["Main"] = function(ctx)
    -- DRAGONTEST.scr:37
    ctx:command("ondamage", "OnDamage") -- DRAGONTEST.scr:38
    -- OnDamageDone OnDamageDone
    ctx:addTrigger("Use", "OnUse") -- DRAGONTEST.scr:40
    ctx:command("wait", "0.5, Init") -- DRAGONTEST.scr:41
    do return ctx:exit("") end -- DRAGONTEST.scr:43
end

return script
