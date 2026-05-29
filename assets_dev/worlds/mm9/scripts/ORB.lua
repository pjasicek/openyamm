-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ORB.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Orb.scr
-- timmy
-- handles checking to see if the party got 6 orbs of linking.
-- Parameters:
-- P0...key to give
script.labels["OnUse"] = function(ctx)
    -- ORB.scr:18
    ctx:giveItem(252) -- ORB.scr:22
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- ORB.scr:23
    ctx:self():remove() -- ORB.scr:25
    do return ctx:exit("") end -- ORB.scr:28
end

script.labels["Init"] = function(ctx)
    -- ORB.scr:32
    if ctx:hasKey(337) then -- ORB.scr:34-35
        ctx:self():remove() -- ORB.scr:37
    end -- ORB.scr:38
    do return ctx:exit("") end -- ORB.scr:41
end

script.labels["Main"] = function(ctx)
    -- ORB.scr:43
    -- traceon  ; delete me
    ctx:getParam(0, "Params") -- ORB.scr:48
    ctx:addTrigger("use", "OnUse") -- ORB.scr:49
    ctx:onEvent("OnPostStartWorld", "Init") -- ORB.scr:50
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ORB.scr:51
    ctx:onEvent("OnPostSaveLoad", "Init") -- ORB.scr:52
    ctx:wait(1, .1, "Init") -- ORB.scr:53
    do return ctx:exit("") end -- ORB.scr:54
end

return script
