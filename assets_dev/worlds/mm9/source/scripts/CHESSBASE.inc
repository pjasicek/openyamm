;--------------------------------
;	ChessBase.inc
;	by SJR
;	Purpose:base include. all the
;			stuff every piece does
;--------------------------------
#include	ListMaker.inc

#hobject	hMe = 0
#hobject	hTrigger = 0
#string		sCameraName = ""
#hobject	hCamera = 0

#number		nTemp = 0
#number		xMe = 0
#number		zMe = 0

#number		xSpace = 0
#number		yHeight = 0
#number		zSpace = 0

#number		nSpeed = 0

#number		bShouldQueen = 0
#number		nLocation = 0

#number		SIZEINDEX = 7

;;must set these before calling initchessbase
#string		sSquareName = ""
#string		sFloorName = ""
#number		BOARDSIZE = 8

;--------------------------------
:InitChessBase
;	sets up everything
;--------------------------------
	AddTrigger ping, CheckPath

	LISTFIRST = 0
	LISTLAST  = BOARDSIZE * BOARDSIZE - 1
	SIZEINDEX = BOARDSIZE - 1
	LISTNAME  = sSquareName

	GetMyHandle hMe
	GetPOS hMe, nTemp, yHeight, nTemp
	SetStat hMe, gravity, 0
	GetConsoleStrVar CHESS_CAM, sCameraName
	GetObjectHandle sCameraName, hCamera

	gosub Create2DCoordinates

	Exit 1

;--------------------------------
:BeginAttack
;	if no other piece attacking, attack
;	must set LISTINDEX prior to this
;	must set hTrigger prior to this
;--------------------------------
	GetConsoleNumVar CLAIM_ATTACK, nTemp
	if( nTemp==1 )
		Exit 1
	endif

	nLocation = LISTINDEX

	gosub LockBoard
	gosub Create2DCoordinates
	gosub StartCamera
	gosub AttackSquare

	ClearFlag hMe, 8192
	SetFlag hMe, 2097152

	Exit 1

;********************************
;private
;********************************

;--------------------------------
:Create2DCoordinates
;	changes (index) to (x,z)
;--------------------------------
	zMe = 0
	while( nLocation>=BOARDSIZE )
		nLocation = nLocation - BOARDSIZE
		zMe = zMe + 1
	endwhile
	xMe = nLocation

	gosub Create1DCoordinates

	Exit 1

;--------------------------------
:Create1DCoordinates
;	changes (x,z) to (index)
;--------------------------------
	nLocation = BOARDSIZE * zMe + xMe

	Exit 1

;--------------------------------
:LockBoard
;	register attack, disable input
;--------------------------------
	SetConsoleNumVar CLAIM_ATTACK, 1
	RemoveTrigger ping

	Exit 1

;--------------------------------
:UnlockBoard
;	unregister attack, enable input
;--------------------------------
	SetConsoleNumVar CLAIM_ATTACK, 0
	AddTrigger ping, CheckPath

	Exit 1

;--------------------------------
:CheckPath
;	override this to check spaces
;--------------------------------
	Exit 1

;--------------------------------
:AttackSquare
;	moves to space
;--------------------------------
	GetDistance hMe, hTrigger, nSpeed
	nSpeed = nSpeed / 2
	GetPOS hTrigger, xSpace, nTemp, zSpace
	MoveToPOS xSpace, yHeight, zSpace, nSpeed, FinishAttack

	PlaySound "sounds\door\doorslidestone.wav", DoNothing, 1000, 2000, 0, 100

	Exit 1

;--------------------------------
:FinishAttack
;	snap to POS, check for pawn->queen, unlock board
;--------------------------------
	SetPOS hMe, xSpace, yHeight, zSpace

	gosub EndCamera
	gosub PawnToQueen
	gosub UnlockBoard

	SetFlag hMe, 8192
	ClearFlag hMe, 2097152

	LISTNAME = sSquareName

	Exit 1

;--------------------------------
:PawnToQueen
;	if at the end of the board, change to queen
;--------------------------------
	if( zMe==SIZEINDEX )
		if( bShouldQueen==1 )
			GetPOS hMe, xSpace, yHeight, zSpace
			Spawn hTrigger, xSpace, yHeight, zSpace, "Terror"
			if( hTrigger!=0 )
				SetStat hTrigger, HitPoints, 1069
				SetStat hTrigger, AC, 80
				DoClientFX hTrigger, "fireblue", 0, 1
			endif
			RemoveObject hMe
		endif
	endif

	Exit 1

;--------------------------------
:StartCamera
;--------------------------------
	if( hCamera!=0 )
		Trigger hCamera, look
	endif

	Exit 1

;--------------------------------
:EndCamera
;--------------------------------
	if( hCamera!=0 )
		Trigger hCamera, turnoff
	endif

	Exit 1

;--------------------------------
:DoNothing
;--------------------------------
	Exit 1