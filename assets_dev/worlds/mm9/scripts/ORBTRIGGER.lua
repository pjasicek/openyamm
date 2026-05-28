-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ORBTRIGGER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Orb.scr
-- timmy
-- handles checking to see if the party got 6 orbs of linking.
script.labels["OnUse"] = function(ctx)
    -- ORBTRIGGER.scr:16
    ctx:command("getobjecthandle", "Orb g_hobject") -- ORBTRIGGER.scr:19
    ctx:trigger("g_hobject", "Placed") -- ORBTRIGGER.scr:20
    do return ctx:exit("") end -- ORBTRIGGER.scr:21
end

script.labels["Main"] = function(ctx)
    -- ORBTRIGGER.scr:27
    -- traceon  ; delete me
    ctx:addTrigger("Use", "OnUse") -- ORBTRIGGER.scr:32
    do return ctx:exit("") end -- ORBTRIGGER.scr:33
end

return script
