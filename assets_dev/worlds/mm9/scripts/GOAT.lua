-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GOAT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 5, path = "FarmAnimal.Inc" }

-- goat.scr
script.labels["AttackDone"] = function(ctx)
    -- GOAT.scr:9
    ctx:command("target", "NULL") -- GOAT.scr:11
    mm9.gosub(script, ctx, "EnableWandering") -- GOAT.scr:12
    do return ctx:exit("") end -- GOAT.scr:13
end

script.labels["OnUse"] = function(ctx)
    -- GOAT.scr:16
    -- If they touch/use us, wack them one!
    ctx:command("stop", "") -- GOAT.scr:22
    mm9.gosub(script, ctx, "DisableWandering") -- GOAT.scr:23
    ctx:getParam(0, "g_hObject") -- GOAT.scr:25
    ctx:command("target", "g_hObject,TRUE") -- GOAT.scr:26
    ctx:command("attack", "") -- GOAT.scr:27
    ctx:command("wait", "22,1,AttackDone") -- GOAT.scr:28
    do return ctx:exit("TRUE") end -- GOAT.scr:29
end

script.labels["Main"] = function(ctx)
    -- GOAT.scr:32
    mm9.gosub(script, ctx, "FarmAnimalInit") -- GOAT.scr:35
    ctx:addTrigger("Use", "OnUse") -- GOAT.scr:36
    do return ctx:exit("") end -- GOAT.scr:38
end

return script
