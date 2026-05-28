;----------------------------------------------------------------
;	attack.inc
;	John Machin
;
;		Attack script 
;		Need to setup g_hTarget and call Init Attack to initiate
;----------------------------------------------------------------
#include globals.inc
#include aiglobals.inc


;Setup attack stuff
#number		g_nDist1
#number		g_nDist2
#number		g_lastDamageType
#number		g_nLastDamage
#number		g_bOkAttackType		= 0
#hobject	g_hAttacker

;----------------------------------------------------------------
:InitAttack
;----------------------------------------------------------------
	if( g_hTarget == NULL )
		Exit FALSE
	endif  

	IsAttacking g_bAttacking
	
	if ( g_bAttacking==TRUE )
		Exit TRUE
	endif

	IsTargetInRange g_bInAttackRange

	if ( g_bInAttackRange==TRUE )
		CanAttack g_bCanAttack

		if ( g_bCanAttack==TRUE )
			gosub AttackReady
		endif

		Exit TRUE
	endif

	;if ( g_bFighting==TRUE )
		RunTo g_hTarget
	;else
	;	WalkTo g_hTarget
	;endif
		
	Exit TRUE

;----------------------------------------------------------------
:AttackReady
;
;	We are now in attack range (for our
;	currently selected weapon) and ready
;	to attack.  So let's do it!
;----------------------------------------------------------------

	Set g_bFighting, TRUE

	GetTime g_nLastAttackTime

	Attack

	Exit

;----------------------------------------------------------------
:HandleTargetOutOfRange
;
;	Target moved out of our weapon range.
;	Go after him!
;	
;----------------------------------------------------------------

	CanAttack g_bCanAttack
	IsAttacking g_bAttacking

	;if ( g_bAttacking==TRUE )
		;Wait 0.5, OutOfRangeWait
	;endif

	;if ( g_bCanAttack==TRUE )
		gosub InitAttack
	;else
		;Wait 0.5, OutOfRangeWait
	;endif

	Exit

;----------------------------------------------------------------
:HandleLostTarget
;
;	We've lost the target, so let's go idle.
;----------------------------------------------------------------

	Set g_hTarget, NULL
	Set g_bFighting, FALSE
	Target NULL

	
	SetIdle

	Exit


;----------------------------------------------------------------
:OutOfRangeWait
;
;	We don't want to run after target
;	until it's far enough away or we are
;	ready to attack...
;----------------------------------------------------------------

	if ( g_hTarget==NULL )
		Exit TRUE
	endif

	IsAttacking g_bAttacking

	if ( g_bAttacking==TRUE )
		Wait 0.5, OutOfRangeWait
		Exit TRUE
	endif

	CanAttack g_bCanAttack
	if ( g_bCanAttack==TRUE )
		;gosub BaseMaybeRangeAttack

		IsAttacking g_bAttacking

		if ( g_bAttacking==TRUE )
			exit TRUE
		endif

		gosub InitAttack
		Exit TRUE
	endif

	; randomly play a taunt animation...
	;GetRandomInt 0, 100, g_nRandom

	;if ( g_nRandom < 30 )
	;	if ( g_nRandom < 15 )
	;		Taunt BaseAttackWaitAnimDone
	;	else
	;		Aware BaseAttackWaitAnimDone
	;	endif
	;	Exit TRUE
	;endif

	;AIGetDistance g_hTarget, g_nDist1

	;if ( g_nDist1 > 200 )		; if they are too far away...
	;	WalkTo g_hTarget
	;	Wait 0.5, OutOfRangeWalkingWait
	;	Exit TRUE
	;endif

	; Continue waiting....

	Wait 0.5, OutOfRangeWait

	Exit

;----------------------------------------------------------------
:HandleAttackReady
;
;	We are now in attack range (for our
;	currently selected weapon) and ready
;	to attack.  So let's do it!
;----------------------------------------------------------------


	Set g_bFighting, TRUE

	GetTime g_nLastAttackTime

	Attack

	Exit

;----------------------------------------------------------------
:HandleDamageDone
;
;	We were attacked, now we want to run
;	after whoever attacked us!
;	
;----------------------------------------------------------------

	if ( g_hAttacker==g_hMyObject )
		exit FALSE
	endif

	IsActor g_hAttacker, g_nTemp

	if ( g_nTemp==FALSE )
		; Not an actor, therefore
		; never go after it...
		if ( g_hTarget!=NULL )
			gosub InitAttack
			Exit TRUE
		else
			Exit FALSE
		endif
	endif

	if ( g_hTarget==NULL )
		Set g_hTarget, g_hAttacker
		Set g_bFighting, TRUE
	else
		IsTargetInRange g_bInAttackRange

		if ( g_hAttacker!=NULL )
			if ( g_hAttacker!=g_hTarget )
				GetClassName g_hAttacker, g_sTemp
				if ( g_sTemp!=Player )
					goto SkipTargetSwitch
				endif
				; 70% chance we'll switch to the damager
				Set g_nTemp, 70
				if ( g_bInAttackRange==TRUE )
					; we're already in attack range of our current target
					; so lower chances of switching
					Set g_nTemp, 10
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
					Set g_hTarget, g_hAttacker
				endif
			endif
		endif
	endif

;----------------------------------------------------------------
:SkipTargetSwitch
;----------------------------------------------------------------

	if ( g_hTarget==0 )
		Exit FALSE		; FALSE means have the AI do its default handling of this event.
	endif

	; Go after the Target...

	Target g_hTarget

	gosub InitAttack

	Exit

;------------------------------------------
:OutOfRangeWalkingWait
;
;	Once we start walking after target,
;   we want to start running as soon as
;	we are attack ready...
;
;------------------------------------------

	CanAttack g_bCanAttack
	if ( g_bCanAttack==TRUE )
		;gosub BaseMaybeRangeAttack
		IsAttacking g_bAttacking

		if ( g_bAttacking==TRUE )
			exit TRUE
		endif

		gosub InitAttack
		Exit TRUE
	endif

	Wait 0.5, OutOfRangeWait

	Exit


;----------------------------------------------------------------
:HandleDamage
;
;	p0 = hAttacker
;	p1 = HitPoints
;	p2 = DamageType
;
;----------------------------------------------------------------

	GetParam 0, g_hAttacker		
	GetParam 1, g_nLastDamage
	GetParam 2, g_lastDamageType	

	SendAlert g_hAttacker		
	
	if( g_nLastDamage == 0 )
		gosub HandleDamageDone
	endif

	Exit FALSE	

;------------------------------------------
:HandlePathClear
;------------------------------------------

	if ( g_hTarget!=NULL )
		RunTo g_hTarget, 120, NearTarget
	endif

	Exit TRUE

;------------------------------------------
:NearTarget
;
;	Only walk up to them if the fight hasn't
;	started yet...
;
;------------------------------------------

	if ( g_bFighting!=TRUE )
		WalkTo g_hTarget
	endif

	Exit


	
;----------------------------------------------------------------
:HandleCongestion
;
;	If there is congestion in the way, 
;	start walking
;----------------------------------------------------------------

	if ( g_hTarget!=NULL )
		WalkTo g_hTarget
	endif

	Exit TRUE
	
;------------------------------------------
:HandleTargetDead
;------------------------------------------

	GetParam 0, g_nTemp

	Target NULL
	Set g_hTarget, NULL

	if ( g_nTemp==g_hMyObject )
		;
		;	We killed him!
		;
		; taunt him, and go home....
		Taunt GoHome
	else
		; just go home...
		gosub GoHome 
	endif

	Exit TRUE

;------------------------------------------
:GoHome
;
;	Sends ai back to where it started
;
;	NOTE: if we ge stuck on way back home,
;   we will just stay there...
;------------------------------------------

	; for now, just go back into idle loop...
	SetIdle

;;	Set g_nGoingHome, TRUE
;;	WalkToPos g_homeX, g_homeY, g_homeZ, BaseImHome

	Exit	  	   


