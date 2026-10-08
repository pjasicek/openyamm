-- Native MM6 gold bags award 50 gold plus a random 1..200, then disappear.
ReplaceGlobalEvent(1747, "Bag of Gold", function()
    AddValue(Gold, 50 + evt.RandomBetween(1, 200))
    evt.ChangeEvent(0)
end)
