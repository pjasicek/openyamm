-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BANDITATTACK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- Banditattack.scr
-- timmy
-- handles The bandits attacking the wagon.
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnAttack"] = function(ctx)
    -- BANDITATTACK.scr:23
    ctx:onEvent("OnFoundPlayer", "OnExit") -- BANDITATTACK.scr:26
    ctx:self():setNumberProperty("TerrainMode", "TRUE") -- BANDITATTACK.scr:28
    ctx:state().g_hobject = ctx:objectOrNil("Atlimarker0") -- BANDITATTACK.scr:30
    ctx:self():runTo(ctx:object("g_hobject"), 256, "Onexit") -- BANDITATTACK.scr:31
    do return ctx:exit("") end -- BANDITATTACK.scr:32
end

script.labels["OnExit"] = function(ctx)
    -- BANDITATTACK.scr:35
    ctx:self():stop() -- BANDITATTACK.scr:37
    mm9.gosub(script, ctx, "baseinit") -- BANDITATTACK.scr:38
    do return ctx:exit("") end -- BANDITATTACK.scr:39
end

script.labels["Obstacle"] = function(ctx)
    -- BANDITATTACK.scr:42
    ctx:onEvent("OnFoundPlayer", "OnExit") -- BANDITATTACK.scr:45
    ctx:state().g_hobject = ctx:objectOrNil("Atlimarker0") -- BANDITATTACK.scr:47
    ctx:self():runTo(ctx:object("g_hobject"), 256, "Onexit") -- BANDITATTACK.scr:48
    do return ctx:exit("") end -- BANDITATTACK.scr:49
end

script.labels["Main"] = function(ctx)
    -- BANDITATTACK.scr:52
    -- traceon
    -- Don't Forget to Delete this!
    ctx:wait(1, 1, "OnAttack") -- BANDITATTACK.scr:57
    ctx:onEvent("OnPostStartWorld", "OnAttack") -- BANDITATTACK.scr:58
    ctx:onEvent("OnPostMiniSaveLoad", "OnAttack") -- BANDITATTACK.scr:59
    ctx:onEvent("OnPostSaveLoad", "OnAttack") -- BANDITATTACK.scr:60
    do return ctx:exit("") end -- BANDITATTACK.scr:63
end

return script
