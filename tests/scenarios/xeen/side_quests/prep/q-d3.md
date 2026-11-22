# Prep: Q-D3 The Drawkcab Way

Scenario `q-d3_drawkcab_way.yml`. Quest file `source/quests/q-d3.yml` (qbits 113060-113066, autonotes 4430 lessons,
4431 Reger, award 443); hooks `q-d3.reger_door`, `reger_word`, `reger_wrong`, `drawkcab_sign`. Routes: D1's L4
`playtest.yml` (the sign, the four cells, Reger's door). Promotion `drawkcab` = Initiate -> Master (xeen_common.lua).
Story precondition: M20 started (111400, Dimitri's key, chain segment 59), set by console after the refusal.

| what | where | how / text |
| --- | --- | --- |
| the sign, D1 event 146 | thing at grid (55.9, 61.35) = (-4147, 1357); stand (-4147, 1700, 1152) yaw -pi/2 | "The Drawkcab Monks study the Palindrome." |
| Otto 4473 / Hannah 4474 / Bob 4475 / Ada 4476 | stand (-3584 / -3072 / -2560 / -2048, 1516, 1152) yaw -pi/2, use: the resident's talk | "Lesson": out of order "Order wrong the. Otto first, Brother. Lesson one."; Otto: started, lesson1, autonote 4430; Hannah lesson2; Bob lesson3; Ada member 113064, award 443, autonote 4431, 2,000 XP each; each again "Learned you have..." / Ada "The word say: palindrome." |
| Reger's door, D1 event 99 (house 4500) | stand (-3328, -15892, 1023) yaw -pi/2, use | non-member: the fail text "Wrong. Go visit the monks..."; member: AskQuestion "What's the word?" (palindrome, palindromes): right "Come in. Ni emoc." (word_said 113065), wrong "WRONG!!! You call yourself a Drawkcab..."; after word_said the door enters house 4500 (Reger's talk) |
| Reger (NPC 4950) | his cell | "The word": word_said without M20 "Masters, though, ready not yet are you."; with M20 "Correct. You are truly a Drawkcab!..." (done 113066, 9,000 XP each, promote drawkcab); done "Pleased to see you, fellow Drawkcabs." |

Asserts: starting bits clear, the sign, both refusals, every lesson and its repeat, both autonotes, the award for all
four, 2,000 + 9,000 XP per member, the refusal before M20 (no promotion), Initiate -> Master only.
