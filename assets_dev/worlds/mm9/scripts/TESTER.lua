-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TESTER.scr"
script.includes = {}
script.labels = {}


script.labels["Main"] = function(ctx)
    -- TESTER.scr:1
    -- traceon
    ctx:command("addfriend", "Player") -- TESTER.scr:3
    -- OnFoundPlayer output
    ctx:command("ondamage", "ondamage") -- TESTER.scr:5
    ctx:addTrigger("use", "givestuff") -- TESTER.scr:6
    -- giveattribute 3, -25, 1, 0
    -- givepromo 100
    ctx:command("setidle", "") -- TESTER.scr:9
    do return ctx:exit(1) end -- TESTER.scr:10
end

script.labels["givestuff"] = function(ctx)
    -- TESTER.scr:13
    ctx:command("playsound", "sounds\\default.wav") -- TESTER.scr:14
    ctx:command("giveattribute", "4, v, 1, 0") -- TESTER.scr:15
    ctx:command("cprint", "v") -- TESTER.scr:16
    do return ctx:exit(1) end -- TESTER.scr:17
end

script.labels["output"] = function(ctx)
    -- TESTER.scr:19
    ctx:command("cprint", "\"FoundPlayer!!!\"") -- TESTER.scr:20
    do return ctx:exit(1) end -- TESTER.scr:21
end

script.labels["reverse"] = function(ctx)
    -- TESTER.scr:23
    ctx:command("playsound", "sounds\\default.wav, callback") -- TESTER.scr:24
    -- AddEnemy Player
    do return ctx:exit(1) end -- TESTER.scr:26
end

script.labels["callback"] = function(ctx)
    -- TESTER.scr:28
    ctx:command("cprint", "PlaySoundCallback") -- TESTER.scr:29
    do return ctx:exit(1) end -- TESTER.scr:30
end

script.labels["dospell"] = function(ctx)
    -- TESTER.scr:34
    -- getmyhandle h
    ctx:command("createfx", "spell, h, 1") -- TESTER.scr:36
    do return ctx:exit(1) end -- TESTER.scr:37
end

script.labels["ondamage"] = function(ctx)
    -- TESTER.scr:41
    ctx:command("v", "= v - 1") -- TESTER.scr:42
    ctx:command("counter", "= counter + 1") -- TESTER.scr:43
    ctx:command("cprint", "Hits:") -- TESTER.scr:44
    ctx:command("cprint", "counter") -- TESTER.scr:45
    ctx:command("cprint", "**********") -- TESTER.scr:46
    do return ctx:exit(1) end -- TESTER.scr:47
end

return script
