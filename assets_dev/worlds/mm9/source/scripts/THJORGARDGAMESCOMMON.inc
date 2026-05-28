;---------------------------------
;	ThjorgardGamesCommon.inc
;	by SJR
;	01-04-02
;	Purpose:
;		a.) keep track of games won
;		b.)	sell, redeem, and check ticket
;		c.) give out prizes and assc. keys
;	Thjorgard and Guberlang games should channel
;	everything through this.
;---------------------------------
#include NoGold.inc

;;;MISC
#number		TICKET_ITEM = 557
#number		TICKET_COST = 5
#number		TICKET_BATCH_COST = 40

#number		RULEBOOK_ITEM = 594

#number		PRIZE_STUFFED_DRAGON = 395
#number		PRIZE_THJORGARD_EXP = 10000
#number		PRIZE_GUBER_MIN = 362
#number		PRIZE_GUBER_MAX = 367

;;;TEXT
#number		TEXT_VICTORY = 6
#number		TEXT_DEFEAT = 7
#number		TEXT_NEEDTICKET = 226
#number		TEXT_BOUGHTTICKET = 227
#number		TEXT_BOUGHTBATCH = 234
#number		TEXT_USEDTICKET = 232
#number		TEXT_NOMONEY = 229
#number		TEXT_STUFFEDDRAGON = 228
#number		TEXT_YOURMOVE = 244

;;;KEYS
#number		YRSAS_QUEST_PENDING   = 93
#number		YRSAS_QUEST_COMPLETED = 94

#number		THJORGARD_STONES = 7100
#number		THJORGARD_BOAT   = 7101
#number		THJORGARD_RUNES  = 7102
#number		THJORGARD_HONKY  = 7103
#number		THJORGARD_BELL   = 7104
#number		THJORGARD_MIGHT  = 7105
#number		THJORGARD_ALL	 = 7106

#number		GUBERLAND_STONES = 7110
#number		GUBERLAND_BOAT   = 7111
#number		GUBERLAND_RUNES  = 7112
#number		GUBERLAND_HONKY  = 7113
#number		GUBERLAND_BELL   = 7114
#number		GUBERLAND_MIGHT  = 7115
#number		GUBERLAND_ALL	 = 7116


#number		THJORGARD_RESULT = 0
#number		thjorgard_nTemp = 0
;---------------------------------
:CheckGameTicket
;	checks for ticket key
;---------------------------------
	HasItem TICKET_ITEM, THJORGARD_RESULT
	if( THJORGARD_RESULT==0 )
		RollOverText TEXT_NEEDTICKET, 1, 3000, 2000
	endif

	Exit 1

;---------------------------------
:SellGameTicket
;	take gold, give ticket and rules
;---------------------------------
	HasGold TICKET_COST, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		PlaySound "sounds\events\gold01.wav", DoNothing, 1, 500, 0, 100
		RollOverText TEXT_BOUGHTTICKET, 1, 3000, 2000
		TakeGold TICKET_COST
		GiveItem TICKET_ITEM

		;;give them the rules
		HasItem RULEBOOK_ITEM, thjorgard_nTemp
		if( thjorgard_nTemp==0 )
			GiveItem RULEBOOK_ITEM
		endif
	else
		gosub NoGold
	endif

	Exit 1

;---------------------------------
:SellBatchTickets
;	take gold, give 10 tickets and rules
;---------------------------------
	HasGold TICKET_BATCH_COST, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		PlaySound "sounds\events\gold01.wav", DoNothing, 1, 500, 0, 100
		RollOverText TEXT_BOUGHTBATCH, 1, 3000, 2000
		HasItem RULEBOOK_ITEM, thjorgard_nTemp
		if( thjorgard_nTemp==0 )
			GiveItem RULEBOOK_ITEM
		endif
		TakeGold TICKET_BATCH_COST

		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM

		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
		GiveItem TICKET_ITEM
	else
		gosub NoGold
	endif

	Exit 1

;---------------------------------
:TakeGameTicket
;	take ticket item, and key if last one
;---------------------------------
	HasItem TICKET_ITEM, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		TakeItem TICKET_ITEM
		RollOverText TEXT_USEDTICKET, 1, 3000, 2000
	endif

	Exit 1

;---------------------------------
:GiveThjorgardPrize
;	completed quest- give prize, key, exp
;---------------------------------
	GiveKey THJORGARD_ALL

	RollOverText TEXT_STUFFEDDRAGON, 1, 3000, 2000
	Playsound "sounds\events\quest.wav", DoNothing, 1, 1000, 0, 100

	GiveExp PRIZE_THJORGARD_EXP
	GiveItem PRIZE_STUFFED_DRAGON
	GiveKey YRSAS_QUEST_COMPLETED

	Exit 1

;---------------------------------
:GiveGuberlandPrize
;	just give random prize each time
;---------------------------------
	GiveKey GUBERLAND_ALL

	GetRandomInt PRIZE_GUBER_MIN, PRIZE_GUBER_MAX, thjorgard_nTemp
	GiveItem thjorgard_nTemp

	Exit 1

;---------------------------------
:CheckThjorgardWins
;	checks to see if all games won
;---------------------------------
	RollOverText TEXT_VICTORY, 1, 3000, 2000

	HasKey THJORGARD_ALL, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		Exit 1
	endif

	HasKey THJORGARD_STONES, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
	HasKey THJORGARD_BOAT, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
	HasKey THJORGARD_RUNES, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
	HasKey THJORGARD_HONKY, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
	HasKey THJORGARD_BELL, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
	HasKey THJORGARD_MIGHT, thjorgard_nTemp
	if( thjorgard_nTemp==1 )

		;;if player won all games AND on Yrsa's quest
		HasKey YRSAS_QUEST_PENDING, thjorgard_nTemp
		if( thjorgard_nTemp==1 )
			Wait 17, 2, GiveThjorgardPrize
		endif

	endif
	endif
	endif
	endif
	endif
	endif

	Exit 1

;---------------------------------
:CheckGuberlandWins
;---------------------------------
	RollOverText TEXT_VICTORY, 1, 3000, 2000

	HasKey GUBERLAND_ALL, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		;;dont exit, no quest prize given
	endif

	gosub GiveGuberlandPrize

	Exit 1

;---------------------------------
:RecordStonesWin
;---------------------------------
	GetConsoleNumVar GUBERLAND_WIN_TYPE, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		GiveKey GUBERLAND_STONES
		gosub CheckGuberlandWins
	else
		GiveKey THJORGARD_STONES
		gosub CheckThjorgardWins
	endif

	Exit 1

;---------------------------------
:RecordBoatWin
;---------------------------------
	GetConsoleNumVar GUBERLAND_WIN_TYPE, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		GiveKey GUBERLAND_BOAT
		gosub CheckGuberlandWins
	else
		GiveKey THJORGARD_BOAT
		gosub CheckThjorgardWins
	endif

	Exit 1

;---------------------------------
:RecordHonkyWin
;---------------------------------
	GetConsoleNumVar GUBERLAND_WIN_TYPE, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		GiveKey GUBERLAND_HONKY
		gosub CheckGuberlandWins
	else
		GiveKey THJORGARD_HONKY
		gosub CheckThjorgardWins
	endif

	Exit 1

;---------------------------------
:RecordRunesWin
;---------------------------------
	GetConsoleNumVar GUBERLAND_WIN_TYPE, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		GiveKey GUBERLAND_RUNES
		gosub CheckGuberlandWins
	else
		GiveKey THJORGARD_RUNES
		gosub CheckThjorgardWins
	endif

	Exit 1

;---------------------------------
:RecordBellWin
;---------------------------------
	GetConsoleNumVar GUBERLAND_WIN_TYPE, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		GiveKey GUBERLAND_BELL
		gosub CheckGuberlandWins
	else
		GiveKey THJORGARD_BELL
		gosub CheckThjorgardWins
	endif

	Exit 1

;---------------------------------
:RecordMightWin
;---------------------------------
	GetConsoleNumVar GUBERLAND_WIN_TYPE, thjorgard_nTemp
	if( thjorgard_nTemp==1 )
		GiveKey GUBERLAND_MIGHT
		gosub CheckGuberlandWins
	else
		GiveKey THJORGARD_MIGHT
		gosub CheckThjorgardWins
	endif

	Exit 1

;---------------------------------
:Countdown5
;---------------------------------
	Playsound "sounds\door\doorlock01.wav", DoNothing, 1, 500, 0, 100
	RolloverText 235, 1, 2000, 1000
	Wait 5, 1, Countdown4

	Exit 1
;---------------------------------
:Countdown4
;---------------------------------
	Playsound "sounds\door\doorlock01.wav", DoNothing, 1, 5000, 0, 100
	RolloverText 236, 1, 2000, 1000
	Wait 4, 1, Countdown3

	Exit 1
;---------------------------------
:Countdown3
;---------------------------------
	Playsound "sounds\door\doorlock01.wav", DoNothing, 1, 5000, 0, 100
	RolloverText 237, 1, 2000, 1000
	Wait 3, 1, Countdown2

	Exit 1
;---------------------------------
:Countdown2
;---------------------------------
	Playsound "sounds\door\doorlock01.wav", DoNothing, 1, 5000, 0, 100
	RolloverText 238, 1, 2000, 1000
	Wait 2, 1, Countdown1

	Exit 1
;---------------------------------
:Countdown1
;---------------------------------
	Playsound "sounds\door\doorlock01.wav", DoNothing, 1, 5000, 0, 100
	RolloverText 239, 1, 2000, 1000
	Wait 1, 1, Countdown0

	Exit 1
;---------------------------------
:Countdown0
;---------------------------------
	Playsound "sounds\events\dingbell.wav", DoNothing, 1, 5000, 0, 100

	Exit 1