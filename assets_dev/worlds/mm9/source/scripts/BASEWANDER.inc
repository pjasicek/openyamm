;-------------------------------------------------------------
;	BaseWander.inc
;	Jeff Leggett
;
;	Handles basic wandering
;
;-------------------------------------------------------------

#include baseTimers.inc
#include aiglobals.inc
#include basedoor.inc


#number				MIN_WANDER_WAIT = 3
#number				MAX_WANDER_WAIT = 8

#number				MIN_WANDER_TIME = 3
#number				MAX_WANDER_TIME = 8

#number				bIsWandering = 0
#number				bWanderEnabled = 0
#number				bWanderDisabled = 0
#number				bWanderPaused = 0
#number				nWanderLeash = 500
#number				nWanderPathStart = 0

#number				wanderStartX = 0
#number				wanderStartY = 0
#number				wanderStartZ = 0


#number				normalX	= 0
#number				normalY = 0
#number				normalZ = 0
#number				bObstacle = 0


#string				sWanderPath
#number				nWanderPathCount = 0
#number				bWanderAimlessly = 0
#number				nCurrentMarker = 0
#number				bWanderRandom = 0

#hobject			hCurrentMarker = 0
#number				bFirstMarker = 1

#number				bFound = 0

;
;	Marker stat vars...
;
#number				g_bUseMarkerWaitTime=0
#number				g_nMarkerWaitMin=3
#number				g_nMarkerWaitMax=6


;-------------------------------------------------------------
:OnWanderAtMarkerNext
;-------------------------------------------------------------
;
;		We hit our marker.. Time to go to next one....
;

	Stop

;
;		See if we need to use the local marker's info...
;
	GetStat hCurrentMarker,UseMarkerWaitTime,g_bUseMarkerWaitTime

	if ( g_bUseMarkerWaitTime==TRUE )
		GetStat hCurrentMarker,WanderWaitMin,g_nMarkerWaitMin
		GetStat hCurrentMarker,WanderWaitMax,g_nMarkerWaitMax
		if ( g_nMarkerWaitMin==0 )
			g_nMarkerWaitMin = 0.01
		endif
		if ( g_nMarkerWaitMax==0 )
			g_nMarkerWaitMax = 0.01
		endif

	Endif

	GetStat hCurrentMarker,UseMarkerRotation,g_bTemp
	if ( g_bTemp==TRUE )
		GetFaceDir hCurrentMarker,g_dirX,g_dirY,g_dirZ
		FaceDir g_dirX,0,g_dirZ, 360
	Endif

	GetStat hCurrentMarker,PlayAnim,g_bTemp

	if ( g_bTemp==TRUE )
		GetStatStr hCurrentMarker,AnimationName,g_sTemp
		GetAnimNbr g_hMyObject,g_sTemp,g_nTemp
		if ( g_nTemp!=-1 )
			GetStat hCurrentMarker,LoopAnim,g_bTemp
			if ( g_bTemp==TRUE )
				LoopAnim g_nTemp,0
			else
				PlayAnim g_nTemp,MarkerAnimDone
			Endif
		Endif
	Endif

	hCurrentMarker = NULL

	; Do our normal wait... 
	gosub BaseWanderResume

	exit

;-------------------------------------------------------------
:OnWanderAtMarker
;
;	We touched a marker...
;
;-------------------------------------------------------------

	GetParam 0, g_hObject

	if ( g_hObject==hCurrentMarker )
;		GetObjectName hCurrentMarker,g_sTemp
;		g_sTemp = g_sTemp + ___AtMarker
;		cprint g_sTemp
;		debugout g_sTemp
		goto OnWanderAtMarkerNext
	endif

	Exit TRUE

;-------------------------------------------------------------
:MarkerAnimDone
;
;	This is here so you can potentially overload it....
;
;-------------------------------------------------------------
	Exit

;-------------------------------------------------------------
:BaseWanderGetFirstMarker
;
;	Returns handle to 1st marker
;
;-------------------------------------------------------------

	if ( bWanderRandom==TRUE )
		gosub BaseWanderGetNextMarker
		Exit
	endif

	if ( nWanderPathCount==0 )
		hCurrentMarker = NULL
		exit
	endif

;;	Set g_sTemp,sWanderPath
;;	Add g_sTemp,nWanderPathStart
	g_sTemp = sWanderPath + nWanderPathStart

	GetObjectHandle g_sTemp, hCurrentMarker

	Exit

;-------------------------------------------------------------
:ValidateWanderMarker
;
;	Will set bFound to FALSE if marker is not valid...
;
;-------------------------------------------------------------

	IsClass g_hMyObject,NPC,g_bTemp
	if ( g_bTemp==FALSE )
		Exit
	Endif
	
	Add g_nCounter,1

	g_nTemp	= nWanderPathCount * 3

	if ( g_nCounter>=g_nTemp )
	; No markers are valid.... We did our best, just punt...
		Exit
	Endif
	
	g_sTemp = sWanderPath + nCurrentMarker
	GetObjectHandle g_sTemp, g_hObject

	if ( g_hObject!=NULL )
		CanReachObject g_hObject,g_bTemp
		if ( g_bTemp==FALSE )
			bFound = FALSE
		endif
	endif

	Exit

;-------------------------------------------------------------
:BaseWanderGetNextMarker
;
;	Gets handle to next path
;
;-------------------------------------------------------------

	if ( nWanderPathCount==0 )
		hCurrentMarker = NULL
		exit
	endif

	if ( bWanderRandom==TRUE )
		bFound = FALSE
		g_nCounter = 0
		while ( bFound==FALSE )
			if ( nWanderPathCount==2 )
				if ( nCurrentMarker==0 )
					nCurrentMarker = 1
				else
					nCurrentMarker = 0
				endif
				bFound = TRUE
			else
				g_nTemp = nWanderPathCount - 1
				GetRandomInt 0, g_nTemp, g_nTemp
				if ( g_nTemp!=nCurrentMarker )
					nCurrentMarker = g_nTemp
					bFound = TRUE
					; will set bFound = FALSE if it's no good.
					gosub ValidateWanderMarker
				endif
			endif
		endwhile
	else
		Add nCurrentMarker, 1
		Mod nCurrentMarker, nWanderPathCount
	endif

;;	Set g_sTemp,sWanderPath
;;	Add g_sTemp,nCurrentMarker
	g_sTemp = sWanderPath + nCurrentMarker
	
	GetObjectHandle g_sTemp, hCurrentMarker

	Exit


;-------------------------------------------------------------
:BaseWanderLeashCheck
;
;
;	Just checks if we're beyond our leash distance...
;-------------------------------------------------------------

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	g_posY = wanderStartY

	CalcDist g_posX,g_posY,g_posZ,wanderStartX,wanderStartY,wanderStartZ,g_nTemp

	if ( g_nTemp >= nWanderLeash )
		; When we start again, we'll head for our start point....
		Stop
		Exit
	endif

	Wait WANDER_LEASH_WAIT, 0.25, BaseWanderLeashCheck

	Exit

;-------------------------------------------------------------
:BaseWanderStartWalking
;
;	We should be facing the way we want to...
;	Walk!!!
;	
;-------------------------------------------------------------

	Walk
	
	GetRandomFloat MIN_WANDER_TIME, MAX_WANDER_TIME, g_nRandom

	if ( bWanderAimlessly==TRUE )
		Wait WANDER_WAIT, g_nRandom, BaseWanderStopTick
	endif

	if ( nWanderLeash!=0 )
		Wait WANDER_LEASH_WAIT, 0.25, BaseWanderLeashCheck
	endif

	Exit

;-------------------------------------------------------------
:BaseWanderObstacle
;
; Stop, and remember the normal of our obstacle...
;
;   
;-------------------------------------------------------------

	if ( hCurrentMarker!=NULL )
		Exit FALSE
	endif

	GetRandomInt 0, 100, g_nRandom

	GetParam 0, g_hObject
	IsClass g_hObject,Actor, g_bTemp

	if ( g_bTemp==TRUE )
		if ( g_nRandom < 90 )
			Exit FALSE
		endif	
	else
		if ( g_nRandom < 70 )
			Exit FALSE
		endif	
	endif

	GetParam 1, normalX
	GetParam 2, normalY
	GetParam 3, normalZ

	gosub BaseWanderPause
	Stop
	Wait WANDER_LEASH_WAIT, 0, DoNothing
	bObstacle = TRUE
	gosub BaseWanderResume

	GetParam 0, g_hObject
	IsClass g_hObject,Actor, g_bTemp
	if ( g_bTemp==FALSE )
		FaceDir normalX, 0, normalZ, 360
	Endif

	
	Exit TRUE

;-------------------------------------------------------------
:BaseWanderStuck
;-------------------------------------------------------------

	gosub BaseWanderPause

	Exit FALSE

;-------------------------------------------------------------
:BaseWanderStuckDone
;-------------------------------------------------------------
	
	gosub BaseWanderResume

	Exit TRUE


;-------------------------------------------------------------
:BaseWanderPickRandomDir
;-------------------------------------------------------------
	if ( bObstacle==TRUE )
		; We've already turned around 180 from the obstacle...
		; Now just turn a little one way or the other...
		bObstacle = FALSE
		GetRandomFloat 15, 90, g_nRandom
	else
		GetRandomFloat 15, 180, g_nRandom
	endif

	GetRandomInt FALSE,TRUE,g_bTemp

	if ( g_bTemp==TRUE )
		g_nRandom = g_nRandom * -1
	endif

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	g_posY = wanderStartY

	CalcDist g_posX,g_posY,g_posZ,wanderStartX,wanderStartY,wanderStartZ,g_nTemp

	if ( nWanderLeash!=0 )
		if ( g_nTemp >= nWanderLeash )
			FacePos wanderStartX, wanderStartY, wanderStartZ, 180
		else
			Rotate 0,1,0, g_nRandom, 180
		endif
	else
			Rotate 0,1,0, g_nRandom, 180
	endif

	Exit

;-------------------------------------------------------------
:BaseWanderPathArrived
;
;	We've hit a path point... Time to wait....
;
;-------------------------------------------------------------

	g_sTemp = hCurrentMarker
	SetParam 0,g_sTemp
	gosub OnWanderAtMarker

	Exit TRUE
;-------------------------------------------------------------
:CanReachCurrentMarker
;-------------------------------------------------------------

	CanReachObject hCurrentMarker, g_bTemp

	exit

;-------------------------------------------------------------
:BaseWanderNextPathDir
;
;	Get handle of next marker... Then turn towards it!
;	
;-------------------------------------------------------------

	if ( bFirstMarker==TRUE )
		bFirstMarker = FALSE
		gosub BaseWanderGetFirstMarker
	else
		gosub BaseWanderGetNextMarker
	endif

	if ( hCurrentMarker==NULL )
		Exit
	endif

	gosub CanReachCurrentMarker

	if ( g_bTemp==FALSE )
		DebugOut Cannot reach following marker.  Wandering aimlessly!
		if ( hCurrentMarker==NULL )
			DebugOut CurrentMarker is NULL!
		else
			g_sTemp = Error
			GetObjectName hCurrentMarker,g_sTemp
			DebugOut g_sTemp
		endif

		bWanderAimlessly = TRUE
		nWanderPathCount = 0
	else
;		GetObjectName hCurrentMarker,g_sTemp
;		cprint WalkingTo
;		cprint g_sTemp
;		DebugOut g_sTemp

		WalkTo hCurrentMarker, 1, BaseWanderPathArrived
	endif

	Exit

;-------------------------------------------------------------
:BD_DoorOpen
;
;	If we are currently wandering toward a marker, walk to
;	it...
;
;-------------------------------------------------------------
	g_bDoorOpening = FALSE

	if ( hCurrentMarker==NULL )
		gosub BD_DoorOpen,1
		Exit
	Endif

;	GetObjectName hCurrentMarker,g_sTemp
;	cprint WalkingTo
;	cprint g_sTemp
;	DebugOut g_sTemp

	WalkTo hCurrentMarker, 1, BaseWanderPathArrived

	RestorePath

	Exit

;-------------------------------------------------------------
:BaseWanderGo
;
;	Pick my direction and start moving....
;
;-------------------------------------------------------------

	gosub BaseDoorInit
	OnObstacle BaseWanderObstacle
	OnStuckDone BaseWanderStuckDone
	OnStuck BaseWanderStuck

	bIsWandering = TRUE

	if ( bWanderAimlessly==FALSE )
		gosub BaseWanderNextPathDir
		if ( bWanderAimlessly==FALSE )
			; If BaseWanderNextPathDir determined that we cannot
			; reach the original wander path that was setup, then
			; we won't exit...
			Exit
		endif
	endif

	gosub BaseWanderPickRandomDir
	gosub BaseWanderStartWalking

	Exit

;-------------------------------------------------------------
:BaseWanderResume
;-------------------------------------------------------------
	if ( bIsWandering==FALSE )
		Exit
	endif

	bWanderPaused = FALSE

	gosub BaseWanderStart

	Exit

;-------------------------------------------------------------
:BaseWanderPause
;-------------------------------------------------------------
	bWanderPaused = TRUE
	Wait WANDER_WAIT, 0, DoNothing

	Exit

;-------------------------------------------------------------
:BaseWanderStart
;
;	Call this to start up the wander again.  Usually after
;	you're done attacking someone....
;-------------------------------------------------------------

	OnObstacle BaseWanderObstacle
	OnStuckDone BaseWanderStuckDone
	OnStuck BaseWanderStuck

	if ( g_bUseMarkerWaitTime==TRUE )
		GetRandomFloat g_nMarkerWaitMin,g_nMarkerWaitMax,g_nRandom
		g_bUseMarkerWaitTime = FALSE
	else
		GetRandomFloat MIN_WANDER_WAIT, MAX_WANDER_WAIT, g_nRandom
	endif

	if ( g_nRandom < 0.2 )
		Wait WANDER_WAIT, 0, DoNothing
		gosub BaseWanderStartTick
		exit
	Endif
	
	Wait WANDER_WAIT, g_nRandom, BaseWanderStartTick
	
	Exit

;-------------------------------------------------------------
:BaseWanderStop
;
;	Call this to stop wander thinking... Usually when you
;	are busy attacking someone....
;-------------------------------------------------------------

	Wait WANDER_WAIT, 0, DoNothing
	Wait WANDER_LEASH_WAIT, 0, DoNothing

	bObstacle = FALSE
	bIsWandering = FALSE
	hCurrentMarker = NULL
	g_bUseMarkerWaitTime = FALSE

	Exit

;-------------------------------------------------------------
:CanWander
;
;	Set g_bTemp = TRUE if now's an OK time to wander...
;
;-------------------------------------------------------------
	g_bTemp = TRUE
	GetStat g_hMyObject,CanWander,g_bTemp
	Exit

;-------------------------------------------------------------
:BaseWanderStartTick
;
;	When this fires, it's time to decide if we want to start
;	wandering....
;	
;-------------------------------------------------------------

	gosub CanWander

	if ( g_bTemp==FALSE )
		GetRandomFloat MIN_WANDER_WAIT, MAX_WANDER_WAIT, g_nRandom
		Wait WANDER_WAIT, g_nRandom, BaseWanderStartTick
		Exit
	Endif

	gosub BaseWanderGo

	Exit

;-------------------------------------------------------------
:BaseWanderStopTick
;
;	When this fires, it's time to decide if we want to stop
;	wandering....
;	
;-------------------------------------------------------------

	Wait WANDER_LEASH_WAIT, 0, DoNothing
	Stop
	gosub BaseWanderStart

	Exit

;-------------------------------------------------------------
:BaseWanderForceStartUp
;
;	Enable it and start it up...
;
;-------------------------------------------------------------

	if ( bWanderEnabled==FALSE )
		bWanderEnabled = TRUE
		gosub BaseWanderStartup
		Exit
	endif

	gosub BaseWanderStart

	Exit
;-------------------------------------------------------------
:OnWanderTrigger
;
;	We've been triggered to start wandering...
;
;-------------------------------------------------------------
	
	if ( bWanderEnabled==TRUE )
		gosub BaseWanderGo
	else
		gosub BaseWanderForceStartUp
	endif
	
	exit

;-------------------------------------------------------------
:BaseWanderStartup
;-------------------------------------------------------------

	GetStat g_hMyObject, WanderPathCount, nWanderPathCount
	GetStat g_hMyObject, WanderPathRandom, bWanderRandom
	GetStat g_hMyObject, WanderLeash, nWanderLeash

	GetStat g_hMyObject, WanderWaitMin, MIN_WANDER_WAIT
	GetStat g_hMyObject, WanderWaitMax, MAX_WANDER_WAIT

	if ( MIN_WANDER_WAIT==0 )
		MIN_WANDER_WAIT = 0.01
	endif
	if ( MAX_WANDER_WAIT==0 )
		MAX_WANDER_WAIT = 0.01
	endif

	GetStat g_hMyObject, WanderTimeMin, MIN_WANDER_TIME
	GetStat g_hMyObject, WanderTimeMax, MAX_WANDER_TIME
	GetStat g_hMyObject, WanderPathStart, nWanderPathStart

	if ( MIN_WANDER_TIME==0 )
		MIN_WANDER_TIME = 0.01
	endif
	if ( MAX_WANDER_TIME==0 )
		MAX_WANDER_TIME = 0.01
	endif

	GetStatStr g_hMyObject, WanderPathName, sWanderPath

	if ( nWanderPathCount<=1 )
		nWanderPathCount = 0
	else
		; No leash with wander paths!
		nWanderLeash = 0
	endif

	if ( nWanderPathStart >= nWanderPathCount )
		nWanderPathStart = 0
	Endif

	if ( nWanderPathCount==0 )
		bWanderAimlessly = TRUE
	else
;;		traceON
	endif


	GetPos g_hMyObject, wanderStartX, wanderStartY, wanderStartZ

	if ( bWanderDisabled==FALSE )
		gosub BaseWanderStart
	Endif

	Exit

;-------------------------------------------------------------
:OnWanderStopTrigger
;
;	We've been triggered to stop wandering...
;-------------------------------------------------------------

	gosub BaseWanderStop

	Exit

;-------------------------------------------------------------
:BaseWanderInit
;
;	Don't forget to call this in your Main function...
;
;	Also, you must setup g_hMyObject prior to calling this
;	function!
;
;-------------------------------------------------------------

	GetMyHandle g_hMyObject

	bWanderEnabled = FALSE

	AddTrigger Wander, OnWanderTrigger
	AddTrigger WanderStop, OnWanderStopTrigger
	AddTrigger TouchedMarker, OnWanderAtMarker

	GetStat g_hMyObject, WanderEnable, bWanderEnabled
	if ( bWanderEnabled==FALSE )
		; No more to do now!
		Exit
	endif

	; Wait a little and then startup.. (so all the names are in...)
	Wait 9, 1, BaseWanderStartup

	Exit
