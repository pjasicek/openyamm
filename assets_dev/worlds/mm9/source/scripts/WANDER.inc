;----------------------------------------------------------------
;	Wander.inc
;	Jeff Leggett
;	2/22/2000
;
;	Include file used by actors that wander around...
;
;----------------------------------------------------------------

#include aiglobals.inc

#number						MAX_DIST_FROM_STARTPOINT=750

#number						WANDER_WAIT_NBR = 8

#number						g_turnRate
#number						g_turnDeg

#number						g_startX
#number						g_startY
#number						g_startZ

#number						g_dist

#number						g_defaultLaunchAlt		= 200

;Number is a percentage 1 is 10% 2 is 20% ect.
#number						g_IdleFrequency			= 4
#number						g_SpecialAnimFrequency	= 3

;Sets the amount of time between idle checks.
#number						g_IdleCheckMin			= 5
#number						g_IdleCheckMax			= 5

;AI States
#number						g_IsAttacking			= 0
#number						g_IsRunning				= 0

;Turning degree
#number						g_TurnDegreeMin			= 15
#number						g_TurnDegreeMax			= 90

;time to see when we were last attacked
#number						g_CurrTime				= 0
#number						g_StopRunTime			= 0

; How fast do you want the ai to turn around when 
; they encounter an obstacle?
#number						g_wanderObstacleRotRate	= 90


;Farm animals will sometimes stop at obstacless
;instead of turning
#number						g_bStoppedAtObstacle	= 0
#number						g_bStopAtObstacle		= 0
#number						g_nStopAtObstacle		= 3
#number						g_StoppedRotX
#number						g_StoppedRotY	
#number						g_StoppedRotZ

;----------------------------------------------------------------
:WanderObstacle
;	p0		- handle to obstacle
;	p1-3	- Normal of the collision... 
;
;	For now, just go the opposite direction +- a little..
;----------------------------------------------------------------		
	;If we are running just go around
	if( g_IsRunning == TRUE )
		goto GoAroundObstacle
	else
	
		;if we are already stopped we go around it
		if( g_bStoppedAtObstacle == TRUE )
			Set g_rotX, g_StoppedRotX
			Set g_rotY, g_StoppedRotY
			Set g_rotZ, g_StoppedRotZ
			goto GoAroundObstacle
		endif
		
		GetRandomInt 1, 10, g_nRandom
		if( g_nRandom > g_nStopAtObstacle )
			goto GoAroundObstacle
		else
			;Save the rotation
			GetParam 1, g_StoppedRotX
			GetParam 2, g_StoppedRotY
			GetParam 3, g_StoppedRotZ

			;We are stopped so save that off as well
			Set g_bStoppedAtObstacle, TRUE

			Stop		
		endif
	endif
	
		
	:GoAroundObstacle
	Set g_bStoppedAtObstacle, FALSE

	GetParam 1, g_rotX
	GetParam 2, g_rotY
	GetParam 3, g_rotZ

	GetRandomFloat 0.2, 0.6, g_nRandom
	GetRandomInt 0,1, g_nTemp
	
	if ( g_nTemp==1 )
		Mul g_nRandom, -1
	endif

	Add g_rotX, g_nRandom

	GetRandomFloat 0.2, 0.6, g_nRandom
	GetRandomInt 0,1, g_nTemp
	
	if ( g_nTemp==1 )
		Mul g_nRandom, -1
	endif

	Add g_rotZ, g_nRandom

	FaceDir g_rotX, g_rotY, g_rotZ, g_wanderObstacleRotRate
	
	if( g_IsRunning == FALSE )
		Walk
	else
		Run
	endif
	

	;Setup next tick
	GetRandomFloat g_IdleCheckMin, g_IdleCheckMax, g_nRandom
	Wait WANDER_WAIT_NBR, g_nRandom, WanderTick


	exit TRUE

;----------------------------------------------------------------
:WanderGo
;
;	Picks a direction and goes...
;----------------------------------------------------------------

	GetRandomFloat g_TurnDegreeMin, g_TurnDegreeMax, g_turnDeg
;;	GetRandomFloat 20, 50, g_turnRate

	;Set g_turnRate, g_turnDeg
	
	if( g_IsRunning == FALSE )
		Set g_turnRate, 10
	else
		Set g_turnRate, 45
	endif

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	
	CalcDist g_posX,g_posY,g_posZ,g_startX,g_startY,g_startZ,g_dist

	if (g_dist>MAX_DIST_FROM_STARTPOINT)
		; Too far away from original starting point!!
		FacePos g_startX, g_startY, g_startZ, 180
	else
		GetRandomInt 0,1, g_nRandom

		if ( g_nRandom==0 )
			Mul g_turnDeg, -1
		endif

		Rotate 0,1,0,g_turnDeg,g_turnRate
	endif

	if( g_IsRunning == FALSE )
		Walk
	else
		Run
	endif
	
	GetRandomFloat g_IdleCheckMin, g_IdleCheckMax, g_nRandom	
	Wait WANDER_WAIT_NBR, g_nRandom, WanderTick	 

	Exit

;----------------------------------------------------------------
:WanderPause
;----------------------------------------------------------------
	if( g_IsAttacking == FALSE )
		if( g_IsRunning == FALSE )
			GetRandomInt 1, 10, g_nRandom
			if ( g_nRandom <= g_SpecialAnimFrequency )
				Trigger g_hMyObject, SpecialAnim
			else
				SetIdle
			endif
		endif	
	endif
	
	GetRandomFloat g_IdleCheckMin, g_IdleCheckMax, g_nRandom
	Wait WANDER_WAIT_NBR, g_nRandom, WanderTick	

	Exit

;----------------------------------------------------------------
:WanderTick
;----------------------------------------------------------------		
	if( g_IsRunning == TRUE )
		GetTime g_CurrTime		
		
		if( g_CurrTime > g_StopRunTime )
			Trigger g_hMyObject, StopRunning
		else
			Trigger g_hMyObject, Running
		endif
		
		gosub WanderGo
	else
		GetRandomInt 0, 10, g_nRandom
		if ( g_nRandom <= g_IdleFrequency )		
			gosub WanderPause			  		
		else		
			gosub WanderGo		
		endif
	endif

	Exit

;----------------------------------------------------------------
:WanderStuckDone
;----------------------------------------------------------------

	gosub WanderTick
	exit TRUE

;----------------------------------------------------------------
:WanderStartup
;----------------------------------------------------------------

	GetPos g_hMyObject, g_startX, g_startY, g_startZ

	gosub WanderTick

	exit TRUE

;----------------------------------------------------------------
:WanderInit
;----------------------------------------------------------------

	GetMyHandle	g_hMyObject
	OnObstacle WanderObstacle
	OnStuckDone WanderStuckDone

	; Must wait and do some stuff after initial execution...
	Wait WANDER_WAIT_NBR, 0.1, WanderStartup

	exit
