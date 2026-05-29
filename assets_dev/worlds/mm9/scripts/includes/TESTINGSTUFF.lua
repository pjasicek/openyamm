-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TESTINGSTUFF.inc"
script.includes = {}
script.labels = {}


script.labels["CompleteIsleOfAshes"] = function(ctx)
    -- TESTINGSTUFF.inc:22
    ctx:giveKey("ISLE_KEY_YRSAFOUND") -- TESTINGSTUFF.inc:23
    ctx:giveKey("ISLE_KEY_YESDRAGONFLIES") -- TESTINGSTUFF.inc:24
    ctx:giveKey("ISLE_KEY_NODRAGONFLIES") -- TESTINGSTUFF.inc:25
    ctx:giveKey("ISLE_KEY_YRSATALK") -- TESTINGSTUFF.inc:26
    ctx:giveKey("ISLE_KEY_XPDRAGONFLIES") -- TESTINGSTUFF.inc:27
    ctx:giveKey("ISLE_KEY_XPYRSAQUEST") -- TESTINGSTUFF.inc:28
    ctx:cprint("You must still:") -- TESTINGSTUFF.inc:30
    ctx:cprint("Pickup Forad and read the book") -- TESTINGSTUFF.inc:31
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:33
end

-- GiveKey ISLE_KEY_NOBLOWUPCAVE
-- GiveKey ISLE_KEY_FORADDARREJOIN
-- GiveKey ISLE_KEY_XPFORADDARREJOIN
-- GiveKey ISLE_KEY_YESBLOWUPCAVE
script.labels["MaxOutAll"] = function(ctx)
    -- TESTINGSTUFF.inc:40
    mm9.gosub(script, ctx, "MaxOutMight") -- TESTINGSTUFF.inc:41
    mm9.gosub(script, ctx, "MaxOutMagic") -- TESTINGSTUFF.inc:42
    mm9.gosub(script, ctx, "MaxOutEndurance") -- TESTINGSTUFF.inc:43
    mm9.gosub(script, ctx, "MaxOutAccuracy") -- TESTINGSTUFF.inc:44
    mm9.gosub(script, ctx, "MaxOutSpeed") -- TESTINGSTUFF.inc:45
    mm9.gosub(script, ctx, "MaxOutLuck") -- TESTINGSTUFF.inc:46
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:47
end

script.labels["ZeroOutAll"] = function(ctx)
    -- TESTINGSTUFF.inc:49
    mm9.gosub(script, ctx, "ZeroOutMight") -- TESTINGSTUFF.inc:50
    mm9.gosub(script, ctx, "ZeroOutMagic") -- TESTINGSTUFF.inc:51
    mm9.gosub(script, ctx, "ZeroOutEndurance") -- TESTINGSTUFF.inc:52
    mm9.gosub(script, ctx, "ZeroOutAccuracy") -- TESTINGSTUFF.inc:53
    mm9.gosub(script, ctx, "ZeroOutSpeed") -- TESTINGSTUFF.inc:54
    mm9.gosub(script, ctx, "ZeroOutLuck") -- TESTINGSTUFF.inc:55
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:56
end

script.labels["MaxOutMight"] = function(ctx)
    -- TESTINGSTUFF.inc:58
    ctx:getAttribute("STAT_MIGHT", "nTemp") -- TESTINGSTUFF.inc:59
    ctx:set("nTemp", "MAX_STAT - nTemp") -- TESTINGSTUFF.inc:60
    ctx:giveAttribute("STAT_MIGHT", "nTemp", 1, 0) -- TESTINGSTUFF.inc:61
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:62
end

script.labels["MaxOutMagic"] = function(ctx)
    -- TESTINGSTUFF.inc:64
    ctx:getAttribute("STAT_MAGIC", "nTemp") -- TESTINGSTUFF.inc:65
    ctx:set("nTemp", "MAX_STAT - nTemp") -- TESTINGSTUFF.inc:66
    ctx:giveAttribute("STAT_MAGIC", "nTemp", 1, 0) -- TESTINGSTUFF.inc:67
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:68
end

script.labels["MaxOutEndurance"] = function(ctx)
    -- TESTINGSTUFF.inc:70
    ctx:getAttribute("STAT_ENDURANCE", "nTemp") -- TESTINGSTUFF.inc:71
    ctx:set("nTemp", "MAX_STAT - nTemp") -- TESTINGSTUFF.inc:72
    ctx:giveAttribute("STAT_ENDURANCE", "nTemp", 1, 0) -- TESTINGSTUFF.inc:73
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:74
end

script.labels["MaxOutAccuracy"] = function(ctx)
    -- TESTINGSTUFF.inc:76
    ctx:getAttribute("STAT_ACCURACY", "nTemp") -- TESTINGSTUFF.inc:77
    ctx:set("nTemp", "MAX_STAT - nTemp") -- TESTINGSTUFF.inc:78
    ctx:giveAttribute("STAT_ACCURACY", "nTemp", 1, 0) -- TESTINGSTUFF.inc:79
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:80
end

script.labels["MaxOutSpeed"] = function(ctx)
    -- TESTINGSTUFF.inc:82
    ctx:getAttribute("STAT_SPEED", "nTemp") -- TESTINGSTUFF.inc:83
    ctx:set("nTemp", "MAX_STAT - nTemp") -- TESTINGSTUFF.inc:84
    ctx:giveAttribute("STAT_SPEED", "nTemp", 1, 0) -- TESTINGSTUFF.inc:85
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:86
end

script.labels["MaxOutLuck"] = function(ctx)
    -- TESTINGSTUFF.inc:88
    ctx:getAttribute("STAT_LUCK", "nTemp") -- TESTINGSTUFF.inc:89
    ctx:set("nTemp", "MAX_STAT - nTemp") -- TESTINGSTUFF.inc:90
    ctx:giveAttribute("STAT_LUCK", "nTemp", 1, 0) -- TESTINGSTUFF.inc:91
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:92
end

script.labels["ZeroOutMight"] = function(ctx)
    -- TESTINGSTUFF.inc:94
    ctx:getAttribute("STAT_MIGHT", "nTemp") -- TESTINGSTUFF.inc:95
    ctx:set("nTemp", "-1 * MAX_STAT + nTemp") -- TESTINGSTUFF.inc:96
    ctx:giveAttribute("STAT_MIGHT", "nTemp", 1, 0) -- TESTINGSTUFF.inc:97
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:98
end

script.labels["ZeroOutMagic"] = function(ctx)
    -- TESTINGSTUFF.inc:100
    ctx:getAttribute("STAT_MAGIC", "nTemp") -- TESTINGSTUFF.inc:101
    ctx:set("nTemp", "-1 * MAX_STAT + nTemp") -- TESTINGSTUFF.inc:102
    ctx:giveAttribute("STAT_MAGIC", "nTemp", 1, 0) -- TESTINGSTUFF.inc:103
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:104
end

script.labels["ZeroOutEndurance"] = function(ctx)
    -- TESTINGSTUFF.inc:106
    ctx:getAttribute("STAT_ENDURANCE", "nTemp") -- TESTINGSTUFF.inc:107
    ctx:set("nTemp", "-1 * MAX_STAT + nTemp") -- TESTINGSTUFF.inc:108
    ctx:giveAttribute("STAT_ENDURANCE", "nTemp", 1, 0) -- TESTINGSTUFF.inc:109
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:110
end

script.labels["ZeroOutAccuracy"] = function(ctx)
    -- TESTINGSTUFF.inc:112
    ctx:getAttribute("STAT_ACCURACY", "nTemp") -- TESTINGSTUFF.inc:113
    ctx:set("nTemp", "-1 * MAX_STAT + nTemp") -- TESTINGSTUFF.inc:114
    ctx:giveAttribute("STAT_ACCURACY", "nTemp", 1, 0) -- TESTINGSTUFF.inc:115
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:116
end

script.labels["ZeroOutSpeed"] = function(ctx)
    -- TESTINGSTUFF.inc:118
    ctx:getAttribute("STAT_SPEED", "nTemp") -- TESTINGSTUFF.inc:119
    ctx:set("nTemp", "-1 * MAX_STAT + nTemp") -- TESTINGSTUFF.inc:120
    ctx:giveAttribute("STAT_SPEED", "nTemp", 1, 0) -- TESTINGSTUFF.inc:121
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:122
end

script.labels["ZeroOutLuck"] = function(ctx)
    -- TESTINGSTUFF.inc:124
    ctx:getAttribute("STAT_LUCK", "nTemp") -- TESTINGSTUFF.inc:125
    ctx:set("nTemp", "-1 * MAX_STAT + nTemp") -- TESTINGSTUFF.inc:126
    ctx:giveAttribute("STAT_LUCK", "nTemp", 1, 0) -- TESTINGSTUFF.inc:127
    do return ctx:exit(1) end -- TESTINGSTUFF.inc:128
end

return script
