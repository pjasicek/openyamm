-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STRENGTHTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- strengthtest.scr
-- By Timmy
-- handles the strength game the the thing and the gathering.
script.labels["OnUse"] = function(ctx)
    -- STRENGTHTEST.scr:17
    if not ctx:hasKey(1002) then -- STRENGTHTEST.scr:19-20
        do return ctx:exit("") end -- STRENGTHTEST.scr:21
    end -- STRENGTHTEST.scr:22
    ctx:takeKey(1002) -- STRENGTHTEST.scr:24
    ctx:takeItem(557) -- STRENGTHTEST.scr:25
    ctx:randomInt(80, 125, "dingbell") -- STRENGTHTEST.scr:27
    ctx:randomInt(1, 100, "TimingVal") -- STRENGTHTEST.scr:28
    ctx:getAttribute(0, "Player_Strength") -- STRENGTHTEST.scr:29
    ctx:add("TimingVal", "Player_Strength") -- STRENGTHTEST.scr:31
    -- delete this
    ctx:state().TimingVal = (tonumber(ctx:state().TimingVal) or 0) + 50 -- STRENGTHTEST.scr:35
    if ctx:condition("timingVal>=dingbell") then -- STRENGTHTEST.scr:38
        if not ctx:hasKey(94) then -- STRENGTHTEST.scr:40-41
            ctx:giveItem(395) -- STRENGTHTEST.scr:42
            ctx:giveKey(94) -- STRENGTHTEST.scr:43
            ctx:giveKey(1003) -- STRENGTHTEST.scr:44
            do return ctx:exit("") end -- STRENGTHTEST.scr:46
        end -- STRENGTHTEST.scr:47
    else -- STRENGTHTEST.scr:48
    end -- STRENGTHTEST.scr:50
    do return ctx:exit("") end -- STRENGTHTEST.scr:52
end

script.labels["OnRing"] = function(ctx)
    -- STRENGTHTEST.scr:56
    if ctx:condition("timingVal>=dingbell") then -- STRENGTHTEST.scr:58
        ctx:playSound("Sounds\\Events\\dingbell.wav", "Onexit", 100, 2400, "FALSE", 100) -- STRENGTHTEST.scr:59
        ctx:rolloverText(6, 1, 3, 2) -- STRENGTHTEST.scr:60
        do return ctx:exit("") end -- STRENGTHTEST.scr:61
    end -- STRENGTHTEST.scr:62
    ctx:rolloverText(7, 1, 3, 2) -- STRENGTHTEST.scr:63
    do return ctx:exit("") end -- STRENGTHTEST.scr:64
end

script.labels["Onexit"] = function(ctx)
    -- STRENGTHTEST.scr:66
    do return ctx:exit("") end -- STRENGTHTEST.scr:70
end

script.labels["Main"] = function(ctx)
    -- STRENGTHTEST.scr:73
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "OnUse") -- STRENGTHTEST.scr:77
    ctx:addTrigger("ring", "OnRing") -- STRENGTHTEST.scr:78
    do return ctx:exit("") end -- STRENGTHTEST.scr:80
end

return script
