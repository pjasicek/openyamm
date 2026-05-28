;---------------------------------------------
;	FollowPlayer.inc
;	by SJR
;	10-13-01
;	Purpose:more cooperative follow
;			script.
;	Triggers:
;		"Use" = follows the sender
;		"Follow" = follows the player
;		"Halt" = stops following
;	Script will call "OnFollowDone" each time it
;	reaches the target. Call FollowInit first.
;
;	edited by Bones 5/6/03
;	TELP Patch 1.3 -- avoid timer crashes
;---------------------------------------------
#include BaseGlobals.inc

#number		follow_bFollowing = 1
#hobject	follow_hPlayer = 0
#hobject	follow_hMe = 0
#number		follow_ds = 0
#number		nTemp = 0
#number		LADDER_GAP = 30
#number		LADDER_HEIGHT = 0

;---------------------------------------------
:FollowInit
;	sets up triggers
;---------------------------------------------
	GetMyHandle follow_hMe

	AddTrigger Use, FollowOnUse
	AddTrigger Follow, FollowStart
	AddTrigger Halt, FollowStop

	OnTouchNotify follow_CheckLadder

	Exit 1

;---------------------------------------------
:FollowStart
;	follow player
;---------------------------------------------
	Wait 16 0 DoNothing
	GetPlayerHandle follow_hPlayer
	GetMyHandle follow_hMe

	follow_bFollowing = 1

	gosub FollowLoop

	Exit 1

;---------------------------------------------
:FollowStop
;	pause following
;---------------------------------------------
	Wait 16 0 DoNothing
	Stop
	follow_bFollowing = 0

	Exit 1

;---------------------------------------------
:FollowResume
;	follow player
;---------------------------------------------
	if( follow_hPlayer!=0 )

		follow_bFollowing = 1
		gosub FollowLoop
	endif

	Exit 1

;---------------------------------------------
:OnFollowDone
;	called each time we reach the target
;---------------------------------------------
	Exit 1

;*****************************
;private
;*****************************

:FollowLoop
	if( follow_bFollowing==0 )
		Exit 1
	endif
	AIGetDistance follow_hPlayer, follow_ds
	;;run radius
	if( follow_ds>200 )
		RunTo follow_hPlayer, 32, FollowDone
	else
		;;walk radius
		if( follow_ds>100 )
			WalkTo follow_hPlayer, 32, FollowDone
		else
			SetIdle
			gosub OnFollowDone
		endif
	endif
	;;refresh action every 3 secs
	Wait 16, 3, FollowLoop
	Exit 1

:FollowDone
	gosub OnFollowDone
	gosub FollowLoop
	Exit 1

:FollowOnUse
	GetParam 0, follow_hPlayer
	follow_bFollowing = 1
	gosub FollowLoop
	Exit 1

:DoNothing
	Exit 1

;;ladder stuff
#hobject	follow_hObject = 0
#string		follow_sObjectName = ""
#number		follow_nDistance = 0

#number		follow_x = 0
#number		follow_y = 0
#number		follow_yMe = 0
#number		follow_nLadderHeight = 0
#number		follow_z = 0
#number		bPinging = 0

:follow_CheckLadder
	GetParam 0, follow_hObject
	GetClassName follow_hObject, follow_sObjectName
	if( follow_sObjectName=="Ladder" )
		GetDims follow_hObject, nTemp,LADDER_HEIGHT,nTemp
		bPinging = 1
		gosub FollowStop
		gosub follow_PingLoop
		OnTouchNotify DoNothing
	endif

	Exit 1

:follow_PingLoop
	GetPOS follow_hPlayer,	nTemp,follow_y	,nTemp
	GetPOS follow_hMe,		nTemp,follow_yMe,nTemp

	follow_nLadderHeight = 2 * LADDER_HEIGHT + LADDER_GAP
	nTemp = follow_y - follow_yMe
	if( nTemp<0 )
		nTemp = nTemp * -1
	endif
;cprint ping...
;cprint follow_nLadderHeight
;cprint nTemp
;cprint ************
	if( nTemp<LADDER_GAP )
		gosub follow_DescendLadder
	else
		nTemp = follow_y - follow_yMe
		if( nTemp<0 )
			gosub follow_DescendLadder
		else
			gosub follow_ClimbLadder
		endif
	endif

	if( bPinging==1 )
		Wait 16, 2, follow_PingLoop
	endif

	Exit 1

:follow_DescendLadder
	bPinging = 0
	SetStat follow_hMe, Gravity, TRUE
	gosub follow_DescendFinish
	Exit 1

:follow_DescendFinish
	OnTouchNotify follow_CheckLadder
	gosub FollowStart
	Exit 1

:follow_ClimbLadder
	;;LoopAnim climb, 0
	bPinging = 0
	SetStat follow_hMe, Gravity, FALSE
	MoveDir 0,1,0, follow_nLadderHeight, follow_nLadderHeight, follow_ClimbFinish
	Exit 1

:follow_ClimbFinish
	Stop
	SetStat follow_hPlayer, Gravity, TRUE
	bPinging = 1
	GetPOS follow_hObject, follow_x,nTemp,follow_z
	GetPOS follow_hMe, nTemp,follow_yMe,nTemp
	WalkToPOS follow_x,follow_yMe,follow_z, 25, follow_PingLoop
	Exit 1