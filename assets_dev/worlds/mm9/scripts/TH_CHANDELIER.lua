-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_CHANDELIER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- TH_Chandelier.scr
-- 1/29
-- timmy
-- Breaks the chain in Training Hall
-- Parameters
-- P0 Item number of item to give
script.labels["OnStart"] = function(ctx)
    -- TH_CHANDELIER.scr:20
    ctx:playSound("sounds\\events\\WoodCreak1.wav", "DoNothing", 100, 2400, "FALSE", 100) -- TH_CHANDELIER.scr:23
    ctx:wait(1, 1, "Break") -- TH_CHANDELIER.scr:24
    -- wait 2 5 Creak
    -- wait 3 10 Creak
    do return ctx:exit("") end -- TH_CHANDELIER.scr:27
end

script.labels["Creak"] = function(ctx)
    -- TH_CHANDELIER.scr:32
    ctx:playSound("sounds\\events\\WoodCreak1.wav", "DoNothing", 100, 2400, "FALSE", 100) -- TH_CHANDELIER.scr:35
    do return ctx:exit("") end -- TH_CHANDELIER.scr:36
end

script.labels["Break"] = function(ctx)
    -- TH_CHANDELIER.scr:38
    ctx:playSound("sounds\\events\\crate_smash.wav", "DoNothing", 100, 2400, "FALSE", 100) -- TH_CHANDELIER.scr:41
    ctx:object("DestructableBrush6"):trigger("destroy") -- TH_CHANDELIER.scr:42-43
    do return ctx:exit("") end -- TH_CHANDELIER.scr:44
end

script.labels["Main"] = function(ctx)
    -- TH_CHANDELIER.scr:49
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- TH_CHANDELIER.scr:54
    do return ctx:exit("") end -- TH_CHANDELIER.scr:57
end

return script
