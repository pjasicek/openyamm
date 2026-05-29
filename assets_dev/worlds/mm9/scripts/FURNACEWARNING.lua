-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FURNACEWARNING.scr"
script.includes = {}
script.labels = {}


-- furnacewarning.scr
-- Displays Furnace warning onuse
-- #hObject		hSign
script.labels["Done"] = function(ctx)
    -- FURNACEWARNING.scr:12
    ctx:letterBox("FALSE") -- FURNACEWARNING.scr:15
    do return ctx:exit("TRUE") end -- FURNACEWARNING.scr:17
end

script.labels["OnUse"] = function(ctx)
    -- FURNACEWARNING.scr:21
    -- Letterbox TRUE
    ctx:rolloverText("", 1, 0, 3000, 2000) -- FURNACEWARNING.scr:25
    -- Wait 0 1.5 Done
    do return ctx:exit("TRUE") end -- FURNACEWARNING.scr:27
end

script.labels["Main"] = function(ctx)
    -- FURNACEWARNING.scr:30
    ctx:addTrigger("use", "OnUse") -- FURNACEWARNING.scr:32
    do return ctx:exit("TRUE") end -- FURNACEWARNING.scr:34
end

return script
