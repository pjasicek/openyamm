#number		STAT_MIGHT = 0
#number		STAT_MAGIC = 1
#number		STAT_ENDURANCE = 2
#number		STAT_ACCURACY = 3
#number		STAT_SPEED = 4
#number		STAT_LUCK = 5

#number		ISLE_KEY_YRSAFOUND = 365
#number		ISLE_KEY_YESDRAGONFLIES = 7
#number		ISLE_KEY_NODRAGONFLIES = 27
#number		ISLE_KEY_YRSATALK = 1
#number		ISLE_KEY_XPDRAGONFLIES = 366
#number		ISLE_KEY_XPYRSAQUEST = 367
#number		ISLE_KEY_NOBLOWUPCAVE = 371
#number		ISLE_KEY_FORADDARREJOIN = 29
#number		ISLE_KEY_XPFORADDARREJOIN = 368
#number		ISLE_KEY_YESBLOWUPCAVE = 28

#number		MAX_STAT = 500
#number		nTemp = 0

:CompleteIsleOfAshes
	GiveKey ISLE_KEY_YRSAFOUND
	GiveKey ISLE_KEY_YESDRAGONFLIES
	GiveKey ISLE_KEY_NODRAGONFLIES
	GiveKey ISLE_KEY_YRSATALK
	GiveKey ISLE_KEY_XPDRAGONFLIES
	GiveKey ISLE_KEY_XPYRSAQUEST

cprint "You must still:"
cprint "Pickup Forad and read the book"

	exit 1

;;	GiveKey ISLE_KEY_NOBLOWUPCAVE
;;	GiveKey ISLE_KEY_FORADDARREJOIN
;;	GiveKey ISLE_KEY_XPFORADDARREJOIN
;;	GiveKey ISLE_KEY_YESBLOWUPCAVE

:MaxOutAll
	gosub MaxOutMight
	gosub MaxOutMagic
	gosub MaxOutEndurance
	gosub MaxOutAccuracy
	gosub MaxOutSpeed
	gosub MaxOutLuck
	exit 1

:ZeroOutAll
	gosub ZeroOutMight
	gosub ZeroOutMagic
	gosub ZeroOutEndurance
	gosub ZeroOutAccuracy
	gosub ZeroOutSpeed
	gosub ZeroOutLuck
	exit 1

:MaxOutMight
	GetAttribute STAT_MIGHT, nTemp
	nTemp = MAX_STAT - nTemp
	GiveAttribute STAT_MIGHT, nTemp, 1, 0
	exit 1

:MaxOutMagic
	GetAttribute STAT_MAGIC, nTemp
	nTemp = MAX_STAT - nTemp
	GiveAttribute STAT_MAGIC, nTemp, 1, 0
	exit 1

:MaxOutEndurance
	GetAttribute STAT_ENDURANCE, nTemp
	nTemp = MAX_STAT - nTemp
	GiveAttribute STAT_ENDURANCE, nTemp, 1, 0
	exit 1

:MaxOutAccuracy
	GetAttribute STAT_ACCURACY, nTemp
	nTemp = MAX_STAT - nTemp
	GiveAttribute STAT_ACCURACY, nTemp, 1, 0
	exit 1

:MaxOutSpeed
	GetAttribute STAT_SPEED, nTemp
	nTemp = MAX_STAT - nTemp
	GiveAttribute STAT_SPEED, nTemp, 1, 0
	exit 1

:MaxOutLuck
	GetAttribute STAT_LUCK, nTemp
	nTemp = MAX_STAT - nTemp
	GiveAttribute STAT_LUCK, nTemp, 1, 0
	exit 1

:ZeroOutMight
	GetAttribute STAT_MIGHT, nTemp
	nTemp = -1 * MAX_STAT + nTemp
	GiveAttribute STAT_MIGHT, nTemp, 1, 0
	exit 1

:ZeroOutMagic
	GetAttribute STAT_MAGIC, nTemp
	nTemp = -1 * MAX_STAT + nTemp
	GiveAttribute STAT_MAGIC, nTemp, 1, 0
	exit 1

:ZeroOutEndurance
	GetAttribute STAT_ENDURANCE, nTemp
	nTemp = -1 * MAX_STAT + nTemp
	GiveAttribute STAT_ENDURANCE, nTemp, 1, 0
	exit 1

:ZeroOutAccuracy
	GetAttribute STAT_ACCURACY, nTemp
	nTemp = -1 * MAX_STAT + nTemp
	GiveAttribute STAT_ACCURACY, nTemp, 1, 0
	exit 1

:ZeroOutSpeed
	GetAttribute STAT_SPEED, nTemp
	nTemp = -1 * MAX_STAT + nTemp
	GiveAttribute STAT_SPEED, nTemp, 1, 0
	exit 1

:ZeroOutLuck
	GetAttribute STAT_LUCK, nTemp
	nTemp = -1 * MAX_STAT + nTemp
	GiveAttribute STAT_LUCK, nTemp, 1, 0
	exit 1