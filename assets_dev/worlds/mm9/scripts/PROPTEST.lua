-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PROPTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- PropTest.scr
script.labels["OnUse"] = function(ctx)
    -- PROPTEST.scr:13
    ctx:state().nCount = (tonumber(ctx:state().nCount) or 0) + 1 -- PROPTEST.scr:16
    if ctx:condition("nCount==2") then -- PROPTEST.scr:18
        ctx:self():setNumberProperty("Locked", "FALSE") -- PROPTEST.scr:19
    end -- PROPTEST.scr:20
    do return ctx:exit(0) end -- PROPTEST.scr:22
end

script.labels["Main"] = function(ctx)
    -- PROPTEST.scr:25
    ctx:addTrigger("Use", "OnUse") -- PROPTEST.scr:28
    do return ctx:exit("") end -- PROPTEST.scr:30
end

return script
