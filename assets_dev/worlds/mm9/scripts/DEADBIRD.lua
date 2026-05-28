-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DEADBIRD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- deadbird.scr
-- timmy
-- handles kill 10 birds for ranger promo
script.labels["OnDeath"] = function(ctx)
    -- DEADBIRD.scr:13
    if not ctx:hasKey(241) then -- DEADBIRD.scr:16-17
        if ctx:condition("g_ncounter>=10") then -- DEADBIRD.scr:18
            ctx:giveKey(241) -- DEADBIRD.scr:19
            do return ctx:exit("") end -- DEADBIRD.scr:20
        else -- DEADBIRD.scr:21
            ctx:command("add", "g_ncounter, 1") -- DEADBIRD.scr:22
            do return ctx:exit("") end -- DEADBIRD.scr:23
        end -- DEADBIRD.scr:24
    end -- DEADBIRD.scr:25
    do return ctx:exit("") end -- DEADBIRD.scr:26
end

script.labels["OnExit"] = function(ctx)
    -- DEADBIRD.scr:29
    do return ctx:exit("") end -- DEADBIRD.scr:32
end

script.labels["Main"] = function(ctx)
    -- DEADBIRD.scr:35
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("ondeath", "OnDeath") -- DEADBIRD.scr:40
    ctx:command("set", "g_ncounter, 0") -- DEADBIRD.scr:41
    -- for debug..delete
    ctx:addTrigger("use", "Ondeath") -- DEADBIRD.scr:44
    do return ctx:exit("") end -- DEADBIRD.scr:47
end

return script
