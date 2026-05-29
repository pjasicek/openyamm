-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GREATBOOKKEY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- GreatBookKey.scr
-- Handles the Great Book Key stuff
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- GREATBOOKKEY.scr:16
    if ctx:hasItem(243) then -- GREATBOOKKEY.scr:19-20
        ctx:giveItem(560) -- GREATBOOKKEY.scr:22
        ctx:giveItem(244) -- GREATBOOKKEY.scr:23
        ctx:giveItem(347) -- GREATBOOKKEY.scr:24
        ctx:self():remove() -- GREATBOOKKEY.scr:26
        ctx:giveKey(374) -- GREATBOOKKEY.scr:27
        do return ctx:exit("") end -- GREATBOOKKEY.scr:28
    else -- GREATBOOKKEY.scr:29
        ctx:giveItem(244) -- GREATBOOKKEY.scr:30
        do return ctx:exit("") end -- GREATBOOKKEY.scr:31
    end -- GREATBOOKKEY.scr:32
end

script.labels["OnAppear"] = function(ctx)
    -- GREATBOOKKEY.scr:34
    ctx:giveKey(375) -- GREATBOOKKEY.scr:37
    ctx:self():setFlag("visible", true) -- GREATBOOKKEY.scr:38
    ctx:self():setFlag("solid", true) -- GREATBOOKKEY.scr:39
    ctx:self():setFlag("gravity", true) -- GREATBOOKKEY.scr:40
    do return ctx:exit("") end -- GREATBOOKKEY.scr:41
end

script.labels["Init"] = function(ctx)
    -- GREATBOOKKEY.scr:43
    if ctx:hasKey(374) then -- GREATBOOKKEY.scr:48-49
        ctx:self():remove() -- GREATBOOKKEY.scr:51
        do return ctx:exit("") end -- GREATBOOKKEY.scr:52
    end -- GREATBOOKKEY.scr:53
    if ctx:hasKey(375) then -- GREATBOOKKEY.scr:55-56
        ctx:self():setFlag("visible", true) -- GREATBOOKKEY.scr:57
        ctx:self():setFlag("solid", true) -- GREATBOOKKEY.scr:58
        ctx:self():setFlag("gravity", true) -- GREATBOOKKEY.scr:59
        do return ctx:exit("") end -- GREATBOOKKEY.scr:60
    else -- GREATBOOKKEY.scr:61
        ctx:self():setFlag("visible", false) -- GREATBOOKKEY.scr:62
        ctx:self():setFlag("solid", false) -- GREATBOOKKEY.scr:63
        ctx:self():setFlag("gravity", false) -- GREATBOOKKEY.scr:64
        do return ctx:exit("") end -- GREATBOOKKEY.scr:65
    end -- GREATBOOKKEY.scr:66
    do return ctx:exit("") end -- GREATBOOKKEY.scr:67
end

script.labels["Main"] = function(ctx)
    -- GREATBOOKKEY.scr:70
    -- traceon
    ctx:addTrigger("Use", "OnUse") -- GREATBOOKKEY.scr:74
    ctx:addTrigger("appear", "OnAppear") -- GREATBOOKKEY.scr:75
    mm9.gosub(script, ctx, "Init") -- GREATBOOKKEY.scr:76
    do return ctx:exit("") end -- GREATBOOKKEY.scr:77
end

return script
