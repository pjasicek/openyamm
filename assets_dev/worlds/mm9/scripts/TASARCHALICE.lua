-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TASARCHALICE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- TaSarChalice.scr
-- 10/01
-- timmy
-- handles Ta'Sar Academy's chalice puzzle.
script.labels["OnUse"] = function(ctx)
    -- TASARCHALICE.scr:13
    if ctx:condition("Chalice_ID==Right") then -- TASARCHALICE.scr:17
        ctx:giveAttribute(0, 10, 0, 288000) -- TASARCHALICE.scr:18
        ctx:giveKey(9500) -- TASARCHALICE.scr:19
        do return ctx:exit("") end -- TASARCHALICE.scr:20
    else -- TASARCHALICE.scr:21
        -- damage player
        do return ctx:exit("") end -- TASARCHALICE.scr:23
    end -- TASARCHALICE.scr:24
    do return ctx:exit("") end -- TASARCHALICE.scr:25
end

script.labels["Main"] = function(ctx)
    -- TASARCHALICE.scr:29
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "Chalice_ID") -- TASARCHALICE.scr:34
    ctx:addTrigger("Use", "OnUse") -- TASARCHALICE.scr:35
    do return ctx:exit("") end -- TASARCHALICE.scr:36
end

return script
