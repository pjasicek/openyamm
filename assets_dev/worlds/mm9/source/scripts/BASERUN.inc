;----------------------------------------------------------
;	BaseRun.Inc
;	Jeff Leggett
;	08/07/2001
;
;	Base include for running away from the target...
;
;	Runs in opposite direction of the target.
;	Looks for hiding places tagged for this Actor.
;	If one is found, it runs to it....
;
;----------------------------------------------------------


#Include BaseTimers.inc
#Include AIGlobals.Inc

#number			MIN_RUNAWAY_DIST = 1000
#number			RUN_AWAY_TICK_TIME = 0.5
#number			RUN_AWAY_TICK_MIN = 0.3
#number			RUN_AWAY_TICK_MAX = 0.8
#number			RUN_AWAY_MAX_TIME = 15


#number			HIDE_WAIT_TIME = 1.5
#number			COWER_TICK = 5

#number			g_nLastRunawayTime = 0

;
; You can customize these to limit how much we'll turn left and right while running away.....
;
#number			RUN_AWAY_TURN_MIN = 15
#number			RUN_AWAY_TURN_MAX = 45


#number				g_bRunningAway = 0


#number				g_dist1
#number				g_dist2

#number				g_bUseHidingPlaces = 1

#hobject			g_hHidingPlace = 0

;
; Set this to TRUE if you want to yell for help while running away....
;
#number				g_bAskForHelp = 1

#number				g_bCanCower = 0
#number				g_bCowering = 0
#number				g_nCowerAnim = 0

#number				g_nRunawayObstacles = 0
#number				g_nLastRunawayObstacle = 0

#hobject			g_hRunAwayTrigger = 0


;----------------------------------------------------------
:CanCower
;
;	Sets g_bCanCower to TRUE or FALSE
;----------------------------------------------------------

	GetAnimNbr g_hMyObject,Cower,g_nCowerAnim

	if ( g_nCowerAnim==-1 )
		g_bCanCower = FALSE
	else
		g_bCanCower = TRUE
	endif

	exit

;----------------------------------------------------------
:BaseIsCowering
;----------------------------------------------------------

	g_bCowering	= FALSE

	GetCurrAnim g_hMyObject, g_nTemp

	if ( g_nTemp==g_nCowerAnim )
		g_bCowering	= TRUE
	endif

	exit

;----------------------------------------------------------
:BaseRunCower
;
;	Go into "cower" mode...  
;
;----------------------------------------------------------

	gosub BaseIsCowering

	if ( g_bCowering==FALSE )
		g_bCowering	= TRUE
		LoopAnim Cower, 0
		GetTime g_nLastRunawayTime
	endif

	Target g_hTarget, FALSE

	Wait RUN_AWAY_WAIT,COWER_TICK,BaseRunCowerTick

	Exit

;----------------------------------------------------------
:BaseRunCowerTick
;
;	See if we should stop cowering...
;
;----------------------------------------------------------

	GetTarget g_hObject

	if ( g_hObject==NULL )
		goto BaseRunCancel
	endif

	IsVisible g_hObject,g_bTemp

	if ( g_bTemp==FALSE )
		goto BaseRunCancel
	Endif

	Wait RUN_AWAY_WAIT,COWER_TICK,BaseRunCowerTick

	Exit

;----------------------------------------------------------
:BaseRunCowerStop
;----------------------------------------------------------
	
	gosub BaseIsCowering

	if ( g_bCowering==TRUE )
		Wait RUN_AWAY_WAIT,0,DoNothing
		Stop
		g_bCowering	= FALSE
	endif

	Exit

;----------------------------------------------------------
:BaseRunLostTarget
;----------------------------------------------------------

	Exit TRUE

;----------------------------------------------------------
:BaseRunCancel
;
;	Stop running away...
;	You'll want to overload this to do your own thing,
;	just remember to call this function (ie:gosub BaseRunCancel,1)
;
;----------------------------------------------------------

	gosub BaseRunCowerStop

	g_bRunningAway = FALSE
;;;;	OnTargetBeyondDist 0
	OnObstacle
	OnLostTarget 

	g_hRunAwayTrigger	= NULL

	Wait RUN_AWAY_WAIT, 0, DoNothing

	Exit

;----------------------------------------------------------
:BaseRunAwayFace
;
;	Figure out direction to face when running away...
;
;----------------------------------------------------------
	if ( g_hTarget==NULL )
		Exit
	Endif

	GetPos g_hTarget, g_targetX, g_targetY, g_targetZ
	GetPos g_hMyObject, g_posX, g_posY, g_posZ

	VecSub g_posX, g_posY, g_posZ, g_targetX, g_targetY, g_targetZ
	g_targetY = 0
	VecNorm g_posX, g_posY, g_posZ
	
	GetRandomFloat RUN_AWAY_TURN_MIN, RUN_AWAY_TURN_MAX, g_nRandom
	GetRandomFloat 0,1, g_nTemp

	if ( g_nTemp==1 )
		g_nRandom = g_nRandom * -1
	endif

	RotateDir g_posX, g_posY, g_posZ, g_nRandom
	CastRay g_posX, g_posY, g_posZ, 100, g_hObject, g_nTemp

	if ( g_hObject!=NULL )
		g_nRandom = g_nRandom * -2
		RotateDir g_posX, g_posY, g_posZ, g_nRandom
		CastRay g_posX, g_posY, g_posZ, 100, g_hObject, g_nTemp
		if ( g_hObject!=NULL )
			Exit		
		endif
	endif

	FaceDir g_posX, g_posY, g_posZ, 360

	Exit

;----------------------------------------------------------
:BaseShouldRun
;----------------------------------------------------------
	g_bTemp = FALSE

	if ( g_hRunAwayTrigger==g_hTarget )
		g_bTemp = TRUE
	else
		ShouldRunAway g_hTarget, g_bTemp
	Endif

	if ( g_bTemp==TRUE )
		IsInNoRunZone g_bTemp
		if ( g_bTemp==TRUE )
			if ( g_hHidingPlace!=NULL )
				g_bTemp = TRUE
			else
				g_bTemp = FALSE
			endif
		else
			g_bTemp = TRUE
		endif
	endif

	Exit

;----------------------------------------------------------
:BaseRunAwayTick
;
;	We do our running away thinking here....
;
;----------------------------------------------------------
	
	GetTarget g_hObject
	if ( g_hObject==NULL )
		; We're done!
		DebugOut Target Is Gone.  Done running...
		gosub BaseRunCancel
		Exit
	Endif

	gosub BaseShouldRun
	
	if ( g_bTemp==FALSE )
		Debugout ShouldRunAway says NO.
		gosub BaseRunCancel
		exit
	Endif

	GetTime g_nTemp

	Sub g_nTemp, g_nLastRunawayTime

	if ( g_nTemp > RUN_AWAY_MAX_TIME )
		Debugout Ran away long enough...
		if ( g_bCanCower==TRUE )
			gosub BaseRunCower
		else
			gosub BaseRunCancel
		endif
		exit
	endif


	AIGetDistance g_hObject, g_dist1

	if ( g_hHidingPlace==NULL )
		if ( g_dist1 > MIN_RUNAWAY_DIST )
			; We're far enough away, let's quit.
			DebugOut Far Enough Away... Stop running!
			gosub BaseRunCancel
			Exit
		Endif
	Endif


	gosub BaseRunAwayFace

	if ( g_bAskForHelp==TRUE )
		if ( g_hTarget!=NULL )
			Help g_hTarget
		endif
	endif

	Run

	GetRandomFloat RUN_AWAY_TICK_MIN, RUN_AWAY_TICK_MAX, g_nRandom
	Wait RUN_AWAY_WAIT, g_nRandom, BaseRunAwayTick

	Exit

;----------------------------------------------------------
:BaseRunAwayObstacle
;
;	See which way is the lesser of two evils....
;
;	p0 - hObstacle
;	p1-3 - Normal of collision...
;----------------------------------------------------------

	if ( g_nLastRunawayObstacle!=0 )
		GetTime g_nTemp
		Sub g_nTemp, g_nLastRunawayObstacle
		if ( g_nTemp < 1 )
			Add g_nRunawayObstacles,1
			if ( g_nRunawayObstacles > 2 )
				if ( g_bCanCower==TRUE )
					goto BaseRunCower
				else
					Stop
					goto BaseRunCancel
				Endif
			Endif
		else
			g_nRunawayObstacles = 0
		Endif
	Endif

	GetParam 1, g_dirX
	GetParam 2, g_dirY
	GetParam 3, g_dirZ

	GetTime g_nLastRunawayObstacle

;	Get distance at 90 degrees of angle...
	RotateDir g_dirX, g_dirY, g_dirZ, 90
	GetPos g_hTarget, g_targetX, g_targetY, g_targetZ
	VecScale g_dirX, g_dirY, g_dirZ, 120
	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	VecAdd g_posX,g_posY,g_posZ,g_dirX,g_dirY,g_dirZ
	VecDist g_posX,g_posY,g_posZ,g_targetX,g_targetY,g_targetZ,g_dist1

	CastRay g_dirX, g_dirY, g_dirZ, 100, g_hObject, g_nTemp

	if ( g_hObject!=NULL )
		g_dist1 = 0
	endif

	GetParam 1, g_dirX
	GetParam 2, g_dirY
	GetParam 3, g_dirZ

;	Get distance at -90 degrees of angle...
	RotateDir g_dirX, g_dirY, g_dirZ, -90
	VecScale g_dirX, g_dirY, g_dirZ, 120
	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	VecAdd g_posX,g_posY,g_posZ,g_dirX,g_dirY,g_dirZ
	VecDist g_posX,g_posY,g_posZ,g_targetX,g_targetY,g_targetZ,g_dist2

	CastRay g_dirX, g_dirY, g_dirZ, 100, g_hObject, g_nTemp

	if ( g_hObject!=NULL )
		g_dist2 = 0
	endif

	GetParam 1, g_dirX
	GetParam 2, g_dirY
	GetParam 3, g_dirZ

	if ( g_dist1 > g_dist2 )
		RotateDir g_dirX, g_dirY, g_dirZ, 90
	else
		if ( g_dist2 > g_dist1 )
			RotateDir g_dirX, g_dirY, g_dirZ, -90
		else
			; Boxed in!  go the direction of the "Normal"
			; (ie: leave g_dir alone...)

			;	Have us go in that direction for a while!
;;;;			DebugOut Boxed In!!!
			Wait RUN_AWAY_WAIT, 3.0, BaseRunAwayTick
		endif
	endif

	FaceDir g_dirX, g_dirY, g_dirZ, 0
	Run 	

	Exit TRUE

;----------------------------------------------------------
:BaseRunFindHidingPlace
;
;	If hiding place is found, stop doing the runAway mode
;	and just run to our hiding place...
;
;----------------------------------------------------------

	if ( g_bUseHidingPlaces==FALSE )
		g_hHidingPlace = NULL
		Exit
	endif

	FindHidingPlace g_hHidingPlace

	if ( g_hHidingPlace==NULL )
		Exit
	Endif

	gosub BaseRunHide

	Exit


;----------------------------------------------------------
:BaseRunHideTick
;----------------------------------------------------------

	if ( g_bAskForHelp==TRUE )
		if ( g_hTarget!=NULL )
			Help g_hTarget
		endif
	endif

	gosub BaseRunHide
	Wait HIDE_WAIT, HIDE_WAIT_TIME, BaseRunHideTick

	Exit

;----------------------------------------------------------
:BaseRunHideArrival
;----------------------------------------------------------
	Wait HIDE_WAIT, 0, DoNothing

	Stop
	SetIdle
	GetFaceDir g_hMyObject, g_dirX, g_dirY, g_dirZ

	RotateDir g_dirX, g_dirY, g_dirZ, 180

	FaceDir g_dirX, g_dirY, g_dirZ, 180

	GetTarget g_hObject
	
	if ( g_hObject!=NULL )
		Help g_hTarget
	endif

	gosub BaseRunCancel


	Exit

;----------------------------------------------------------
:BaseRunHide
;
;	Run to hiding place.
;
;----------------------------------------------------------

	if ( g_hHidingPlace==NULL )
		DebugOut Assert ( g_hHidingPlace!=NULL )
		Exit
	endif
	
	Wait RUN_AWAY_WAIT, 0, DoNothing

;We'll keep looking for a hiding spot....
	Wait HIDE_WAIT, HIDE_WAIT_TIME, BaseRunHideTick

	RunTo g_hHidingPlace,0, BaseRunHideArrival

	Exit

;----------------------------------------------------------
:BaseRunRandom
;----------------------------------------------------------

	gosub BaseRunAwayFace

; Setup our callbacks...
	OnObstacle BaseRunAwayObstacle

	gosub BaseRunAwayFace
;;;;	OnTargetBeyondDist MIN_RUNAWAY_DIST, BaseRunCancel
	g_bRunningAway = TRUE

	Run

	Wait RUN_AWAY_WAIT, RUN_AWAY_TICK_TIME, BaseRunAwayTick

;We'll keep looking for a hiding spot....
	Wait HIDE_WAIT, HIDE_WAIT_TIME, BaseRunFindHidingPlace

	Exit

;----------------------------------------------------------
:BaseRunAway
;
;	This assumes that g_hTarget is the handle of the one
;	we're running away FROM.
;
;----------------------------------------------------------
	if ( g_hTarget==NULL )
		GetTarget g_hTarget
		if ( g_hTarget==NULL )
			Exit
		Endif
	Endif

	if ( g_bCanCower==TRUE )
		GetRandomInt 0,100, g_nRandom
		;
		;	10% of time, just cower without running away...
		;
		if ( g_nRandom < 10 )
			gosub BaseRunCower
			exit
		endif
	endif

	GetTime g_nLastRunawayTime

;
;	Clear out whatever we were doing....
;	
	Stop
	SetIdle

	; Cannot "lose" the target in this manner...
	OnLostTarget BaseRunLostTarget

	gosub BaseRunFindHidingPlace

	if ( g_hHidingPlace==NULL )
		DebugOut No Hiding Place... Just running away.....
		gosub BaseRunRandom
		Exit
	else
		DebugOut Runing to hiding place!!
	endif

;
;	We have a hiding place... Time to run to it...
;

	Exit

;----------------------------------------------------------
:BaseRunOnFear
;
;	See if we've had the FEAR condition set on us....
;
;----------------------------------------------------------

	Debugout We've been hit with FEAR

	gosub BaseRunAway

	exit

;----------------------------------------------------------
:BaseRunOnFearDone
;
;	See if we've had the FEAR condition set on us....
;
;----------------------------------------------------------

	Debugout Fear is DONE... Cancel runaway...

	gosub BaseRunCancel

	exit

;----------------------------------------------------------
:OnRunAwayFromMe
;----------------------------------------------------------

	GetParam 0, g_hTarget

	Target g_hTarget, FALSE

	g_hRunAwayTrigger	= g_hTarget

	gosub BaseRunAway

	Exit

;----------------------------------------------------------
:BaseRunInit
;
;	Set up our fear & fear done callbacks...
;
;----------------------------------------------------------


	OnFear		BaseRunOnFear
	OnFearDone	BaseRunOnFearDone

	AddTrigger RunAwayFromMe, OnRunAwayFromMe

	gosub CanCower

	Exit
