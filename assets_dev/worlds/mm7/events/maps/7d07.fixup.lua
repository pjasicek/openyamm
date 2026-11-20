-- Use the merged transition descriptions for the two tunnel passages.
ReplaceMapEvent(505, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(9350, -1010, 1, 744, 0, 0, 675, 0, "7d35.blv")
end, "Leave Thunderfist Mountain")

ReplaceMapEvent(506, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(-437, -1078, 1, 256, 0, 0, 673, 0, "7d36.blv")
end, "Leave Thunderfist Mountain")
