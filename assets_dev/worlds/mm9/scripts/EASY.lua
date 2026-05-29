-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EASY.scr"
script.includes = {}
script.labels = {}


script.labels["GoDown"] = function(ctx)
    -- EASY.scr:3
    ctx:object("h"):setVelocity(0, -400, 0) -- EASY.scr:4
    ctx:wait(0, 15, "GoUp") -- EASY.scr:5
    do return ctx:exit("") end -- EASY.scr:6
end

script.labels["GoUp"] = function(ctx)
    -- EASY.scr:9
    ctx:object("h"):setVelocity(0, 400, 0) -- EASY.scr:10
    ctx:wait(0, 15, "GoDown") -- EASY.scr:11
    do return ctx:exit("") end -- EASY.scr:12
end

script.labels["Main"] = function(ctx)
    -- EASY.scr:14
    ctx:state().h = ctx:self() -- EASY.scr:15
    ctx:wait(0, 2, "GoUp") -- EASY.scr:16
    do return ctx:exit("") end -- EASY.scr:17
end

return script
