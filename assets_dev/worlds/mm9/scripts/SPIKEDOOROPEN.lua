-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPIKEDOOROPEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- SpikeDoorOpen.scr
-- By Karl
-- When spike are removed the blocks can be
-- opened
script.labels["OnUse"] = function(ctx)
    -- SPIKEDOOROPEN.scr:15
    ctx:state().hMyDoor = ctx:self() -- SPIKEDOOROPEN.scr:17
    if ctx:condition("count == 6") then -- SPIKEDOOROPEN.scr:18
        ctx:trigger("hMyDoor", "unlock") -- SPIKEDOOROPEN.scr:19
        ctx:trigger("hMyDoor", "toggle") -- SPIKEDOOROPEN.scr:20
    end -- SPIKEDOOROPEN.scr:21
    do return ctx:exit("TRUE") end -- SPIKEDOOROPEN.scr:22
end

script.labels["OnePulled"] = function(ctx)
    -- SPIKEDOOROPEN.scr:24
    ctx:set("count", "count + 1") -- SPIKEDOOROPEN.scr:26
    if ctx:condition("count == 6") then -- SPIKEDOOROPEN.scr:27
        ctx:trigger("hMyDoor", "unlock") -- SPIKEDOOROPEN.scr:28
        ctx:trigger("hMyDoor", "use") -- SPIKEDOOROPEN.scr:29
    end -- SPIKEDOOROPEN.scr:30
    do return ctx:exit(1) end -- SPIKEDOOROPEN.scr:31
end

script.labels["Main2"] = function(ctx)
    -- SPIKEDOOROPEN.scr:33
    ctx:state().hMyDoor = ctx:objectOrNil("ABDoorBoards0") -- SPIKEDOOROPEN.scr:35
    ctx:addTrigger("OnePulled", "OnePulled") -- SPIKEDOOROPEN.scr:36
    do return ctx:exit(1) end -- SPIKEDOOROPEN.scr:37
end

script.labels["main"] = function(ctx)
    -- SPIKEDOOROPEN.scr:39
    ctx:wait(0, 0.4, "Main2") -- SPIKEDOOROPEN.scr:41
    do return ctx:exit("") end -- SPIKEDOOROPEN.scr:42
end

return script
