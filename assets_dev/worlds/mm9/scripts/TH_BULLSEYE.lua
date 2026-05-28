-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_BULLSEYE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Flags.inc" }

-- TH_BullsEye.scr
-- Karl Drown 11-15-01
-- shoot the target's bulleye and get rewarded.
script.labels["Done"] = function(ctx)
    -- TH_BULLSEYE.scr:34
    ctx:command("ondamage", "DoNothing") -- TH_BULLSEYE.scr:37
    ctx:command("removetrigger", "Done") -- TH_BULLSEYE.scr:38
    do return ctx:exit("True") end -- TH_BULLSEYE.scr:40
end

script.labels["TurnOn"] = function(ctx)
    -- TH_BULLSEYE.scr:43
    ctx:command("getmyhandle", "hDummy") -- TH_BULLSEYE.scr:46
    ctx:command("setflag", "hDummy, FLAG_SOLID") -- TH_BULLSEYE.scr:47
    do return ctx:exit("True") end -- TH_BULLSEYE.scr:49
end

script.labels["TurnOff"] = function(ctx)
    -- TH_BULLSEYE.scr:51
    ctx:command("getmyhandle", "hDummy") -- TH_BULLSEYE.scr:54
    ctx:command("clearflag", "hDummy, FLAG_SOLID") -- TH_BULLSEYE.scr:55
    do return ctx:exit("True") end -- TH_BULLSEYE.scr:57
end

script.labels["StopHere"] = function(ctx)
    -- TH_BULLSEYE.scr:59
    ctx:command("cprint", "StopHere") -- TH_BULLSEYE.scr:61
    -- playsound Sounds\Door\doorslammetal01.wav DoNothing 500 1000 FALSE 100
    -- GetObjectHandle sResetTrigger, hResetTrigger
    -- GetObjectHandle sCloseTrigger, hCloseTrigger
    -- RemoveObject hResetTrigger
    -- RemoveObject hCloseTrigger
    ctx:command("nloop", "= 0") -- TH_BULLSEYE.scr:71
    while ctx:condition("nLoop < 4") do -- TH_BULLSEYE.scr:73
        if ctx:condition("nLoop == 0") then -- TH_BULLSEYE.scr:74
            ctx:command("sringname", "= \"centertarget\" + nTargetNum") -- TH_BULLSEYE.scr:75
        else -- TH_BULLSEYE.scr:76
            if ctx:condition("nLoop == 1") then -- TH_BULLSEYE.scr:77
                ctx:command("sringname", "= \"FirstRing\" + nTargetNum") -- TH_BULLSEYE.scr:78
            else -- TH_BULLSEYE.scr:79
                if ctx:condition("nLoop == 2") then -- TH_BULLSEYE.scr:80
                    ctx:command("sringname", "= \"SecondRing\" + nTargetNum") -- TH_BULLSEYE.scr:81
                else -- TH_BULLSEYE.scr:82
                    if ctx:condition("nLoop == 3") then -- TH_BULLSEYE.scr:83
                        ctx:command("sringname", "= \"ThirdRing\" + nTargetNum") -- TH_BULLSEYE.scr:84
                    end -- TH_BULLSEYE.scr:85
                end -- TH_BULLSEYE.scr:86
            end -- TH_BULLSEYE.scr:87
        end -- TH_BULLSEYE.scr:88
        ctx:command("getobjecthandle", "sRingName hTrigger") -- TH_BULLSEYE.scr:89
        ctx:trigger("hTrigger", "Done") -- TH_BULLSEYE.scr:90
        ctx:command("nloop", "= nLoop + 1") -- TH_BULLSEYE.scr:91
    end -- TH_BULLSEYE.scr:92
    do return ctx:exit("TRUE") end -- TH_BULLSEYE.scr:94
end

script.labels["CloseMe"] = function(ctx)
    -- TH_BULLSEYE.scr:96
    ctx:command("playsound", "Sounds\\Events\\Gold01.wav DoNothing 500 4000 FALSE 100") -- TH_BULLSEYE.scr:98
    if ctx:condition("nRing==0") then -- TH_BULLSEYE.scr:99
        ctx:giveGold(8000) -- TH_BULLSEYE.scr:100
        ctx:command("playsound", "Sounds\\spells\\DivineIntervention.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:101
    else -- TH_BULLSEYE.scr:102
        if ctx:condition("nRing==1") then -- TH_BULLSEYE.scr:103
            ctx:giveGold(4000) -- TH_BULLSEYE.scr:104
            ctx:command("playsound", "Sounds\\spells\\phantom.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:105
        else -- TH_BULLSEYE.scr:106
            if ctx:condition("nRing==2") then -- TH_BULLSEYE.scr:107
                ctx:giveGold(2000) -- TH_BULLSEYE.scr:108
                ctx:command("playsound", "Sounds\\spells\\spellreaver.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:109
            else -- TH_BULLSEYE.scr:110
                if ctx:condition("nRing==3") then -- TH_BULLSEYE.scr:111
                    ctx:giveGold(1000) -- TH_BULLSEYE.scr:112
                    ctx:command("playsound", "Sounds\\spells\\Regeneration.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:113
                else -- TH_BULLSEYE.scr:114
                    if ctx:condition("nRing==4") then -- TH_BULLSEYE.scr:115
                        ctx:giveGold(750) -- TH_BULLSEYE.scr:116
                        ctx:command("playsound", "Sounds\\spells\\leggib.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:117
                    else -- TH_BULLSEYE.scr:118
                        if ctx:condition("nRing==5") then -- TH_BULLSEYE.scr:119
                            ctx:giveGold(500) -- TH_BULLSEYE.scr:120
                            ctx:command("playsound", "Sounds\\spells\\mine01.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:121
                        else -- TH_BULLSEYE.scr:122
                            if ctx:condition("nRing==6") then -- TH_BULLSEYE.scr:123
                                ctx:giveGold(250) -- TH_BULLSEYE.scr:124
                                ctx:command("playsound", "Sounds\\spells\\paralyze.wav DoNothing 500 1000 FALSE 100") -- TH_BULLSEYE.scr:125
                            end -- TH_BULLSEYE.scr:126
                        end -- TH_BULLSEYE.scr:127
                    end -- TH_BULLSEYE.scr:128
                end -- TH_BULLSEYE.scr:129
            end -- TH_BULLSEYE.scr:130
        end -- TH_BULLSEYE.scr:131
    end -- TH_BULLSEYE.scr:132
    ctx:command("getmyhandle", "hMe") -- TH_BULLSEYE.scr:134
    ctx:command("getobjecthandle", "sTargetObject, hDummy") -- TH_BULLSEYE.scr:135
    ctx:command("getobjecthandle", "sTrigger, hTrigger") -- TH_BULLSEYE.scr:136
    ctx:trigger("hMe", "Open") -- TH_BULLSEYE.scr:137
    ctx:trigger("hDummy", "Open") -- TH_BULLSEYE.scr:138
    ctx:trigger("hMe", "Lock") -- TH_BULLSEYE.scr:139
    ctx:trigger("hDummy", "Lock") -- TH_BULLSEYE.scr:140
    ctx:trigger("hTrigger", "Trigger") -- TH_BULLSEYE.scr:141
    mm9.gosub(script, ctx, "StopHere") -- TH_BULLSEYE.scr:142
    do return ctx:exit("") end -- TH_BULLSEYE.scr:144
end

script.labels["TargetInit"] = function(ctx)
    -- TH_BULLSEYE.scr:147
    ctx:command("getmyhandle", "hDummy") -- TH_BULLSEYE.scr:149
    ctx:command("setflag", "hDummy, FLAG_SOLID") -- TH_BULLSEYE.scr:150
    do return ctx:exit("True") end -- TH_BULLSEYE.scr:152
end

script.labels["Main"] = function(ctx)
    -- TH_BULLSEYE.scr:154
    ctx:getParam(0, "sTargetObject") -- TH_BULLSEYE.scr:156
    ctx:getParam(1, "sTrigger") -- TH_BULLSEYE.scr:157
    ctx:getParam(2, "nRing") -- TH_BULLSEYE.scr:158
    ctx:getParam(3, "sResetTrigger") -- TH_BULLSEYE.scr:159
    ctx:getParam(4, "sCloseTrigger") -- TH_BULLSEYE.scr:160
    ctx:getParam(5, "nTargetNum") -- TH_BULLSEYE.scr:161
    ctx:command("ondamage", "CloseMe") -- TH_BULLSEYE.scr:162
    ctx:addTrigger("Stop", "TurnOff") -- TH_BULLSEYE.scr:163
    ctx:addTrigger("Go", "TurnOn") -- TH_BULLSEYE.scr:164
    ctx:addTrigger("Done", "Done") -- TH_BULLSEYE.scr:165
    ctx:command("wait", "0, 2, TargetInit") -- TH_BULLSEYE.scr:166
    do return ctx:exit("") end -- TH_BULLSEYE.scr:167
end

return script
