-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOOKLETTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- BookLetter.scr
-- 9/21
-- timmy
-- handles Books and scrolls doing Letter interface
script.labels["OnUse"] = function(ctx)
    -- BOOKLETTER.scr:16
    -- this opens the book
    if ctx:condition("open==false") then -- BOOKLETTER.scr:21
        if ctx:condition("Item_Type!=letter") then -- BOOKLETTER.scr:22
            ctx:self():playAnimation("Openbook") -- BOOKLETTER.scr:23
            ctx:playSound("Sounds\\Events\\bookopen.wav", "DoNothing", 256, 2048, "FALSE", 100) -- BOOKLETTER.scr:24
            ctx:state().Open = true -- BOOKLETTER.scr:25
            ctx:wait(0, 1, "Letter") -- BOOKLETTER.scr:26
            do return ctx:exit("") end -- BOOKLETTER.scr:27
        else -- BOOKLETTER.scr:28
            ctx:doLetter("Item_Id") -- BOOKLETTER.scr:29
            ctx:playSound("Sounds\\Events\\bookopen.wav", "DoNothing", 256, 2048, "FALSE", 100) -- BOOKLETTER.scr:30
            do return ctx:exit("") end -- BOOKLETTER.scr:31
        end -- BOOKLETTER.scr:32
        do return ctx:exit("") end -- BOOKLETTER.scr:33
    end -- BOOKLETTER.scr:34
    do return ctx:exit("") end -- BOOKLETTER.scr:35
end

script.labels["Letter"] = function(ctx)
    -- BOOKLETTER.scr:38
    -- this does the letter interface
    ctx:doLetter("Item_Id") -- BOOKLETTER.scr:43
    ctx:wait(0, 5, "close") -- BOOKLETTER.scr:44
    do return ctx:exit("") end -- BOOKLETTER.scr:45
end

script.labels["Init"] = function(ctx)
    -- BOOKLETTER.scr:48
    if ctx:condition("bDown==TRUE") then -- BOOKLETTER.scr:51
        ctx:self():loopAnimation("Down", 0, "DoNothing") -- BOOKLETTER.scr:52
        do return ctx:exit("") end -- BOOKLETTER.scr:53
    end -- BOOKLETTER.scr:54
    do return ctx:exit("") end -- BOOKLETTER.scr:55
end

script.labels["Close"] = function(ctx)
    -- BOOKLETTER.scr:58
    ctx:self():playAnimation("closebook") -- BOOKLETTER.scr:61
    ctx:playSound("Sounds\\Events\\bookclose.wav", "DoNothing", 256, 2048, "FALSE", 100) -- BOOKLETTER.scr:62
    ctx:state().Open = false -- BOOKLETTER.scr:63
    do return ctx:exit("") end -- BOOKLETTER.scr:64
end

script.labels["Main"] = function(ctx)
    -- BOOKLETTER.scr:66
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "Item_ID") -- BOOKLETTER.scr:71
    ctx:getParam(1, "Item_Type") -- BOOKLETTER.scr:72
    ctx:getParam(2, "bDown") -- BOOKLETTER.scr:73
    ctx:addTrigger("Use", "OnUse") -- BOOKLETTER.scr:74
    ctx:state().Open = false -- BOOKLETTER.scr:75
    ctx:onEvent("OnPostStartWorld", "Init") -- BOOKLETTER.scr:76
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- BOOKLETTER.scr:77
    ctx:onEvent("OnPostSaveLoad", "Init") -- BOOKLETTER.scr:78
    ctx:wait(1, .1, "Init") -- BOOKLETTER.scr:79
    do return ctx:exit("") end -- BOOKLETTER.scr:80
end

return script
