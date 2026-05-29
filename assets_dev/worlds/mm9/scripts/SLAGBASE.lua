-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SLAGBASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- Slagbase.scr
-- timmy
-- handles the slag extractor stuff.
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- SLAGBASE.scr:16
    if ctx:hasItem(399) then -- SLAGBASE.scr:22-23
        ctx:object("slag"):trigger("Show") -- SLAGBASE.scr:24-25
        do return ctx:exit("") end -- SLAGBASE.scr:26
    end -- SLAGBASE.scr:27
    do return ctx:exit("") end -- SLAGBASE.scr:28
end

script.labels["Main"] = function(ctx)
    -- SLAGBASE.scr:32
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- SLAGBASE.scr:39
    do return ctx:exit("") end -- SLAGBASE.scr:41
end

return script
