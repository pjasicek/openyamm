;---------------------------------
;	TheIt.scr (stephen king's)
;	by SJR
;	11-04-01
;	Purpose:turn into a weirdo lookin
;			spiky skeleton mutant
;			thing with big pointy teeth
;---------------------------------
#include baseMelee.inc

#stringarray	spSockets[8]
#stringarray	spAnimations[8]

#string			sSocket = ""
#string			sAttachment = ""
#string			sAnimation = ""
#string			sSkin = ""

#hobject		hAttachment = 0
#number			nCounter = 0

;---------------
:InitTheIt
;---------------
	sAttachment = "..\lobberpod.abc"
	sSkin = "..\skeleton1.dtx"

	gosub InitStrings
	gosub BaseInit

	SetModelFilenames models\skeleton.abc, skins\skeleton1.dtx

	SetIdle

	GetPlayerHandle g_hTarget

	AddTrigger Mutate, AttachThing
	nCounter = 0

	gosub BaseWanderStartup

	Exit TRUE

;---------------
:AttachThing
;---------------
	PlaySound "sounds\animsounds\pig\wince1.wav", DoNothing, 1, 500, FALSE, 100

	ArrayGet spSockets,		nCounter, sSocket
	ArrayGet spAnimations,	nCounter, sAnimation

	AttachProp sAttachment, sSkin, sSocket, hAttachment
	Trigger hAttachment, sAnimation

	if( nCounter>=7 )
		gosub SetupTarget
		gosub AggressiveStart
		PlaySound "sounds\animsounds\pig\wince1.wav", DoNothing, 1, 500, FALSE, 100
	endif

	nCounter = nCounter + 1

	gosub AttachThing

	Exit TRUE

#string		ANIMCOMMAND = "LOOPANIM "
;---------------
:InitStrings
;---------------
	ArrayPut spAnimations, 0, "hattack1"
	ArrayPut spAnimations, 1, "rattack1"
	ArrayPut spAnimations, 2, "wince1"
	ArrayPut spAnimations, 3, "wince2"
	ArrayPut spAnimations, 4, "land"
	ArrayPut spAnimations, 5, "hattack1"
	ArrayPut spAnimations, 6, "walk"
	ArrayPut spAnimations, 7, "fidget"


	ArrayPut spSockets, 0, "Head1"
	ArrayPut spSockets, 1, "SpineMiddle"
	ArrayPut spSockets, 2, "ThighR"
	ArrayPut spSockets, 3, "ThighL"
	ArrayPut spSockets, 4, "CalfR"
	ArrayPut spSockets, 5, "CalfL"
	ArrayPut spSockets, 6, "RHand1"
	ArrayPut spSockets, 7, "LHand1"

	nCounter = 7
	while( nCounter>=0 )
		ArrayGet spAnimations, nCounter, sAnimation
		sAnimation = ANIMCOMMAND + sAnimation
		ArrayPut spAnimations, nCounter, sAnimation
		nCounter = nCounter - 1
	endwhile

	Exit TRUE