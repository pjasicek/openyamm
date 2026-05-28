#include BaseGlobals.inc
#include basewander.inc

;;;THIS FILE IS NOTHING BUT WALKTO CALLBACKS!

#hobject	hCurDest=0
#hobject	hButtons=0
#hobject	hChests=0
#hobject	hSound=0

;;these are IN order
#string		sWaypoint0="PathMarker0"
#string		sWaypoint1="PathMarker1"
#string		sWaypoint2="PathMarker2"
#string		sWaypoint3="PathMarker3"
#string		sWaypoint4="PathMarker4"
#string		sWaypoint5="PathMarker5"
#string		sWaypoint6="PathMarker6"
#string		sWaypoint7="PathMarker7"
#string		sWaypoint8="PathMarker8"
#string		sWaypoint9="PathMarker9"
#string		sTemp=""

#number		rand=1
#number		x=0
#number		y=0
#number		z=0
#number		dir=1
#number		bTurning=FALSE
#number		bReturning=FALSE

;;;	Trigger, hButtons, UnlockButtons

;------------
:InitHonkAccountant
;------------
	GetObjectHandle CollectionChestM, hChests
;;	GetObjectHandle , hButtons

	@M 7 : 0, StartTrip, DoNothing
	@M 19 : 0, StartTrip, DoNothing
	@M 7 : 30, DoNothing, DoNothing
	@M 19 : 30, DoNothing, DoNothing

;;	gosub BaseWanderInit
;;	gosub BaseWanderStartup
	Exit TRUE

;------------
:AvoidObstacle
;------------
	if( bTurning == TRUE )
		Exit TRUE
	endif
;;	bTurning = TRUE
	GetRightDir x,y,z
	x = x * dir
	z = z * dir
	FaceDir x,y,z, 0, DoneAvoiding
	Exit TRUE

;------------
:DoneAvoiding
;------------
	bTurning = FALSE
	dir = dir * -1
	Exit TRUE

:StartTrip
	Stop
	OnObstacle AvoidObstacle
	gosub BaseWanderStop
	gosub GoToWaypoint0
	Exit TRUE

:GoToWaypoint0
	OnStuck GoToWaypoint0
	GetObjectHandle sWaypoint0, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint1
	Exit TRUE

:GoToWaypoint1
	OnStuck GoToWaypoint1
	GetObjectHandle sWaypoint1, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint2
	Exit TRUE

:GoToWaypoint2
	OnStuck GoToWaypoint2
	GetObjectHandle sWaypoint2, hCurDest
	if( bReturning==TRUE )
		WalkTo hCurDest, 20, GoToWaypoint3
	else
		WalkTo hCurDest, 20, DoCollect
	endif
	Exit TRUE

:GoToWaypoint3
	SetCrouch FALSE
	OnStuck GoToWaypoint3
	GetObjectHandle sWaypoint3, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint4
	Exit TRUE

:GoToWaypoint4
	OnStuck GoToWaypoint4
	GetObjectHandle sWaypoint4, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint5
	Exit TRUE

:GoToWaypoint5
	OnStuck GoToWaypoint5
	GetObjectHandle sWaypoint5, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint6
	Exit TRUE

:GoToWaypoint6
	OnStuck GoToWaypoint6
	GetObjectHandle sWaypoint6, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint7
	Exit TRUE

:GoToWaypoint7
	OnStuck GoToWaypoint7
	GetObjectHandle sWaypoint7, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint8
	Exit TRUE

:GoToWaypoint8
	OnStuck GoToWaypoint8
	GetObjectHandle sWaypoint8, hCurDest
	WalkTo hCurDest, 20, GoToWaypoint9
	Exit TRUE

:GoToWaypoint9
;;	Trigger hButtons, UnlockDoor
	OnStuck GoToWaypoint9
	GetObjectHandle sWaypoint9, hCurDest
	if( bReturning==TRUE )
		WalkTo hCurDest, 20, DoNothing
	else
		WalkTo hCurDest, 20, FinishTrip
	endif
	Exit TRUE

:FinishTrip
	Stop
	if( bReturning==FALSE )
		bReturning = TRUE
	else
		bReturning = FALSE
	endif
	gosub ReversePaths
	gosub GoToWaypoint0
	Exit TRUE

:ReversePaths
	sTemp = sWaypoint0
	sWaypoint0 = sWaypoint9
	sWaypoint9 = sTemp

	sTemp = sWaypoint1
	sWaypoint1 = sWaypoint8
	sWaypoint8 = sTemp

	sTemp = sWaypoint2
	sWaypoint2 = sWaypoint7
	sWaypoint7 = sTemp

	sTemp = sWaypoint3
	sWaypoint3 = sWaypoint6
	sWaypoint6 = sTemp

	sTemp = sWaypoint4
	sWaypoint4 = sWaypoint5
	sWaypoint5 = sTemp

	Exit TRUE

:DoCollect
	Stop
	FaceObject hChests, 180, PlayCollectSound
	SetCrouch TRUE
	Wait 3, 3, GoToWaypoint3
	Exit TRUE

:PlayCollectSound
	PlaySound sounds\weapons\knifereload.wav, DoNothing, hSound, 500, FALSE, 100
	Exit TRUE