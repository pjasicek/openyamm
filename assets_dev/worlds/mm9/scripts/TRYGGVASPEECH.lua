-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRYGGVASPEECH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- tryggvaspeech.scr
-- By Timmy
-- handles tryggva the hammers audio stuff
-- number of animation to play
script.labels["Onblabber"] = function(ctx)
    -- TRYGGVASPEECH.scr:16
    -- pick and play a soundfile
    if ctx:condition("bSpeak==0") then -- TRYGGVASPEECH.scr:20
        ctx:randomInt(1, 4, "g_ntemp") -- TRYGGVASPEECH.scr:21
        ctx:state().bSpeak = 1 -- TRYGGVASPEECH.scr:22
        if ctx:condition("g_ntemp==1") then -- TRYGGVASPEECH.scr:23
            ctx:playSound("\\voices\\cinema\\Tryygva01.wav", "OnDrink", 100, 512, "FALSE", 100) -- TRYGGVASPEECH.scr:24
            ctx:self():loopAnimation("conv1", 0, "DoNothing") -- TRYGGVASPEECH.scr:25
            do return ctx:exit("") end -- TRYGGVASPEECH.scr:26
        end -- TRYGGVASPEECH.scr:27
        if ctx:condition("g_ntemp==2") then -- TRYGGVASPEECH.scr:29
            ctx:playSound("\\voices\\cinema\\Tryygva02.wav", "OnDrink", 100, 512, "FALSE", 100) -- TRYGGVASPEECH.scr:31
            ctx:self():loopAnimation("conv1", 0, "DoNothing") -- TRYGGVASPEECH.scr:32
            do return ctx:exit("") end -- TRYGGVASPEECH.scr:33
        end -- TRYGGVASPEECH.scr:34
        if ctx:condition("g_ntemp==3") then -- TRYGGVASPEECH.scr:36
            ctx:playSound("\\voices\\cinema\\Tryygva03.wav", "OnDrink", 100, 512, "FALSE", 100) -- TRYGGVASPEECH.scr:38
            ctx:self():loopAnimation("conv1", 0, "DoNothing") -- TRYGGVASPEECH.scr:39
            do return ctx:exit("") end -- TRYGGVASPEECH.scr:40
        end -- TRYGGVASPEECH.scr:41
        if ctx:condition("g_ntemp==4") then -- TRYGGVASPEECH.scr:43
            ctx:playSound("\\voices\\cinema\\Tryygva04.wav", "OnDrink", 100, 512, "FALSE", 100) -- TRYGGVASPEECH.scr:45
            ctx:self():loopAnimation("conv1", 0, "DoNothing") -- TRYGGVASPEECH.scr:46
            do return ctx:exit("") end -- TRYGGVASPEECH.scr:47
        end -- TRYGGVASPEECH.scr:48
    end -- TRYGGVASPEECH.scr:49
    do return ctx:exit("") end -- TRYGGVASPEECH.scr:50
end

script.labels["OnUse"] = function(ctx)
    -- TRYGGVASPEECH.scr:54
    do return ctx:exit("") end -- TRYGGVASPEECH.scr:57
end

script.labels["Ondrink"] = function(ctx)
    -- TRYGGVASPEECH.scr:60
    -- takes a drink (adds an extra 5 second wait)
    ctx:self():loopAnimation("poundfist", 1, "DoNothing") -- TRYGGVASPEECH.scr:65
    ctx:state().bSpeak = 0 -- TRYGGVASPEECH.scr:66
    ctx:wait(1, 5, "DoNothing") -- TRYGGVASPEECH.scr:67
    do return ctx:exit("") end -- TRYGGVASPEECH.scr:68
end

script.labels["Off"] = function(ctx)
    -- TRYGGVASPEECH.scr:72
    ctx:randomInt(1, 4, "anim") -- TRYGGVASPEECH.scr:75
    if ctx:condition("anim==1") then -- TRYGGVASPEECH.scr:77
        ctx:self():playAnimation("fidget1", "Anim") -- TRYGGVASPEECH.scr:78
        do return ctx:exit("") end -- TRYGGVASPEECH.scr:79
    end -- TRYGGVASPEECH.scr:80
    if ctx:condition("anim==2") then -- TRYGGVASPEECH.scr:82
        ctx:self():playAnimation("fidget2", "Anim") -- TRYGGVASPEECH.scr:83
        do return ctx:exit("") end -- TRYGGVASPEECH.scr:84
    end -- TRYGGVASPEECH.scr:85
    if ctx:condition("anim==3") then -- TRYGGVASPEECH.scr:87
        ctx:self():playAnimation("fidget3", "Anim") -- TRYGGVASPEECH.scr:88
        do return ctx:exit("") end -- TRYGGVASPEECH.scr:89
    end -- TRYGGVASPEECH.scr:90
    if ctx:condition("anim==4") then -- TRYGGVASPEECH.scr:92
        ctx:self():playAnimation("fidget4", "Anim") -- TRYGGVASPEECH.scr:93
        do return ctx:exit("") end -- TRYGGVASPEECH.scr:94
    end -- TRYGGVASPEECH.scr:95
    do return ctx:exit("") end -- TRYGGVASPEECH.scr:97
end

script.labels["Anim"] = function(ctx)
    -- TRYGGVASPEECH.scr:102
    ctx:self():loopAnimation("listen", 0, "Donothing") -- TRYGGVASPEECH.scr:105
    do return ctx:exit("") end -- TRYGGVASPEECH.scr:107
end

script.labels["Main"] = function(ctx)
    -- TRYGGVASPEECH.scr:111
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- TRYGGVASPEECH.scr:115
    ctx:state().anim = 1 -- TRYGGVASPEECH.scr:118
    ctx:state().g_ntemp = 0 -- TRYGGVASPEECH.scr:119
    do return mm9.gotoLabel(script, ctx, "anim") end -- TRYGGVASPEECH.scr:120
    do return ctx:exit("") end -- TRYGGVASPEECH.scr:121
end

return script
