-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASLISK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- Baslisk.scr
-- timmy
-- handles giving the player the baslisk skin
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnUse"] = function(ctx)
    -- BASLISK.scr:22
    -- merc to gladiator Quest
    if not ctx:hasKey(215) then -- BASLISK.scr:27-28
        if ctx:hasKey(214) then -- BASLISK.scr:29-30
            ctx:giveKey(215) -- BASLISK.scr:31
            ctx:giveItem(380) -- BASLISK.scr:32
            do return ctx:exit("") end -- BASLISK.scr:33
        end -- BASLISK.scr:34
    end -- BASLISK.scr:35
    -- NOTE: this gives the waiting key outright.
    -- The player should have to kill the baslisk to get the skin
    -- End merc to gladiator quest
    do return ctx:exit("") end -- BASLISK.scr:42
end

script.labels["OnExit"] = function(ctx)
    -- BASLISK.scr:48
    do return ctx:exit("") end -- BASLISK.scr:51
end

script.labels["Main"] = function(ctx)
    -- BASLISK.scr:54
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- BASLISK.scr:62
    do return ctx:exit("") end -- BASLISK.scr:64
end

return script
