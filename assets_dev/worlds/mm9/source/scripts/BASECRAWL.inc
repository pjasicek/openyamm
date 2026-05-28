;--------------------------------------------------------
;	BaseCrawl.inc
;	Jeff Leggett
;	10/03/2001
;
;	Script for our 4-legged friends.....
;
;	No strafe attacks
;	No dodging
;	Just run up and attack....
;	
;--------------------------------------------------------

#include AICommon.inc
#include baseevade.inc
#include basewander.inc
#include SpeedThrottle.inc
#include BaseRun.inc
#include BaseDoor.inc

#number				AWARE_CHANCE = 40

#number				AGGRESSIVE_TICK = 0.2
#number				BACKOFF_TICK = 0.2
#number				ATTACK_TICK = 0.01

#number				MIN_CHECK_REACH_TIME = 0.4
#number				MIN_CHECK_REACH_TIME2 = 0.1

#number				MIN_RUN_AWAY_AGAIN_TIME = 30

;
; Max time to keep chasing a target if we haven't attacked them nor have we
; been attacked.....
;
#number				MAX_CHASE_TIME = 30


#number				g_runToRange = 0
#number				g_runAfterRange = 0
#number				g_bAggressive = 0

#number				g_strafeDirX
#number				g_strafeDirY
#number				g_strafeDirZ

#number				g_attackStrafeAngle = 45

#number				g_nLastCanReachCheck = 0
#number				g_bCanReach = 1

#number				g_lastDamageTime = 0

#hobject			g_hLastTarget = 0

#number				g_nTime = 0

#number				g_bRotateFollowTarget = 1

#number				g_nTargetDist = 0
#number				g_nTimeToTarget = 0

#hobject			g_hObstacle

#number				g_bFirstPlayerTime = 0



;--------------------------------------------------------
:CanReachTarget
;
;	Set's g_bCanReach to TRUE or FALSE
;	
;--------------------------------------------------------

	GetTime g_nLastCanReachCheck
	CanReachTarget g_bCanReach

	exit

;--------------------------------------------------------
:BaseCrawlGetHim
;
;	
;
;--------------------------------------------------------

	OnObstacle AggressiveObstacle

	if ( g_hTarget==NULL )
		Exit
	Endif

	RunTo g_hTarget, g_runToRange, BaseCrawlArrival

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
:BaseCrawlArrival
;--------------------------------------------------------

	if ( g_bAggressive==TRUE )
		gosub AggressiveTick
	endif

	Exit TRUE

;--------------------------------------------------------
:AggressiveStart
;--------------------------------------------------------

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AggressiveTick
	g_bAggressive = TRUE

	gosub SpeedThrottleStart

	OnObstacle AggressiveObstacle


	Exit

;--------------------------------------------------------
:AggressiveStop
;--------------------------------------------------------

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, DoNothing

	g_bAggressive = FALSE

	OnObstacle
		
	Exit

;--------------------------------------------------------
:ShouldRunAfterNewTarget
;--------------------------------------------------------

	gosub ShouldRunAway
;;;;	ShouldRunAway g_hObject, g_bTemp

	if ( g_bTemp==TRUE )
		g_bTemp = FALSE
	else
		g_bTemp = TRUE
	endif

	Exit

;--------------------------------------------------------
:ShouldRunAway
;
;	Set g_hObject to the object you're asking about
;	g_bTemp will be set to TRUE or FALSE
;
;--------------------------------------------------------
	
	g_bTemp	= FALSE
	if ( g_hObject==NULL )
		exit
	endif
;
;	See if we should hold our ground for awhile...
;
	IsFear g_nTemp
	if ( g_nTemp==FALSE )
		if ( g_nLastRunawayTime!=0 )
			GetTime g_nTemp
			Sub g_nTemp, g_nLastRunawayTime

			if ( g_nTemp < MIN_RUN_AWAY_AGAIN_TIME )
				Exit
			Endif
		endif
	endif

	ShouldRunAway g_hObject, g_bTemp

	exit

;--------------------------------------------------------
:BaseRunCancel
;--------------------------------------------------------
	gosub BaseRunCancel,1

	OnProjectile				OnProjectile, 200
	OnFoundTarget				OnFoundTarget
	OnHelp						OnHelp
	OnAlert						OnAlert
	OnLostTarget				OnLostTarget

	if ( g_hTarget!=NULL )
		gosub ClearTarget
	Endif

	Exit


;--------------------------------------------------------
:BaseRunAway
;--------------------------------------------------------

	Stop
	gosub AggressiveStop
	gosub DisableWandering
	gosub SpeedThrottleStop

	OnProjectile
	OnFoundPlayer
	OnTargetOutOfRange
	OnHelp
	OnAlert

	gosub BaseRunAway, 1

	Exit

;--------------------------------------------------------
:ShouldAttack
;
;	Sets g_bTemp to TRUE or FALSE
;--------------------------------------------------------

	if ( g_hTarget==NULL )
		g_bTemp = FALSE
		Exit
	Endif

	IsClearShot g_hTarget, g_bTemp, g_hObstacle

	exit

;--------------------------------------------------------
:AggressiveInRange
;
;	They're within melee attack range....
;	
;--------------------------------------------------------
	
	g_bCanReach = TRUE

	CanAttack g_bTemp

	if ( g_bTemp==TRUE )
		gosub ShouldAttack
	Endif

	if ( g_bTemp==FALSE )
		
		if ( g_hObstacle!=NULL )
			
			IsClass g_hObject,Actor,g_btemp

			if ( g_bTemp!=TRUE )
				IsFriend g_hObstacle, g_bTemp

				if ( g_bTemp==FALSE )
		;
		;			If not a friend, then let's just set him up as our new target!
		;		
					g_hTarget	= g_hObstacle
					gosub SetupTarget
					Exit
				Endif

				IsClass g_hObstacle,Actor,g_bTemp

				if ( g_bTemp==TRUE )
					gosub AggressiveOutOfRange
					Exit
				Endif
			Endif

		Endif

		g_nTemp = g_attackRange * 0.75

		if ( g_nDist < g_nTemp )

			gosub IsTargetMoving

			if ( g_bTemp==FALSE )
				Stop
			endif
		Endif
	else
		gosub DoAttack
	endif

	exit


;--------------------------------------------------------
:GetTimeToTarget
;
;	returns in g_nTimeToTarget
;--------------------------------------------------------
	g_nTargetDist = 0

	if ( g_hTarget==NULL )
		exit
	Endif

	AIGetDistance g_hTarget, g_nTargetDist

	g_nTimeToTarget = g_nTargetDist / g_runVel
	
	exit

;--------------------------------------------------------
:ShouldRunAfter
;
;	See if they are far enough away that by the time
;	we get to them, we'll be ready to fight....
;
;--------------------------------------------------------
	g_bTemp = FALSE

	if ( g_bDoorOpening==TRUE )
		;CPRINT dooropening.. Not running after!!
		exit
	endif

	CanAttack g_bTemp

	if ( g_bTemp==TRUE )
		exit
	endif

	gosub GetTimeToTarget

	GetStat g_hMyObject,RecoveryTimeLeft,g_nTemp

	if ( g_nTemp < g_nTimeToTarget )
		g_bTemp = TRUE
	endif

	exit

;--------------------------------------------------------
:AggressiveOutOfRange
;
;	They're beyond our attack range.  See if they are out of reach.  If so,
;	just stop...
;	Otherwise, try to go after him....
;
;--------------------------------------------------------

	GetStat g_hTarget,IsFlying,g_bTemp

	if ( g_bCanReach==FALSE )
		gosub CanReachTarget
	endif

	if ( g_bCanReach==TRUE )
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
			gosub CanReachTarget
			if ( g_bCanReach==FALSE	)
				Stop
			endif
		Endif
	Endif

	if ( g_bCanReach==TRUE )
		gosub ShouldRunAfter
		if ( g_bTemp==TRUE )
			gosub BaseCrawlGetHim
		else
		;;	Stop
		endif
	endif

	exit

;--------------------------------------------------------
:GiveUpOnTarget
;--------------------------------------------------------
	gosub ClearTarget

	Exit

;--------------------------------------------------------
:AggressiveTick
;
;	See's if we are within range to attack and such...
;
;--------------------------------------------------------

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AggressiveTick

	GetTime g_nTime
	
	g_nTemp = g_nLastAttackTime + MAX_CHASE_TIME

	if ( g_nTime > g_nTemp )
		; Time to give up on this target!
		gosub GiveUpOnTarget
		Exit
	endif

	if ( g_hTarget==NULL )
		Exit
	Endif

	g_hObject = g_hTarget

	gosub ShouldRunAway

	if ( g_bTemp==TRUE )
		gosub BaseRunAway
		Exit
	Endif

;
;	if we are within attack range do our attack...
;
	AIGetDistance g_hTarget, g_nTargetDist

	if ( g_nTargetDist < g_attackRange )
		gosub AggressiveInRange
	else
		gosub AggressiveOutOfRange
	endif

	Exit



;--------------------------------------------------------
:AttackArrival
;--------------------------------------------------------

	Exit TRUE

;--------------------------------------------------------
:TargetMoving
;
;	Run after him....
;
;--------------------------------------------------------

	AIGetDistance g_hTarget, g_nDist

	if ( g_nDist > g_runAfterRange )
		RunTo g_hTarget, g_runToRange, AttackArrival
	Endif

	Exit

;--------------------------------------------------------
:TargetStill
;--------------------------------------------------------

	AIGetDistance g_hTarget, g_nDist

	IsMoving g_bTemp

	if ( g_bTemp==TRUE )
		if ( g_nDist < g_attackRange )
			if ( g_bTemp==TRUE )
				Stop
			Endif
		Endif
	else
		if ( g_nDist > g_attackRange )
			RunTo g_hTarget, g_runToRange, AttackArrival
		Endif
	Endif
	
	Exit


;--------------------------------------------------------
:AttackTick
;
;	Keep us near the target if they're moving....
;
;--------------------------------------------------------

	IsAttacking g_bTemp

	if ( g_bTemp==FALSE )
		gosub AttackDone
		exit
	Endif

	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AttackTick

	if ( g_hTarget==NULL )
		Exit
	Endif

	gosub IsTargetMoving
	
	if ( g_bTemp==TRUE )
		gosub TargetMoving
	else
		gosub TargetStill
	endif	

	Exit

;--------------------------------------------------------
:AttackDoneCallback
;
;	Just exit TRUE.  This will cause us NOT to stop..
;
;--------------------------------------------------------

	if ( g_hTarget==NULL )
		Stop
	Endif

	Exit TRUE

;--------------------------------------------------------
:AttackObstacle
;
;	p0 - hObstacle
;--------------------------------------------------------

	GetParam 0, g_hObject

	if ( g_hObject==g_hTarget )
		Stop
		exit TRUE
	endif
	
	exit FALSE

;--------------------------------------------------------
:AttackTargetMoved
;--------------------------------------------------------
	gosub IsTargetMoving

	if ( g_bTemp==FALSE )
		Exit
	Endif

	if ( g_bResurrecting==TRUE )
		Exit
	Endif

	RunTo g_hTarget, g_runToRange, AttackArrival

	Exit

;--------------------------------------------------------
:PreAttack
;--------------------------------------------------------
	gosub AggressiveStop

	GetTime g_nLastAttackTime

	; Make sure we face our target during the attack anim...
	FaceObject g_hTarget, 360
	Target g_hTarget, TRUE

	OnObstacle AttackObstacle

	OnTargetBeyondDist g_runAfterRange, AttackTargetMoved


	Exit	

;--------------------------------------------------------
:MeleeAttack
;--------------------------------------------------------

	g_bAttackPerformed	= FALSE
	Wait AGGRESSIVE_WAIT, AGGRESSIVE_TICK, AttackTick
	Attack AttackDoneCallback

	Exit

;--------------------------------------------------------
:PostAttack
;
;	virtual function only...
;--------------------------------------------------------
	Exit

;--------------------------------------------------------
:DoAttack
;--------------------------------------------------------

	if ( g_hTarget==NULL )
		DebugOut (DoAttack) ASSERT(g_hTarget!=NULL)
		Stop
		Exit
	Endif
	

	gosub PreAttack
	gosub MeleeAttack
	gosub PostAttack


	Exit

;--------------------------------------------------------
:AttackTickCancel
;--------------------------------------------------------
	Wait AGGRESSIVE_WAIT, 0, DoNothing
	exit

;--------------------------------------------------------
:AttackDone
;
;--------------------------------------------------------

;
;	Cancel our attack tick...
;

	gosub AttackTickCancel

	OnTargetBeyondDist 0

	SetStat g_hMyObject,RunVel,g_runVel

	gosub IsTargetMoving

	if ( g_bTemp==FALSE )
		Stop
	Endif

	if ( g_hTarget!=NULL )
		IsFriend g_hTarget,g_bTemp
		if ( g_bTemp==TRUE )
			Stop
			gosub ClearTarget
			Exit TRUE
		Endif
	Endif

	gosub AggressiveStart

	Exit TRUE


;--------------------------------------------------------
:AwareDone
;--------------------------------------------------------

	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:SetupTarget
;--------------------------------------------------------

	gosub BaseRunCowerStop
	gosub DisableWandering

	g_hAttacker = NULL

	Target g_hTarget, g_bRotateFollowTarget

	gosub AlertStart

	GetTime g_nLastAttackTime

;
;	Once we've seen the player, double our vision and hearing
;	distances.  Make sure we see them a little better once we've
;	targeted them
;	
	IsPlayer g_hTarget,g_bTemp

	if ( g_bTemp==TRUE )
		if ( g_bFirstPlayerTime==FALSE )
			g_bFirstPlayerTime	= TRUE
			GetStat g_hMyObject,VisibleRange,g_nTemp
			g_nTemp	= g_nTemp * 2
			SetStat g_hMyObject,VisibleRange,g_nTemp
			GetStat g_hMyObject,HearingRange,g_nTemp
			g_nTemp	= g_nTemp * 2
			SetStat g_hMyObject,HearingRange,g_nTemp
		Endif
	Endif

	Exit

;--------------------------------------------------------
:OnFoundTarget
;
;	p0	- hTarget
;
;--------------------------------------------------------

	if ( g_bResurrecting==TRUE )
		Exit
	Endif

	GetParam 0, g_hObject

	gosub ShouldRunAfterNewTarget

	if ( g_bTemp==FALSE )
		g_hTarget	= g_hObject
		target g_hTarget
		gosub BaseRunAway
		Exit
	Endif

	g_hTarget	= g_hObject

	gosub SetupTarget
	gosub AggressiveStop

	GetRandomInt 0, 100, g_nRandom

	if ( g_nRandom < AWARE_CHANCE )
		Taunt AwareDone
	else
		gosub AggressiveStart
	endif

	Exit

;--------------------------------------------------------
:OnDamage
;
;	p0 - hDamager
;
;--------------------------------------------------------

	GetParam 0, g_hAttacker

	if ( g_hAttacker==g_hTarget )
		GetTime g_lastDamageTime
		Exit
	endif

	gosub SetupAttacker

	Exit

;--------------------------------------------------------
:OnDamageDone
;--------------------------------------------------------

	if ( g_hAttacker==NULL )
		Exit FALSE
	endif

	gosub NewTargetCheck

	Exit

;--------------------------------------------------------
:ClearTarget
;--------------------------------------------------------

	if ( g_hTarget==NULL )
		Exit
	Endif
;
;	Don't need speed throttling when we're not attacking anyone..
;
	g_hLastTarget = g_hTarget
	g_hTarget = NULL

	gosub BaseRunCancel
	gosub SpeedThrottleStop
	gosub AggressiveStop
	gosub AlertStop

	Target NULL
	Stop

	gosub EnableWandering

	exit

;--------------------------------------------------------
:OnLostTarget
;--------------------------------------------------------

	gosub ClearTarget

	Exit

;--------------------------------------------------------
:KilledTargetTaunt
;--------------------------------------------------------
	Taunt

	Exit

;--------------------------------------------------------
:OnTargetDead
;
;	p0 - hKiller
;
;--------------------------------------------------------

;
;	To be safe, just clear this out as well.
;
	g_hAttacker = NULL

	gosub ClearTarget

	GetParam 0, g_hObject

	if ( g_hObject==g_hMyObject )
		Stop
		wait TAUNT_WAIT,0.5,KilledTargetTaunt
	Endif

	Exit

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

	if ( g_hAttacker==g_hTarget )
		exit
	endif

	IsActor g_hAttacker, g_bTemp

	if ( g_bTemp==FALSE )
		exit
	endif

	IsFriend g_hAttacker, g_bTemp

	if ( g_bTemp==TRUE )
		g_bTemp = FALSE
		exit
	else
		g_bTemp = TRUE
	endif

	GetStat g_hAttacker,IsDead,g_bTemp

	if ( g_bTemp==TRUE )
		g_bTemp = FALSE
		exit
	endif

	g_bTemp = TRUE

	exit

;--------------------------------------------------------
:NewTargetCheck
;	
;	Fill in g_hAttacker with the potential new target,
;	and this function takes care of the rest....
;
;--------------------------------------------------------

	g_nTemp = g_nLastAttackTime + MAX_CHASE_TIME

	if ( m_hTarget!=NULL )
		GetTime g_nTime
		if ( g_nTime > g_nTemp )
			; Time to give up on this target!
			gosub GiveUpOnTarget
		endif
	Endif

	if ( g_bResurrecting==TRUE )
		goto NewTargetCheckFailed
	Endif

	if ( g_hAttacker==NULL )
		goto NewTargetCheckFailed
	endif

	GetTarget g_hTarget

	gosub IsAttackerValidTarget

	if ( g_bTemp==FALSE	)
		goto NewTargetCheckFailed
	endif

	if ( g_bRunningAway==TRUE )
		goto NewTargetCheckFailed
	Endif

	if ( g_bCowering==TRUE )
		goto NewTargetCheckFailed
	Endif

;
;	if we don't currently have a target, then he's our man....
;
	if ( g_hTarget==NULL )
		g_hTarget = g_hAttacker
		g_hAttacker = NULL
		gosub SetupTarget
		Target g_hTarget, TRUE
		gosub AggressiveStart
		exit TRUE
	Endif

;
;	We have a target, decide if we should switch.......
;

	IsTargetInRange g_bInAttackRange

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
		g_nTemp = g_nTemp / 2
	else
;
;		increase odds if attacker is less than 1/2 the distance to
;		current target...
;
		g_nDist1 = g_nDist1 * 2

		if ( g_nDist2 < g_nDist1 )
			g_nTemp = g_nTemp * 1.15
		endif
	endif

	GetRandomInt 0, 100, g_nRandom
	if ( g_nRandom < g_nTemp )
		; 
		; Okay, we decided to switch our current target to the 
		; attacker!
		;
		g_hTarget = g_hAttacker
		g_hAttacker = NULL
		gosub SetupTarget
		gosub AggressiveStart
	endif

	exit TRUE

:NewTargetCheckFailed
;
;	Break the link to it if needed...
;
	gosub ClearAttacker

	Exit FALSE

;--------------------------------------------------------
:OnAlert
;
;	p0 - The alerter
;	p1 - who he's alerting about....
;
;--------------------------------------------------------
	GetParam 0, g_hObject
	
	IsFriend g_hObject,g_bTemp
	if ( g_bTemp==FALSE )
		Exit
	Endif

	GetParam 1, g_hAttacker
	gosub NewTargetCheck

	Exit

;--------------------------------------------------------
:OnProjectile
;
;	p0	- hProjectile
;	p1	- hLaunchedFrom
;	p2	- dist
;
;--------------------------------------------------------

	GetParam 0, g_nTemp
	GetParam 1, g_hObject

 	if ( g_hObject==g_nTemp )
;
;		Don't take these seriously...
;
		Exit
	endif

	gosub NewTargetCheck

	exit

;--------------------------------------------------------
:AttackPerformed
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
;	Do all things necessary to enable
;	Wandering...
;
;------------------------------------------

	bWanderDisabled	= FALSE
	gosub BaseWanderStart

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

	GetParam 1, g_hAttacker
	gosub NewTargetCheck

	Exit

;--------------------------------------------------------
:ResurrectMe
;--------------------------------------------------------
	if ( g_bRunningAway==TRUE )
		Exit
	Endif

	gosub ResurrectMe,1

	Exit

;--------------------------------------------------------
:DelayResurrection
;--------------------------------------------------------
	Wait RESURRECT_WAIT,0.1,DoResurrection
	exit

;--------------------------------------------------------
:OnResurrect
;--------------------------------------------------------
	gosub AggressiveStop
	gosub BaseRunCancel
	gosub OnResurrect,1

	exit

;--------------------------------------------------------
:ResurrectDone
;--------------------------------------------------------

	gosub ResurrectDone,1

	g_hTarget = g_hDeathTarget

	if (g_hTarget!=NULL)
		gosub SetupTarget
		gosub AggressiveStart
	endif

	Exit

;--------------------------------------------------------
:DoResurrection
;--------------------------------------------------------

	if ( g_hResurrect==NULL )
		;cprint NO ONE TO RESURRECT??
		Exit
	Endif

	IsDead g_hResurrect,g_bTemp

	if ( g_bTemp==FALSE )
		g_hResurrect = NULL
		Exit
	Endif

	if ( g_hTarget!=NULL )
		Target g_hTarget, FALSE
	Endif

	IsAttacking g_bTemp

	if ( g_bTemp==TRUE )
		gosub DelayResurrection
		exit
	endif

	GetStat g_hMyObject,IsWincing,g_bTemp

	if ( g_bTemp==TRUE )
		gosub DelayResurrection
		Exit
	Endif

	gosub DoResurrection,1
	gosub AggressiveStop
	gosub DisableWandering

	Exit

;--------------------------------------------------------
:DoResurrectionDone
;--------------------------------------------------------
	gosub DoResurrectionDone,1

	gosub BaseRunCancel

	GetTarget g_hTarget

	if ( g_hTarget!=NULL )
		gosub AggressiveStart
		Target g_hTarget, TRUE
	else
		Target NULL
		Stop
		gosub EnableWandering
	Endif
	

	Exit
;--------------------------------------------------------
:InitCallbacks
;--------------------------------------------------------

	OnFoundTarget				OnFoundTarget
	OnLostTarget				OnLostTarget
	OnDamageDone				OnDamageDone
	OnDamage					OnDamage
	OnTargetDead				OnTargetDead
	OnAlert						OnAlert
	OnProjectile				OnProjectile, 200
	OnHelp						OnHelp

	gosub InitCommon

	Exit

;--------------------------------------------------------
:OnDeath
;--------------------------------------------------------
	gosub OnDeath,1

	g_hObject = g_hTarget
	gosub BaseRunCancel
	gosub ClearTarget
	gosub DisableWandering
	g_hTarget = g_hObject
	Target g_hTarget,TRUE

	Exit

;--------------------------------------------------------
:OnGetPlayer
;--------------------------------------------------------
	gosub ClearTarget
	GetPlayerHandle g_hTarget
	gosub SetupTarget
	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:OnGetMe
;--------------------------------------------------------
	gosub ClearTarget
	GetParam 0,g_hTarget
	gosub SetupTarget
	gosub AggressiveStart

	Exit

;--------------------------------------------------------
:BaseCrawlInit
;--------------------------------------------------------

	GetMyHandle g_hMyObject

	gosub InitCallbacks

	AddModelKey rAttack, AttackPerformed
	AddModelKey lAttack, AttackPerformed
	AddModelKey Bite, AttackPerformed
	AddModelKey rKick, AttackPerformed
	AddModelKey lKick, AttackPerformed
	AddTrigger GetPlayer,OnGetPlayer

	GetStat g_hMyObject, RunVel, g_runVel
	GetStat g_hMyObject, WalkVel, g_walkVel
	GetStat g_hMyObject, AttackRange, g_attackRange

	g_runToRange	= g_attackRange * 0.95
	g_runAfterRange	= g_attackRange * 0.70

	gosub BaseWanderInit
	gosub BaseRunInit
	gosub BaseDoorInit	; make sure we can open doors....

	GetTarget g_hTarget

	if ( g_hTarget!=NULL )
		gosub SetupTarget
		gosub AggressiveStart
	Endif

	Exit

