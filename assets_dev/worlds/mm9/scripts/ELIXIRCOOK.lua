-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ELIXIRCOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- ElixirCook.scr
-- 10/4
-- timmy
-- gives party Elixir Fluid and takes elixir ingredients
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- ELIXIRCOOK.scr:26
    if ctx:hasItem(378) then -- ELIXIRCOOK.scr:29-30
        ctx:takeItem(378) -- ELIXIRCOOK.scr:31
        ctx:giveItem(561) -- ELIXIRCOOK.scr:32
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- ELIXIRCOOK.scr:33
        do return ctx:exit("") end -- ELIXIRCOOK.scr:34
    end -- ELIXIRCOOK.scr:35
    do return ctx:exit("") end -- ELIXIRCOOK.scr:36
end

script.labels["Main"] = function(ctx)
    -- ELIXIRCOOK.scr:40
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- ELIXIRCOOK.scr:45
    ctx:getParam(0, "Item_Id") -- ELIXIRCOOK.scr:46
    ctx:getParam(1, "nGiveOnce") -- ELIXIRCOOK.scr:47
    do return ctx:exit("") end -- ELIXIRCOOK.scr:50
end

return script
