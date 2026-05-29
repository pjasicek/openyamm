-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GIVEELIXIR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- giveElixir.scr
-- 10/4
-- timmy
-- gives party Elixir of defedation and takes elixir fluid
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- GIVEELIXIR.scr:26
    if ctx:hasItem(358) then -- GIVEELIXIR.scr:30-31
        if ctx:hasItem(561) then -- GIVEELIXIR.scr:32-33
            ctx:takeItem(358) -- GIVEELIXIR.scr:34
            ctx:takeItem(561) -- GIVEELIXIR.scr:35
            ctx:giveItem(246) -- GIVEELIXIR.scr:36
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- GIVEELIXIR.scr:37
            do return ctx:exit("") end -- GIVEELIXIR.scr:38
        end -- GIVEELIXIR.scr:39
    end -- GIVEELIXIR.scr:40
    do return ctx:exit("") end -- GIVEELIXIR.scr:41
end

script.labels["Main"] = function(ctx)
    -- GIVEELIXIR.scr:43
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- GIVEELIXIR.scr:48
    do return ctx:exit("") end -- GIVEELIXIR.scr:51
end

return script
