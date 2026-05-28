;--------------------------------------------------------
;	BaseFly.Inc
;	Jeff Leggett
;	09/27/2001
;
;
;	Basic implementation of flying creatures..
;		
;--------------------------------------------------------

#include AICommon.inc
#include baseevade.inc
#include basewander.inc
#include flags.inc


#number				AGGRESSIVE_TICK = 0.2
#number				BACKOFF_TICK = 0.2
#number				ATTACK_TICK = 0.01

#number				MAX_ATTACK_FLY_VEL = 200
#number				MAX_CHASE_TIME = 30

#number				g_attackRange = 0
#number				g_runToRange = 0
#number				g_bAggressive = 0

#number				g_strafeDirX
#number				g_strafeDirY
#number				g_strafeDirZ

#number				g_flyVel = 100

#number				g_attackStrafeAngle = 45

#number				g_backOffYVal=0.6
#number				g_backOffTime=1.0

#number				g_bSwooping = 0
#number				g_bBackingOff = 0

#number				g_nTargetDist = 0
#number				g_nTimeToTarget = 0

#number				g_nTime = 0

;--------------------------------------------------------
:AlertStart
;--------------------------------------------------------
	gosub AlertTick
	Exit

;--------------------------------------------------------
:AlertTick
;--------------------------------------------------------
	Wait ALERT_WAIT, g_nRandom, AlertTick

	if ( g_hTarget==NULL )
		Exit
	Endif

	SendAlert g_hTarget

	Exit

;--------------------------------------------------------
:AlertStop
;--------------------------------------------------------
	Wait ALERT_WAIT, 0, DoNothing
	Exit


;--------------------------------------------------------
:GetTimeToTarget
;
;	returns in g_nTimeToTarget
;--------------------------------------------------------

	g_nTargetDist = 0
	g_nTimeToTarget	= 0

	if ( g_hTarget==NULL )
		exit
	Endif

	AIGetDistance g_hTarget, g_nTargetDist

	g_nTimeToTarget = g_nTargetDist / g_flyVel
	
	exit


;--------------------------------------------------------
:BaseFlyGetHim
;
;	
;
;--------------------------------------------------------

	OnObstacle AggressiveObstacle

	if ( g_hTarget==NULL )
		Exit
	Endif

	RunTo g_hTarget, g_runToRange, BaseFlyArrival

	Exit

;--------------------------------------------------------
:AggressiveObstacle
;--------------------------------------------------------

	GetParam 0,g_hObject

	if ( g_hObject==g_hTarget )
		Debugout Ran into target!  stopping....
		Stop
		Exit TRUE
	endif

	Exit FALSE

;--------------------------------------------------------
:BaseFlyArrival
;--------------------------------------------------------

	if ( g_bAggressive==TRUE )
		gosub AggressiveTick
	endif

	Exit TRUE

;--------------------------------------------------------
:AggressiveStart
;--------------------------------------------------------

	SetStat g_hMyObject, flyVel, g_flyVel

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AggressiveTick
	g_bAggressive = TRUE


	Exit

;--------------------------------------------------------
:AggressiveStop
;--------------------------------------------------------

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, DoNothing

	g_bAggressive = FALSE

	OnObstacle
		
	Exit


;--------------------------------------------------------
:AggressiveTick
;
;	See's if we are within range to attack and such...
;
;--------------------------------------------------------

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AggressiveTick

	if ( g_hTarget==NULL )
		Exit
	Endif

	GetTime g_nTime
	
	g_nTemp = g_nLastAttackTime + MAX_CHASE_TIME

	if ( g_nTime > g_nTemp )
		; Time to give up on this target!
		gosub GiveUpOnTarget
		Exit
	endif


;
;	if we are within attack range do our attack...
;

	AIGetDistance g_hTarget, g_nTemp

	if ( g_nTemp < g_attackRange )
		CanAttack g_bTemp
		if ( g_bTemp==FALSE )
			GetTime g_nLastAttackTime
			gosub Backoff
		else
			gosub BaseFlyAttack
			Exit
		endif
	else
		gosub BaseFlyGetHim
	endif

	Exit


;--------------------------------------------------------
:SwoopDone
;--------------------------------------------------------

	g_bSwooping	= FALSE

	Target g_hTarget, TRUE
	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:SwoopIn
;
;	Instead of coming right at target, fly towards him
;	at an angle for a little bit...
;	"Swoop" in for the kill!
;
;--------------------------------------------------------

	gosub BE_GetTargetDir

	g_targetDirY	= 0
	g_bSwooping		= TRUE

	GetRandomInt 30,50, g_nRandom

	GetRandomInt 0,1,g_nTemp

	if (g_nTemp==0)
		Mul g_nRandom, -1
	endif

	Target g_hTarget, FALSE

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, g_nRandom
	FaceDir g_targetDirX, g_targetDirY, g_targetDirZ, 180

	Strafe g_targetDirX, g_targetDirY, g_targetDirZ, TRUE

	Wait AGGRESSIVE_WAIT,1, SwoopDone

	Exit

;--------------------------------------------------------
:BackOffTick
;--------------------------------------------------------

	Wait AGGRESSIVE_WAIT, BACKOFF_TICK, BackOffTick
	gosub DoBackoff

	Exit

;--------------------------------------------------------
:BackoffDone
;--------------------------------------------------------
	SetStat g_hMyObject, flyVel, g_flyVel

	g_bBackingOff = FALSE

	gosub BackoffStop
;;	gosub AggressiveStart

	if ( g_hTarget!=NULL )
		SendAlert g_hTarget
	endif

	gosub SwoopIn

	exit

;--------------------------------------------------------
:DoBackoff
;--------------------------------------------------------

	g_bBackingOff = TRUE

	gosub BE_GetTargetDir

	g_targetDirY	= 0

	FaceDir g_targetDirX, 0, g_targetDirZ, 360
	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, 180

	g_targetDirY	= g_backOffYVal

	if ( g_hTarget!=NULL )
		GetStat g_hTarget,IsFlying,g_bTemp
		if ( g_bTemp==TRUE )
			g_targetDirY	= 0
		endif
	endif

	Strafe g_targetDirX, g_targetDirY, g_targetDirZ, TRUE

	exit

;--------------------------------------------------------
:BackOff
;--------------------------------------------------------

	SetStat g_hMyObject, flyVel, g_flyVel
	
	gosub AggressiveStop

	Wait AGGRESSIVE_WAIT, BACKOFF_TICK, BackOffTick

	gosub DoBackoff

	Wait BASE_EVADE_WAIT, g_backOffTime, BackOffDone

	Target g_hTarget, FALSE


	Exit

;--------------------------------------------------------
:BackoffStop
;--------------------------------------------------------
	Wait AGGRESSIVE_WAIT, 0.1, DoNothing

	Exit

;--------------------------------------------------------
:BaseFlyAttackDone
;
;	Now back off....
;	
;--------------------------------------------------------

	SetStat g_hMyObject,FlyVel,g_flyVel
	SetStat g_hMyObject,RunVel,g_runVel

	if ( g_hTarget==NULL )
		Exit TRUE
	Endif

	gosub BackOff


	Exit TRUE

;--------------------------------------------------------
:AttackArrival
;--------------------------------------------------------

	Exit TRUE

;--------------------------------------------------------
:TargetMoving
;--------------------------------------------------------

	AIGetDistance g_hTarget, g_nTemp

	if ( g_nTemp < g_attackRange )
		gosub AttackStrafe
	else
		RunTo g_hTarget, g_runToRange, AttackArrival
	endif

	Exit

;--------------------------------------------------------
:TargetStill
;--------------------------------------------------------

	gosub AttackStrafe

	Exit

;--------------------------------------------------------
:AttackTick
;
;	Keep us strafing near the target as we go by...
;
;--------------------------------------------------------

	gosub IsTargetMoving

	if ( g_bTemp==FALSE )
		g_nTemp	= g_runVel * 0.8
		SetStat g_hMyObject,RunVel,g_nTemp

		g_nTemp = g_flyVel * 0.8

		if ( g_flyVel > MAX_ATTACK_FLY_VEL )
			g_nTemp = MAX_ATTACK_FLY_VEL
		endif

		SetStat g_hMyObject,FlyVel,g_nTemp
	else
		SetStat g_hMyObject,FlyVel,g_flyVel
	Endif

	if ( g_bAttackPerformed==TRUE )
		Exit
	Endif

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AttackTick

	if ( g_bTemp==TRUE )
		gosub TargetMoving
	else
		gosub TargetStill
	endif

	Exit

;--------------------------------------------------------
:AttackStrafeObstacle
;
;	p0 - hObstacle
;
;	p1-3 - normal
;
;--------------------------------------------------------
	GetParam 0, g_hObject

	if ( g_hObject==g_hTarget )
		; bumping into target... strafing on...
		gosub AttackStrafe
		Exit TRUE
	Endif

	Debugout bumped into something during attack... stopping

	stop

	Exit TRUE

;--------------------------------------------------------
:AttackStrafe
;--------------------------------------------------------
	gosub BE_GetTargetDir

	g_targetDirY = 0

	OnObstacle AttackStrafeObstacle

	FaceDir g_targetDirX, g_targetDirY, g_targetDirZ, 180

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, g_attackStrafeAngle
	Strafe g_targetDirX, 0, g_targetDirZ, TRUE
	Target g_hTarget, TRUE

	Exit

;--------------------------------------------------------
:BaseFlyAttack
;--------------------------------------------------------

	if ( g_hTarget==NULL )
		DebugOut (BaseFlyAttack) ASSERT(g_hTarget!=NULL)
		Stop
		Exit
	Endif

	GetTime g_nLastAttackTime

	gosub AggressiveStop

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AttackTick

	g_bAttackPerformed	= FALSE

	GetRandomInt 0,1,g_nRandom

	if ( g_nRandom==1 )
		g_attackStrafeAngle = 45
	else
		g_attackStrafeAngle = -45
	endif

	gosub AttackStrafe

	Target g_hTarget, TRUE

	Attack BaseFlyAttackDone

	Exit

;--------------------------------------------------------
:TauntDone
;--------------------------------------------------------

	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:SetupTarget
;--------------------------------------------------------
	gosub DisableWandering

	Target g_hTarget, TRUE
	gosub AlertStart

	GetTime g_nLastAttackTime

	Exit

;--------------------------------------------------------
:OnFoundTarget
;
;	p0	- hPlayer
;
;--------------------------------------------------------

	GetParam 0, g_hTarget

	gosub SetupTarget
	gosub AggressiveStop

	Taunt TauntDone

	Exit

;--------------------------------------------------------
:OnDamage
;
;	p0 - hDamager
;
;--------------------------------------------------------
	
	GetParam 0, g_hAttacker

	gosub SetupAttacker

	Exit

;--------------------------------------------------------
:OnDamageDone
;--------------------------------------------------------

	SetStat g_hMyObject,FlyVel,g_flyVel

	if ( g_hAttacker!=NULL )
		GetTarget g_hTarget

		if ( g_hTarget==NULL )
			g_hTarget	= g_hAttacker
			gosub SetupTarget
			gosub AggressiveStart
			Exit TRUE
		Endif

		GetRandomInt 0, 100, g_nRandom

		if ( g_nRandom < 50 )
			g_hTarget	= g_hAttacker
			gosub SetupTarget
			gosub AggressiveStart
			Exit TRUE
		Endif
	Endif

	if ( g_hTarget==NULL )
		gosub ClearTarget
		Exit
	Endif

	CanAttack g_bTemp

	if ( g_bTemp==TRUE )
		gosub AggressiveStart
	else
		gosub Backoff
	endif

	Exit TRUE

;--------------------------------------------------------
:GiveUpOnTarget
;--------------------------------------------------------

	gosub ClearTarget

	Exit

;--------------------------------------------------------
:ClearTarget
;--------------------------------------------------------

	gosub AggressiveStop
	gosub BackoffStop
	gosub AlertStop

	g_hTarget = NULL
	Target NULL
	Stop

	gosub BaseWanderStart

	exit

;--------------------------------------------------------
:OnLostTarget
;--------------------------------------------------------

	gosub ClearTarget

	Exit

;--------------------------------------------------------
:OnTargetDead
;--------------------------------------------------------

	gosub ClearTarget

	Exit

;--------------------------------------------------------
:NewTargetCheck
;	
;	Fill in g_hObject with the potential new target,
;	and this function takes care of the rest....
;
;--------------------------------------------------------

	if ( g_hObject==NULL )
		exit
	endif

	if ( g_hObject==g_hMyObject )
		Exit FALSE
	endif

	IsFriend g_hObject, g_bTemp
	
	if ( g_bTemp==TRUE )
		Exit FALSE
	endif

	GetTime g_nLastAttackTime

	if ( g_hTarget==NULL )
		g_hTarget = g_hObject
		Target g_hTarget, TRUE
		gosub AggressiveStart
		exit TRUE
	Endif

	Exit

;--------------------------------------------------------
:OnAlert
;--------------------------------------------------------
	GetParam 0, g_hObject
	gosub NewTargetCheck

	Exit

;--------------------------------------------------------
:OnProjectile
;--------------------------------------------------------

	GetParam 1, g_hObject
	gosub NewTargetCheck
	

	exit

;--------------------------------------------------------
:FlyAttackPerformed
;--------------------------------------------------------
	g_bAttackPerformed	= TRUE
	Exit FALSE

;------------------------------------------
:DisableWandering
;
;	Do all things necessary to disable
;	Wandering...
;
;------------------------------------------

	gosub BaseWanderStop

	bWanderDisabled	= TRUE

	OnObstacle
	OnStuckDone
	OnStuck

	Exit

;------------------------------------------
:EnableWandering
;
;	Do all things necessary to disable
;	Wandering...
;
;------------------------------------------

	bWanderDisabled	= FALSE
	gosub BaseWanderStart

	Exit

;--------------------------------------------------------
:BaseWanderStartWalking
;
;	Override this so we can slow down our flying speed
;
;--------------------------------------------------------

	SetStat g_hMyObject, FlyVel, g_walkVel
	gosub BaseWanderStartWalking, 1

	Exit

;--------------------------------------------------------
:BaseWanderGo
;--------------------------------------------------------
	gosub BaseWanderGo,1
	SetStat g_hMyObject,CheckForObstacles,FALSE

	if ( nWanderPathCount!=0 )
;;;		SetStat g_hMyObject,AllowRotateY,TRUE
;;;		SetStat g_hMyObject,FaceVelocity,TRUE
	Endif

	Exit


;--------------------------------------------------------
:BaseWanderStop
;--------------------------------------------------------

	SetStat g_hMyObject,CheckForObstacles,TRUE
	SetStat g_hMyObject, FlyVel, g_flyVel
;;;	SetStat g_hMyObject,AllowRotateY,FALSE
;;;	SetStat g_hMyObject,FaceVelocity,FALSE

	gosub BaseWanderStop, 1

	Exit


;--------------------------------------------------------
:OnHelp
;
;	p0 - hPoorSlob
;	p1 - hBadGuy
;--------------------------------------------------------

	if ( g_hTarget!=NULL )
		Exit
	Endif

	GetParam 0, g_hObject

	IsFriend g_hObject, g_bTemp

	if (g_bTemp==FALSE)
		Exit
	Endif

	GetParam 1, g_hObject
	gosub NewTargetCheck

	Exit


;--------------------------------------------------------
:BaseFlyInitCallbacks
;--------------------------------------------------------

	OnFoundTarget				OnFoundTarget
	OnLostTarget				OnLostTarget
	OnDamageDone				OnDamageDone
	OnDamage					OnDamage
	OnTargetDead				OnTargetDead
	OnAlert						OnAlert
	OnProjectile				OnProjectile, 200
	OnHelp						OnHelp

	Exit

;--------------------------------------------------------
:OnGetPlayer
;--------------------------------------------------------
	GetPlayerHandle g_hObject

	if ( g_hObject==g_hTarget )
		Exit
	Endif

	if ( g_hTarget!=NULL )
		gosub ClearTarget
	endif

	g_hTarget	= g_hObject
	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:OnGetMe
;--------------------------------------------------------
	GetParam 0,g_hObject

	if ( g_hObject==g_hTarget )
		Exit
	Endif

	if ( g_hTarget!=NULL )
		gosub ClearTarget
	endif

	g_hTarget	= g_hObject
	gosub AggressiveStart

	Exit


;--------------------------------------------------------
:BaseFlyInit
;--------------------------------------------------------

	GetMyHandle g_hMyObject

	gosub BaseFlyInitCallbacks
	gosub InitCommon

	AddModelKey rAttack, FlyAttackPerformed
	AddModelKey lAttack, FlyAttackPerformed
	AddModelKey Bite, FlyAttackPerformed
	AddModelKey rKick, FlyAttackPerformed
	AddModelKey lKick, FlyAttackPerformed

	GetStat g_hMyObject, RunVel, g_runVel
	GetStat g_hMyObject, WalkVel, g_walkVel
	GetStat g_hMyObject, flyVel, g_flyVel
	GetStat g_hMyObject, AttackRange, g_attackRange

	g_runToRange = g_attackRange * 0.95


	AddTrigger GetPlayer,OnGetPlayer
	AddTrigger GetMe,OnGetMe

	gosub BaseWanderInit

	GetTarget g_hTarget
	if ( g_hTarget!=NULL )
		gosub SetupTarget
	Endif

	Exit
	
