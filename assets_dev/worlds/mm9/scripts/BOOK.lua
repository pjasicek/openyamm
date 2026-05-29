-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- book.scr
-- timmy
-- Handles the book's multiple animation
script.labels["OnUse"] = function(ctx)
    -- BOOK.scr:12
    if ctx:condition("counter==0") then -- BOOK.scr:15
        ctx:self():playAnimation("OpenBook") -- BOOK.scr:17
        ctx:state().counter = (tonumber(ctx:state().counter) or 0) + 1 -- BOOK.scr:18
        do return ctx:exit("") end -- BOOK.scr:19
    end -- BOOK.scr:20
    if ctx:condition("counter==1") then -- BOOK.scr:22
        ctx:self():playAnimation("TurnPage") -- BOOK.scr:23
        ctx:state().counter = (tonumber(ctx:state().counter) or 0) + 1 -- BOOK.scr:24
        do return ctx:exit("") end -- BOOK.scr:25
    end -- BOOK.scr:26
    if ctx:condition("counter==2") then -- BOOK.scr:28
        ctx:self():playAnimation("TurnBack") -- BOOK.scr:29
        ctx:state().counter = (tonumber(ctx:state().counter) or 0) + 1 -- BOOK.scr:30
        do return ctx:exit("") end -- BOOK.scr:31
    end -- BOOK.scr:32
    if ctx:condition("Counter>=3") then -- BOOK.scr:34
        ctx:self():playAnimation("Closebook") -- BOOK.scr:35
        ctx:state().counter = 0 -- BOOK.scr:36
        do return ctx:exit("") end -- BOOK.scr:37
    end -- BOOK.scr:38
end

script.labels["Main"] = function(ctx)
    -- BOOK.scr:44
    ctx:state().counter = 0 -- BOOK.scr:49
    ctx:addTrigger("Use", "OnUse") -- BOOK.scr:50
    do return ctx:exit("") end -- BOOK.scr:51
end

return script
