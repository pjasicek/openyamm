;-------------------------------------------------------------
;	BaseDoor.inc
;	Jeff Leggett
;	09/26/2001
;
;	Basic door handling...
;
;	if we hit a door that is closed, we stop, trigger it to open,
;	start walking again.... if we have a target, we will head
;	towards that target, otherwise, we'll just go forward...
;
;
;	
;-------------------------------------------------------------


#include AIGlobals.inc

#number			g_bWasWalking = 0
#number			g_bWasRunning = 0
#hobject		g_hDoor
#number			g_bDoorOpening = 0

#string			g_sOpenString=Use

;-------------------------------------------------------------
:BD_DoorOpen
;-------------------------------------------------------------
	g_bDoorOpening = FALSE

	ResumeWait -1

	GetTarget g_hObject

	if ( g_hObject==NULL )
		if ( g_bWasRunning==TRUE )
			Run
		Else
			Walk
		Endif
	else
		if ( g_bWasRunning==TRUE )
			RunTo g_hObject
		else
			WalkTo g_hObject
		endif
	endif

	RestorePath

	Exit

;-------------------------------------------------------------
:BD_OnDoor
;
;	Params:
;		p0		- hDoor
;		p1-3	- Normal
;
;	Return Value:
;
;		g_bDoorOpening	is set to TRUE if we actually are opening 
;		the door...
;
;-------------------------------------------------------------

	g_bDoorOpening = FALSE

	GetParam 0, g_hDoor
	GetStat g_hDoor,IsClosed,g_bTemp

	if ( g_bTemp==FALSE )
		; door is not closed, ignore....
		Exit FALSE
	Endif

	GetStat g_hMyObject,IsWalking,g_bWasWalking
	GetStat g_hMyObject,IsRunning,g_bWasRunning

	if ( g_bWasRunning==FALSE )
		GetStat g_hMyObject,IsFlying,g_bWasRunning
	Endif

	; if we're not walking or running, then the door hit us.
	; don't care about this...
	if ( g_bWasRunning==FALSE )
		if ( g_bWasWalking==FALSE )
			Exit FALSE
		endif
	endif

;	Get the angle between the way we're facing and the door. 
;	Perhaps we aren't going through the door...

	GetParam 1, g_normalX
	GetParam 2, g_normalY
	GetParam 3, g_normalZ
	RotateDir g_normalX, g_normalY, g_normalZ, 180

	GetFaceDir g_hMyObject, g_velX, g_velY, g_velZ

	VecAngle g_normalX,0,g_normalZ,g_velX,0,g_velZ, g_nTemp

	if ( g_nTemp > 45 )
		; we're not really heading toward the door....
		exit FALSE
	endif

;	OK, we want to go through the door...

;
;	Stop and face the door...
;
	Stop
	FaceDir g_normalX, 0, g_normalZ, 360

; Open it...
	Trigger g_hDoor,g_sOpenString
;
;	Pause all wait timeouts...
;
	PauseWait -1

;
;	wait for door to open...
;
	GetStat g_hDoor,DoorOpenTime,g_nTemp

	Wait 0, g_nTemp, BD_DoorOpen

	SavePath

	g_bDoorOpening = TRUE

	Exit

;-------------------------------------------------------------
:BaseDoorInit
;-------------------------------------------------------------

	GetMyHandle g_hMyObject
	OnDoor	BD_OnDoor

	Exit