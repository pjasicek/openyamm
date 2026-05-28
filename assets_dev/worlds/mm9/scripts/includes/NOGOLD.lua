-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NOGOLD.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NoGold.inc
-- timmy
-- handles Hjarrrand Fixer voice and quest stuff
-- flag variables
-- Init all the voice variables
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["NoGold"] = function(ctx)
    -- NOGOLD.inc:81
    ctx:command("getrandomint", "1,2 g_ntemp") -- NOGOLD.inc:86
    if ctx:condition("g_ntemp==1") then -- NOGOLD.inc:87
        ctx:command("playsound", "sVoice1, DoNothing, 100, 240, FALSE, 100") -- NOGOLD.inc:88
    else -- NOGOLD.inc:89
        ctx:command("playsound", "sVoice2, DoNothing, 100, 240, FALSE, 100") -- NOGOLD.inc:90
    end -- NOGOLD.inc:91
    do return ctx:exit("") end -- NOGOLD.inc:92
end

script.labels["VoiceInit"] = function(ctx)
    -- NOGOLD.inc:99
    ctx:command("getpcvoice", "g_ntemp") -- NOGOLD.inc:104
    if ctx:condition("g_ntemp==0") then -- NOGOLD.inc:107
        ctx:command("set", "sVoice1 sAngryFa") -- NOGOLD.inc:108
        ctx:command("set", "sVoice2 sAngryFb") -- NOGOLD.inc:109
        do return ctx:exit("") end -- NOGOLD.inc:110
    end -- NOGOLD.inc:111
    if ctx:condition("g_ntemp==1") then -- NOGOLD.inc:113
        ctx:command("set", "sVoice1 sArrogantFa") -- NOGOLD.inc:114
        ctx:command("set", "sVoice2 sArrogantFb") -- NOGOLD.inc:115
        do return ctx:exit("") end -- NOGOLD.inc:116
    end -- NOGOLD.inc:117
    if ctx:condition("g_ntemp==2") then -- NOGOLD.inc:119
        ctx:command("set", "sVoice1 sAssertiveFa") -- NOGOLD.inc:120
        ctx:command("set", "sVoice2 sAssertiveFb") -- NOGOLD.inc:121
        do return ctx:exit("") end -- NOGOLD.inc:122
    end -- NOGOLD.inc:123
    if ctx:condition("g_ntemp==3") then -- NOGOLD.inc:125
        ctx:command("set", "sVoice1 sCowardlyFa") -- NOGOLD.inc:126
        ctx:command("set", "sVoice2 sCowardlyFb") -- NOGOLD.inc:127
        do return ctx:exit("") end -- NOGOLD.inc:128
    end -- NOGOLD.inc:129
    if ctx:condition("g_ntemp==4") then -- NOGOLD.inc:131
        ctx:command("set", "sVoice1 sDimFa") -- NOGOLD.inc:132
        ctx:command("set", "sVoice2 sDimFb") -- NOGOLD.inc:133
        do return ctx:exit("") end -- NOGOLD.inc:134
    end -- NOGOLD.inc:135
    if ctx:condition("g_ntemp==5") then -- NOGOLD.inc:137
        ctx:command("set", "sVoice1 sHappyFa") -- NOGOLD.inc:138
        ctx:command("set", "sVoice2 sHappyFb") -- NOGOLD.inc:139
        do return ctx:exit("") end -- NOGOLD.inc:140
    end -- NOGOLD.inc:141
    if ctx:condition("g_ntemp==6") then -- NOGOLD.inc:143
        ctx:command("set", "sVoice1 sSarcasticFa") -- NOGOLD.inc:144
        ctx:command("set", "sVoice2 sSarcasticFb") -- NOGOLD.inc:145
        do return ctx:exit("") end -- NOGOLD.inc:146
    end -- NOGOLD.inc:147
    if ctx:condition("g_ntemp==7") then -- NOGOLD.inc:149
        ctx:command("set", "sVoice1 sLichFa") -- NOGOLD.inc:150
        ctx:command("set", "sVoice2 sLichFb") -- NOGOLD.inc:151
        do return ctx:exit("") end -- NOGOLD.inc:152
    end -- NOGOLD.inc:153
    if ctx:condition("g_ntemp==8") then -- NOGOLD.inc:155
        ctx:command("set", "sVoice1 sHalfOrcLichFa") -- NOGOLD.inc:156
        ctx:command("set", "sVoice2 sHalfOrcLichFb") -- NOGOLD.inc:157
        do return ctx:exit("") end -- NOGOLD.inc:158
    end -- NOGOLD.inc:159
    if ctx:condition("g_ntemp==9") then -- NOGOLD.inc:161
        ctx:command("set", "sVoice1 sAngryMa") -- NOGOLD.inc:162
        ctx:command("set", "sVoice2 sAngryMb") -- NOGOLD.inc:163
        do return ctx:exit("") end -- NOGOLD.inc:164
    end -- NOGOLD.inc:165
    if ctx:condition("g_ntemp==10") then -- NOGOLD.inc:167
        ctx:command("set", "sVoice1 sArrogantMa") -- NOGOLD.inc:168
        ctx:command("set", "sVoice2 sArrogantMb") -- NOGOLD.inc:169
        do return ctx:exit("") end -- NOGOLD.inc:170
    end -- NOGOLD.inc:171
    if ctx:condition("g_ntemp==11") then -- NOGOLD.inc:173
        ctx:command("set", "sVoice1 sAssertiveMa") -- NOGOLD.inc:174
        ctx:command("set", "sVoice2 sAssertiveMb") -- NOGOLD.inc:175
    end -- NOGOLD.inc:176
    if ctx:condition("g_ntemp==12") then -- NOGOLD.inc:178
        ctx:command("set", "sVoice1 sCowardlyMa") -- NOGOLD.inc:179
        ctx:command("set", "sVoice2 sCowardlyMb") -- NOGOLD.inc:180
        do return ctx:exit("") end -- NOGOLD.inc:181
    end -- NOGOLD.inc:182
    if ctx:condition("g_ntemp==13") then -- NOGOLD.inc:184
        ctx:command("set", "sVoice1 sDimMa") -- NOGOLD.inc:185
        ctx:command("set", "sVoice2 sDimMb") -- NOGOLD.inc:186
        do return ctx:exit("") end -- NOGOLD.inc:187
    end -- NOGOLD.inc:188
    if ctx:condition("g_ntemp==14") then -- NOGOLD.inc:190
        ctx:command("set", "sVoice1 sHappyMa") -- NOGOLD.inc:191
        ctx:command("set", "sVoice2 sHappyMb") -- NOGOLD.inc:192
        do return ctx:exit("") end -- NOGOLD.inc:193
    end -- NOGOLD.inc:194
    if ctx:condition("g_ntemp==15") then -- NOGOLD.inc:196
        ctx:command("set", "sVoice1 sSarcasticMa") -- NOGOLD.inc:197
        ctx:command("set", "sVoice2 sSarcasticMb") -- NOGOLD.inc:198
        do return ctx:exit("") end -- NOGOLD.inc:199
    end -- NOGOLD.inc:200
    if ctx:condition("g_ntemp==16") then -- NOGOLD.inc:202
        ctx:command("set", "sVoice1 sLichMa") -- NOGOLD.inc:203
        ctx:command("set", "sVoice2 sLichMb") -- NOGOLD.inc:204
        do return ctx:exit("") end -- NOGOLD.inc:205
    end -- NOGOLD.inc:206
    if ctx:condition("g_ntemp==17") then -- NOGOLD.inc:208
        ctx:command("set", "sVoice1 sHalfOrcLichMa") -- NOGOLD.inc:209
        ctx:command("set", "sVoice2 sHalfOrcLichMb") -- NOGOLD.inc:210
        do return ctx:exit("") end -- NOGOLD.inc:211
    end -- NOGOLD.inc:212
    do return ctx:exit("") end -- NOGOLD.inc:214
end

return script
