-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CLOSESHOP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- closeshop.scr
-- timmy
-- closes and open shops
script.labels["Close"] = function(ctx)
    -- CLOSESHOP.scr:13
    ctx:giveKey(5017) -- CLOSESHOP.scr:16
    do return ctx:exit("") end -- CLOSESHOP.scr:17
end

script.labels["Open"] = function(ctx)
    -- CLOSESHOP.scr:20
    ctx:takeKey(5017) -- CLOSESHOP.scr:23
    do return ctx:exit("") end -- CLOSESHOP.scr:24
end

script.labels["Main"] = function(ctx)
    -- CLOSESHOP.scr:27
    -- traceon
    -- Don't Forget to Delete this!
    ctx:atTime(20, 0, "Close") -- CLOSESHOP.scr:32
    ctx:atTime(6, 0, "Open") -- CLOSESHOP.scr:33
    do return ctx:exit("") end -- CLOSESHOP.scr:35
end

return script
