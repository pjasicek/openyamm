-- Use the merged Thunderfist Mountain entrance record for the surface doors.
ReplaceMapEvent(501, nil, function()
    evt.MoveToMap(-1024, 768, 4097, 1792, 0, 0, 406, 1, "7d07.blv")
end)

ReplaceMapEvent(503, nil, function()
    evt.MoveToMap(9960, 1443, 390, 1936, 0, 0, 406, 1, "7d07.blv")
end)

ReplaceMapEvent(504, nil, function()
    evt.MoveToMap(-11058, 4858, 3969, 148, 0, 0, 406, 1, "7d07.blv")
end)

ReplaceMapEvent(505, nil, function()
    evt.MoveToMap(11471, -3498, 2814, 414, 0, 0, 406, 1, "7d07.blv")
end)
