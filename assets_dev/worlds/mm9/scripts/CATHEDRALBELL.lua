-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CATHEDRALBELL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- CathedralBell.scr
-- timmy
-- Makes the bell ring
script.labels["OnUse"] = function(ctx)
    -- CATHEDRALBELL.scr:12
    ctx:self():playAnimation("Ring") -- CATHEDRALBELL.scr:16
    do return ctx:exit("") end -- CATHEDRALBELL.scr:18
end

script.labels["Main"] = function(ctx)
    -- CATHEDRALBELL.scr:24
    ctx:state().counter = 0 -- CATHEDRALBELL.scr:29
    ctx:addTrigger("Use", "OnUse") -- CATHEDRALBELL.scr:30
    ctx:onEvent("OnDamage", "Onuse") -- CATHEDRALBELL.scr:31
    do return ctx:exit("") end -- CATHEDRALBELL.scr:32
end

return script
