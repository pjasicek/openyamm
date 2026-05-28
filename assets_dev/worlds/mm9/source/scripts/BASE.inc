;------------------------------------------
;	base.inc
;	Jeff Leggett
;
;	This include file contains base monster
;	handling.  Basically, the monster sees
;	the player.  Runs after him and keeps
;	attacking.  Nothing fancy here.
;	
;	NOTE: Be sure to gosub InitBase in your
;	:main routine.
;------------------------------------------


#include aiglobals.inc
#include baseTimers.inc
#include baseWander.inc
#include BaseRun.inc
#include BaseEvade.inc
#include BaseDoor.inc
#include SpeedThrottle.inc


#number				MIN_STUCK_TIME = 5
#number				BORED_WITH_TARGET_TIME = 2
#number				MIN_CHECK_REACH_TIME = 0.4
#number				MIN_CHECK_REACH_TIME2 = 0.1

#number				g_nDist1
#number				g_nDist2

#number				g_nStuckTime = 0
#number				g_nGoingHome = 0

#number				g_lastDamageType = 0

#number				g_nLastDamage

#number				g_bAlwaysRunToTarget = 1

#number				g_bClearShot
#number				g_bShouldAttack

#number				g_bFaceTarget = 1
#number				g_bCanHeadTurn = 0
#number				g_bBaseGoGetHim = 0
#number				g_bCanBlendAnim = 0

#string				g_sMyClassName

#number				g_targetOutOfReachStart = 0

#number				g_bClearTargetOnObstacle = 0


#number				g_nMaxEvadeDist = 180

#number				g_nEvadeChance = 40
#number				g_nStrafeAttackPct = 80

#number				TAUNT_CHANCE = 40

#number				g_nLastCanReachCheck = 0

#number				g_bCanReach = 1


;------------------------------------------
:BaseStuck
;------------------------------------------

	SetIdle

	Exit TRUE

;------------------------------------------
:DisableWandering
;
;	Do all things necessary to disable
;	Wandering...
;
;------------------------------------------

	gosub BaseWanderStop

	OnObstacle					BaseObstacle
	OnStuckDone					BaseStuckDone
	OnStuck						BaseStuck

	Exit

;------------------------------------------
:EnableWandering
;
;	Do all things necessary to disable
;	Wandering...
;
;------------------------------------------

	gosub BaseWanderStart

	Exit

;------------------------------------------
:ShouldAttack
;
;	output: g_bShouldAttack
;------------------------------------------
	g_bShouldAttack = FALSE

	IsClearShot g_hTarget, g_bClearShot

	if ( g_bClearShot==TRUE )
		g_bShouldAttack = TRUE
		Exit
	endif

;
;	Even without a clear shot, sometimes we should
;	go ahead and attack...
;

;	GetRandomInt 0, 100, g_nRandom

;	if ( g_nRandom < 20 )
;		g_bShouldAttack = TRUE
;	endif

	Exit

;------------------------------------------
:BaseGoGetHim
;
;	Sets g_bBaseGoGetHim to FALSE if we 
;	didn't run/walk after him...
;
;------------------------------------------

	g_bBaseGoGetHim = FALSE

	if ( g_hTarget==NULL )
		Exit FALSE
	endif

	if ( g_bRunningAway==TRUE )
		Exit TRUE
	EndIf

;;;;	IsAttacking g_bAttacking

;;;;	if ( g_bAttacking==TRUE )
;;;;		Exit TRUE
;;;;	endif


	g_targetOutOfReachStart = 0

	IsTargetInRange g_bInAttackRange

	if ( g_bInAttackRange==TRUE )
		CanAttack g_bCanAttack

		if ( g_bCanAttack==TRUE )
			gosub ShouldAttack

			if ( g_bShouldAttack==TRUE )
				gosub BaseDoAttack
				Exit TRUE
			else
				; Go into stuck mode... (just pauses the action, when the stuck anim is done, we'll go after him again)
				;;;;;;  SetStuck
				Exit TRUE
			endif
		else
			Exit TRUE
		endif
	endif

;
;	Make sure we're using the correct movement callbacks...
;

	OnCongestion				BaseCongestion
	OnPathClear					BasePathClear
	OnObstacle					BaseObstacle

	g_nTemp = g_attackRange
	IsAttacking g_bTemp
	if ( g_bTemp==TRUE )
		Mul g_nTemp, 0.4
	else
		Mul g_nTemp, 0.6
	endif

	if ( g_bAlwaysRunToTarget==TRUE )
		RunTo g_hTarget, g_nTemp, AggressiveArrival
	else

		if ( g_bFighting==TRUE )
			RunTo g_hTarget, g_nTemp, AggressiveArrival
		else
			WalkTo g_hTarget, g_nTemp, AggressiveArrival
		endif
	endif

	g_bBaseGoGetHim = TRUE
		
	Exit TRUE


;------------------------------------------
:AggressiveTick
;------------------------------------------

	Wait AGGRESSIVE_WAIT, 0.1, AggressiveTick

	if ( g_hTarget==NULL )
		Exit
	Endif

	IsTargetInRange g_bInAttackRange

	if ( g_bInAttackRange==FALSE )
		GetStat g_hTarget,IsFlying,g_bTemp

		if ( g_bTemp==TRUE )
			GetTime g_nTemp
			g_nTemp = g_nTemp - g_nLastCanReachCheck

			g_bTemp = FALSE
			if ( g_bCanReach==FALSE )
				if ( g_nTemp > MIN_CHECK_REACH_TIME2 )
					g_bTemp = TRUE
				endif
			else
				if ( g_nTemp > MIN_CHECK_REACH_TIME )
					g_bTemp = TRUE
				endif
			endif

			if ( g_bTemp==TRUE )
				GetTime g_nLastCanReachCheck
				CanReachTarget g_bCanReach
				if ( g_bCanReach==FALSE	)
					Stop
				endif
			Endif
		Endif

		if ( g_bCanReach==TRUE )
			gosub BaseGoGetHim
		endif

		Exit
	else
		g_bCanReach	= TRUE
	EndIf

	CanAttack g_bTemp

	if ( g_bTemp==FALSE )
		Exit
	EndIf

;	If we're backpedaling and want to go get him, let's stop...
	GetStat g_hMyObject,BackPedaling,g_bTemp
	if ( g_bTemp==TRUE )
		Stop
	Endif

;	If we're strafing and want to go get him, let's stop...
	GetStat g_hMyObject,Strafing,g_bTemp
	if ( g_bTemp==TRUE )
		Stop
	Endif

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:AggressiveStart
;------------------------------------------
	
	Wait AGGRESSIVE_WAIT, 0.1, AggressiveTick
	Exit

;------------------------------------------
:AggressiveStop
;------------------------------------------
	Wait AGGRESSIVE_WAIT,0,DoNothing

	Exit

;------------------------------------------
:AggressiveArrival
;
;	Decide if we should keep running after 
;	the target or not...
;
;------------------------------------------

	if ( g_hTarget==NULL )
		Exit FALSE
	Endif

	GetVelocity g_hTarget, g_velX, g_velY, g_velZ

	VecMag g_velX, g_velY, g_velZ, g_nDist1
	g_nTemp = g_walkVel * 0.5

	if ( g_nDist1 > g_nTemp )
		Exit TRUE
	Endif

;;	Stop

	Exit TRUE

;------------------------------------------
:BaseSetFaceTarget
;------------------------------------------
	if ( g_bCanHeadTurn==TRUE )
		g_bFaceTarget = FALSE
	else
		g_bFaceTarget = TRUE
	endif

	Exit

;------------------------------------------
:BaseRotationDone
;------------------------------------------

	gosub BaseSetFaceTarget
	gosub BaseSetupTarget

	GetRandomInt 0, 100, g_nRandom

;
; Only do the aware sometimes...
;
	if ( g_nRandom < 30 )
		Aware BaseAwareDone
	else
		gosub BaseAwareDone
	endif

	Exit

;------------------------------------------
:BaseAwareDone
;
;	In an attempt to keep AI from looking
;	like they're doing everything in-sync,
;	we'll wait a random amount of time 
;	before we go get him...
;------------------------------------------

	GetRandomFloat 0.1, 0.5, g_nRandom
	Wait AGGRESSIVE_WAIT, g_nRandom, BeAggressive

	Exit TRUE

;------------------------------------------
:BaseFoundPlayer
;
;	Found a player, set it as our current
;	target and run after him!
;------------------------------------------

	GetParam 0, g_hTarget

	if ( g_hTarget==0 )
;		This shouldn't happen, but you can't be too careful!
		Exit FALSE
	Endif

	ShouldRunAway g_hTarget, g_bTemp

	if ( g_bTemp==TRUE )
		Target g_hTarget, FALSE
		gosub BaseRunAway
		Exit TRUE
	endif

	SendAlert g_hTarget

	gosub BaseSetFaceTarget
	gosub BaseSetupTarget

	; Turn and face target before running after him!
;;;;;	FaceObject g_hTarget, 180, BaseRotationDone
	FaceObject g_hTarget, 180

	gosub BaseRotationDone

	Exit TRUE


;------------------------------------------
:BaseEvadeDone
;------------------------------------------
;;	Stop
	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseAttackPerformed
;------------------------------------------
	g_bAttackPerformed = TRUE

	Exit FALSE

;------------------------------------------
:ShouldEvade
;
;	Returns TRUE or FALSE in g_bTemp
;------------------------------------------

	GetRandomInt 0,100,g_nRandom
	GetStat g_hMyObject, EvadeChance, g_nEvadeChance

	if ( g_nRandom < g_nEvadeChance )
		g_bTemp = TRUE
	else
		g_bTemp = FALSE
	Endif

	Exit

;------------------------------------------
:BaseAttackDone
;------------------------------------------

	if ( g_hTarget==NULL )
		Stop
		Exit FALSE
	endif

;;	Stop

	gosub ShouldEvade

	if ( g_bTemp==TRUE )
		GetStat g_hMyObject,RecoveryTime,g_nEvadeTime
		gosub SpeedThrottleStop
		gosub BaseEvadeStart
		OnTargetBeyondDist g_nMaxEvadeDist, BeAggressive

		g_nTemp = g_nEvadeTime
;;;;		Mul g_nTemp, 0.8

		if ( g_nTemp < 1 )
			g_nTemp = 1
		Endif

		Wait AGGRESSIVE_WAIT, g_nTemp, BeAggressive
	else
		gosub IsTargetMoving
		if ( g_bTemp==FALSE )
			AIGetDistance g_hTarget, g_nDist1

			if ( g_nDist1 < g_attackRange )
				GetStat g_hMyObject,RecoveryTime,g_nEvadeTime
				gosub SpeedThrottleStop
				gosub BaseEvadeStart
				OnTargetBeyondDist g_nMaxEvadeDist, BeAggressive

				; Back off, but don't go too far away...
				g_nTemp = g_nEvadeTime * 0.5

				Wait AGGRESSIVE_WAIT, g_nTemp, BeAggressive
			else
				Stop
				GetRandomInt 0, 100, g_nRandom
				if ( g_nRandom < TAUNT_CHANCE )
					Wait AGGRESSIVE_WAIT, 1, BeAggressive
					Taunt BeAggressive
				Endif
			Endif
		Endif
	EndIf


;		Let our aggressive tick handle this stuff...
;;;;;;;	gosub BaseSetFaceTarget
;;;;;;;	Target g_hTarget, g_bFaceTarget

;;;;;;;	gosub BaseGoGetHim


	Exit TRUE

;------------------------------------------
:BaseEvadeStop
;------------------------------------------

	gosub BaseEvadeStop,1

	OnPathClear					BasePathClear
	OnObstacle					BaseObstacle
	OnTargetBeyondDist 0

	if (g_bCanBlendAnim==TRUE)
		OnTargetOutOfRange			BaseTargetOutOfRange
	Endif

	gosub SpeedThrottleStart

	Exit


;------------------------------------------
:BeAggressive
;------------------------------------------

	gosub BaseEvadeStop

	g_bBaseGoGetHim = FALSE
	gosub AggressiveTick

	if ( g_bBaseGoGetHim==FALSE )
;;		Stop
	Endif

	Exit

;------------------------------------------
:BaseDoAttack
;------------------------------------------

	g_bFighting = TRUE

	GetTime g_nLastAttackTime

	if ( g_hTarget!=NULL )
		GetPos g_hTarget, g_posX, g_posY, g_posZ
		FacePos g_posX, g_posY, g_posZ, 360
	EndIf

	g_bAttackPerformed = FALSE
	Target g_hTarget, TRUE

	gosub IsTargetMoving
;
;	if they're not moving, attack and strafe past them..
;
	if ( g_bCanBlendAnim==TRUE )
		if ( g_bTemp==FALSE )

			GetRandomInt 0, 100, g_nRandom

			if ( g_nRandom < g_nStrafeAttackPct )
				g_bPickDir = TRUE
				gosub BE_AttackStrafe
				g_bPickDir = TRUE
				g_bStrafeAttack = TRUE
			else
				Stop
			Endif
		else
			g_bStrafeAttack = FALSE
		endif
	else
		g_bStrafeAttack = FALSE
		Stop
	endif

	Attack BaseAttackDone

	Wait AGGRESSIVE_WAIT, 2, AggressiveTick


	Exit

;------------------------------------------
:BaseAttackReady
;
;	We are now in attack range (for our
;	currently selected weapon) and ready
;	to attack.  So let's do it!
;------------------------------------------

;	gosub ShouldAttack

;	if ( g_bShouldAttack==TRUE )
;		gosub BaseDoAttack
;		Exit
;	endif

;;	gosub BaseGoGetHim

	Exit TRUE

;------------------------------------------
:BaseLostTarget
;
;	We've lost the target, so let's go idle.
;------------------------------------------

	g_hTarget = NULL
	g_bFighting = FALSE

	gosub BaseClearTarget
	
	SetIdle

	Exit

;------------------------------------------
:BaseStuckDone
;
;	This is called when a stuck animation
;	has finished... We'll just re-attempt
;	to run after our target...
;------------------------------------------

	if ( g_hTarget==NULL )
		Exit FALSE
	endif


	; for now, don't wait when stuck..

	gosub BaseGoGetHim

	if ( g_bBaseGoGetHim==TRUE )
		exit TRUE
	endif

	if ( g_nStuckTime==0.0 )
		GetTime g_nStuckTime
	else
		GetTime g_nTemp
		Sub g_nTemp, g_nStuckTime

		if ( g_nTemp > MIN_STUCK_TIME )
			g_nStuckTime = 0
			Exit FALSE
		endif
	endif
	
	SetStuck

	Exit TRUE

;------------------------------------------
:IsAttackerValidTarget
;
;	Returns g_bTemp = TRUE or FALSE
;------------------------------------------

	g_bTemp = FALSE

	if ( g_hAttacker==g_hMyObject )
		exit
	endif

	if ( g_hAttacker==NULL )
		exit
	endif

	IsActor g_hAttacker, g_nTemp

	if ( g_nTemp==FALSE )
		exit
	endif

	IsFriend g_hAttacker, g_bTemp

	if ( g_bTemp==TRUE )
		g_bTemp = FALSE
	else
		g_bTemp = TRUE
	endif
	
;	GetClassName g_hAttacker, g_sTemp
;	if ( g_sTemp==g_sMyClassName )
;		exit
;	endif
;	Set g_bTemp, TRUE

	exit


;------------------------------------------
:BaseRunAway
;
;	Overloading on purpose....
;
;------------------------------------------
	if ( g_hTarget==NULL )
		Exit
	endif

	gosub BaseEvadeStop
	OnProjectile
	OnFoundPlayer
	OnTargetOutOfRange

	gosub DisableWandering
	gosub ChaseStop
	gosub AggressiveStop

	gosub BaseRunAway, 1

	exit


;----------------------------------------------------------
:BaseRunCancel
;
;	We're overloading the function here....
;
;----------------------------------------------------------

	gosub BaseRunCancel,1

	g_hTarget = NULL
	Target NULL
	Stop

	OnProjectile BaseOnProjectile, 200
	OnFoundPlayer BaseFoundPlayer

	gosub EnableWandering

	Exit


;------------------------------------------
:BaseCheckAttacker
;
;	Looks at last attacker and decides
;	if we want to go after him...
;------------------------------------------

	gosub IsAttackerValidTarget

	if ( g_bTemp==FALSE )
		goto BaseSkipTargetSwitch
	endif

	ShouldRunAway g_hAttacker, g_bTemp

	if ( g_bTemp==TRUE )
		g_hTarget = g_hAttacker
		Target g_hTarget, FALSE
		gosub BaseRunAway
		Exit TRUE
	endif

	if ( g_hTarget==NULL )
		g_hTarget = g_hAttacker
		g_bFighting = TRUE
	else
		IsTargetInRange g_bInAttackRange

		if ( g_hAttacker!=NULL )
			if ( g_hAttacker!=g_hTarget )
				GetClassName g_hAttacker, g_sTemp
;;				if ( g_sTemp!=Player )
;;					goto BaseSkipTargetSwitch
;;				endif
				; 70% chance we'll switch to the damager
				g_nTemp = 70
				if ( g_bInAttackRange==TRUE )
					; we're already in attack range of our current target
					; so lower chances of switching
					g_nTemp = 45
				endif

				AIGetDistance g_hTarget, g_nDist1
				AIGetDistance g_hAttacker, g_nDist2

				if ( g_nDist2 > g_nDist1 )
					; reduce odds even further...
					Divide g_nTemp, 2
				endif

				GetRandomInt 0, 100, g_nRandom
				if ( g_nRandom < g_nTemp )
					; 
					; Okay, we decided to switch our current target to the 
					; attacker!
					;
					g_hTarget = g_hAttacker
				endif
			endif
		endif
	endif

:BaseSkipTargetSwitch

	if ( g_hTarget==NULL )
		Exit FALSE		; FALSE means have the AI do its default handling of this event.
	endif

	; Go after the Target...

	gosub BaseSetFaceTarget
	gosub BaseSetupTarget

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseDamageDone
;
;	We were attacked, now we want to run
;	after whoever attacked us!
;	
;------------------------------------------

	gosub BaseCheckAttacker
	Exit

;------------------------------------------
:BaseSetupAttacker
;------------------------------------------

	CreateObjectLink g_hAttacker


	IsFriend g_hAttacker, g_bTemp

	if (g_bTemp==FALSE)
		SendAlert g_hAttacker
	endif

	Exit

;------------------------------------------
:BaseDamage
;
;	p0 = hAttacker
;	p1 = HitPoints
;	p2 = DamageType
;
;------------------------------------------

	GetParam 0, g_hAttacker
	GetParam 1, g_nLastDamage
	GetParam 2, g_lastDamageType

	gosub BaseSetupAttacker

	if( g_nLastDamage == 0 )
		gosub BaseDamageDone
	endif		   

	Exit FALSE


;------------------------------------------
:BaseObjectLinkBroken
;
;	Any object handle that I create a link
;	for needs to be checked in this routine
;------------------------------------------

	GetParam 0, g_hObject

	if (g_hObject==g_hAttacker)
		g_hAttacker = NULL
	endif

	if (g_hTarget==g_hObject)
		gosub BaseClearTarget
	endif

	Exit

;------------------------------------------
:BaseCongestion
;
;	If there is congestion in the way, 
;	start walking
;------------------------------------------
	Exit FALSE

	if ( g_hTarget!=NULL )
		if ( g_bRunningAway==FALSE )
			WalkTo g_hTarget, 0, AggressiveArrival
		Endif
	endif

	Exit TRUE

;------------------------------------------
:BasePathClear
;------------------------------------------

	if ( g_hTarget!=NULL )
		gosub BaseGoGetHim
	endif

	Exit TRUE

;------------------------------------------
:BaseTargetDead
;------------------------------------------

	GetParam 0, g_nTemp

	gosub BaseClearTarget


;	if ( g_nTemp==g_hMyObject )
;		;
;		;	We killed him!
;		;
;		; taunt him, and go home....
;		Taunt BaseGoHome
;	else
;		; just go home...
;		gosub BaseGoHome 
;	endif

	Exit TRUE

;------------------------------------------
:BaseImHome
;
;
;	I made it back home, now, rotate to
;	face the way I was facing...
;------------------------------------------

	Exit

;------------------------------------------
:BaseGoHome
;
;	Sends ai back to where it started
;
;	NOTE: if we ge stuck on way back home,
;   we will just stay there...
;------------------------------------------

	; for now, just go back into idle loop...
	Stop
	SetIdle

;;	Set g_nGoingHome, TRUE
;;	WalkToPos g_homeX, g_homeY, g_homeZ, BaseImHome

	Exit

;------------------------------------------
:BaseObstacle
;
;------------------------------------------

	if ( g_bClearTargetOnObstacle==TRUE )
		if ( g_hTarget!=NULL )
			CanReachTarget g_bTemp
			
			if ( g_bTemp==FALSE )
				Stop
				gosub BaseClearTarget
			endif

		endif
	endif


	GetRandomInt 0, 100, g_nRandom

	if ( g_nRandom > 3 )
		Exit FALSE
	endif

	; small pct chance we'll taunt him when we hit an obstacle....
;;	Taunt BaseGoGetHim
	
	Exit


;------------------------------------------
:BaseAlert
;
;	p0	- Handle of AI who sent the alert
;	p1	- Handle of that AI's target
;------------------------------------------

	
	GetParam 1, g_hObject

	if ( g_hObject==g_hMyObject )
		; Someone yelped about us attacking them!
		exit FALSE
	endif
	
	IsFriend g_hObject, g_bTemp

	if ( g_bTemp==TRUE )
		; We don't answer the call to attack our friends..
		exit FALSE
	endif

	if ( g_hTarget==NULL )
		g_hTarget = g_hObject

		g_bFaceTarget = TRUE
		gosub BaseSetupTarget

		GetRandomFloat 0.2, 0.5, g_nRandom
		Wait BASE_WAIT_NBR, g_nRandom, BaseGoGetHim
	else
		if ( g_hAttacker!=NULL )
			BreakObjectLink g_hAttacker
		endif
		g_hAttacker = g_hObject
		gosub BaseSetupAttacker
		gosub BaseCheckAttacker
	endif


	exit TRUE

;------------------------------------------
:BaseHelp
;
;	If we're not busy, and we feel like it, 
;	go after the target...
;
;	p0 - hPoorSlob
;	p1 - hBadGuy
;
;------------------------------------------

	GetTarget g_hObject
	if ( g_hObject!=NULL )
		Exit
	endif

	GetParam 0, g_hObject
	GetParam 1, g_hObject2

	IsFriend g_hObject, g_bTemp

	if ( g_bTemp==FALSE )
		; Not a friend aye?  Screw him!
		Exit
	endif

	IsFriend g_hObject2, g_bTemp

	if ( g_bTemp==TRUE )
		; He's complaining about a friend of mine.
		Exit
	endif

	; OK, now decide if we SHOULD go after him...

	CanReachObject g_hObject2, g_bTemp
	
	if ( g_bTemp==FALSE )
		; Don't have a way to get to him.  Nevermind...
		Exit
	Endif

	g_bFighting = TRUE
	g_hTarget = g_hObject2
	gosub BaseSetFaceTarget
	gosub BaseSetupTarget
	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseOnProjectile
;
;	p0	- hProjectile
;	p1	- hLaunchedFrom
;	p2	- dist
;
;
;
;------------------------------------------

	GetParam 0, g_hObject
	GetParam 1, g_nTemp
	if ( g_hObject==g_nTemp )
	;
	; Don't take these seriously...
	;
		Exit
	endif

	if ( g_hTarget!=NULL )
		Exit
	endif

	if ( g_hAttacker!=NULL )
		BreakObjectLink g_hAttacker
	endif
	
	GetParam 1, g_hAttacker

	gosub BaseSetupAttacker
	gosub BaseCheckAttacker


	Exit

;------------------------------------------
:ChaseStop
;------------------------------------------
	Wait CHASE_TARGET_WAIT, 0, DoNothing

	Exit

;------------------------------------------
:BaseChaseTargetTick
;
;	A little heartbeat to make sure we 
;	never get stuck when we have a target
;
;------------------------------------------

	Wait CHASE_TARGET_WAIT, 1.0, BaseChaseTargetTick

	if ( g_hTarget==NULL )
		;
		; No target?  No one to go after...
		;
		Exit
	endif

	GetStat g_hMyObject, IsIdle, g_bTemp

	if ( g_bTemp==FALSE )
		;
		; Only do this if we're idle...
		;
		Exit
	endif

	CanReachTarget g_bTemp

	if ( g_bTemp==FALSE )
		if ( g_targetOutOfReachStart==0 )
			GetTime g_targetOutOfReachStart
			Exit
		else
			GetTime g_nTemp
			Sub g_nTemp, g_targetOutOfReachStart

			if ( g_nTemp < BORED_WITH_TARGET_TIME )
				Exit
			endif

			gosub BaseClearTarget
			gosub BaseWanderForceStartUp
		endif
	endif

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:BaseSetupTarget
;
;	Sets up all the stuff for a new target
;
;------------------------------------------

	if ( g_hTarget==NULL )
		DebugOut Script ASSERT!!!!! [BaseSetupTarget]
		DebugOut Script ASSERT!!!!! [BaseSetupTarget]
		DebugOut Script ASSERT!!!!! [BaseSetupTarget]
		DebugOut Script ASSERT!!!!! [BaseSetupTarget]
		Exit
	endif

	; Once we've had a target, we can start wandering...

	g_nStuckTime = 0
	g_targetOutOfReachStart = 0

	gosub DisableWandering

	Target g_hTarget, g_bFaceTarget

	Exit

;------------------------------------------
:BaseClearTarget
;
;	Sets up all the stuff for a new target
;
;------------------------------------------

	g_nStuckTime = 0
	g_targetOutOfReachStart = 0
	g_hTarget = NULL
	Target NULL
	gosub BaseWanderStart
;;;	gosub BaseWanderGo
;;;	gosub EnableWandering

	Exit


;------------------------------------------
:BaseRunAwayTick
;------------------------------------------
	gosub BaseRunAwayTick, 1

	if ( g_bRunningAway==TRUE )
		if ( g_hTarget!=NULL )
			ShouldRunAway g_hTarget, g_bTemp
			if ( g_bTemp==FALSE )
				g_hObject = g_hTarget
				gosub BaseRunCancel
				g_hTarget = g_hObject
				gosub BaseSetFaceTarget
				gosub BaseSetupTarget
				gosub BaseGoGetHim
			EndIf
		EndIf
	EndIf

	Exit

;------------------------------------------
:BaseTargetOutOfRange
;------------------------------------------

	if ( g_bAttackPerformed==TRUE )
		Exit
	EndIf

	GetVelocity g_hTarget, g_velX, g_velY, g_velZ

	if ( g_velX==0 )
		if ( g_velZ==0 )
			Exit
		Endif
	Endif

	SetStat g_hMyObject, RunVel, g_runVel
	SetStat g_hMyObject, WalkVel, g_walkVel

	gosub BaseGoGetHim

	Exit

;------------------------------------------
:InitBase
;
;	Main intialization code.
;
;	This should be called by the actual
;	script file..
;------------------------------------------

	GetMyHandle g_hMyObject
	GetClassName g_hMyObject, g_sMyClassName

;
; Setup our event handlers...
;
	OnFoundPlayer				BaseFoundPlayer
	OnLostTarget				BaseLostTarget
;;;	OnAttackReady				BaseAttackReady
	OnStuck						BaseStuck
	OnStuckDone					BaseStuckDone
	OnDamageDone				BaseDamageDone
	OnDamage					BaseDamage
	OnCongestion				BaseCongestion
	OnPathClear					BasePathClear
	OnTargetDead				BaseTargetDead
	OnObstacle					BaseObstacle
	OnAlert						BaseAlert
	OnHelp						BaseHelp
	OnProjectile				BaseOnProjectile, 200
	OnObjectLinkBroken			BaseObjectLinkBroken
	AddModelKey rAttack, BaseAttackPerformed
	AddModelKey lAttack, BaseAttackPerformed

	GetStat g_hMyObject, CanHeadTurn, g_bCanHeadTurn
	GetStat g_hMyObject, CanBlendAnim, g_bCanBlendAnim
	GetStat g_hMyObject, StrafeAttackPct, g_nStrafeAttackPct

	if (g_bCanBlendAnim==TRUE)
		OnTargetOutOfRange			BaseTargetOutOfRange
	Endif

	; Setup our chase target timer....
;;;;;;;;	Wait CHASE_TARGET_WAIT, 1.0, BaseChaseTargetTick

;
;	See if we already have a target (this would normally happen if
;	the ai were running another script and then decided to start running 
;	this one...
;
	GetTarget g_hTarget

	if ( g_hTarget!=NULL )
		gosub BaseGoGetHim
	endif

	gosub BaseWanderInit

	gosub AggressiveStart
	gosub BaseDoorInit
	gosub SpeedThrottleInit
	gosub SpeedThrottleStart
	gosub BaseRunInit

;;	TraceOn
;;	TraceRoutinesOn

	Exit
