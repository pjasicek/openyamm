;--------------------------------------------------------
;	FlyRange.Inc
;	Jeff Leggett
;	10/22/2001
;
;
;	Implements flying creatures that can shoot....
;
;	Still want to swoop in on target (so they can melee
;	you a little...)
;
;	Randomly shoot once we've backed off....
;		
;--------------------------------------------------------

#include baseFly.inc

#number			MIN_RANGE_ATTACK_INTERVAL = 2
#number			MIN_RANGE_CHECK_TIME = 0.3
#number			MAX_RANGE_CHECK_TIME = 1.3
#number			RANGE_CHECK_WAIT = 15

#number			g_lastRangeCheck = 0
#number			g_lastRangeAttack = 0
#number			g_bCanRangeAttack = 0

#number			g_bSwoopAfterRange = 0

;--------------------------------------------------------
:RangeCheckSetup
;--------------------------------------------------------

	if ( g_hTarget==NULL )
		gosub RangeCheckStop
		Exit
	Endif

	GetRandomFloat MIN_RANGE_CHECK_TIME,MAX_RANGE_CHECK_TIME, g_nRandom
	Wait RANGE_CHECK_WAIT, g_nRandom, RangeCheckTick

	Exit

;--------------------------------------------------------
:RangeCheckStop
;--------------------------------------------------------

	Wait RANGE_CHECK_WAIT, 0, DoNothing

	Exit

;--------------------------------------------------------
:RangeCheckTick
;--------------------------------------------------------

	gosub RangeCheckSetup	
	gosub ShouldRangeAttack

	if ( g_bTemp==TRUE )
		g_bSwoopAfterRange = FALSE
		gosub StartRangeAttack
	endif

	Exit

;--------------------------------------------------------
:CanRangeAttack
;--------------------------------------------------------

	GetTime g_nTemp

	g_nTemp = g_nTemp - g_lastRangeAttack

	if ( g_nTemp < MIN_RANGE_ATTACK_INTERVAL )
		g_bCanRangeAttack = FALSE
		exit
	Endif
	
	CanRangeAttack g_bCanRangeAttack

	Exit

;--------------------------------------------------------
:RangeAttackDone
;--------------------------------------------------------
	gosub RangeCheckSetup
	
	if ( g_bSwoopAfterRange==TRUE )
		gosub SwoopIn
	else
		gosub AggressiveStart
	endif

	Exit

;--------------------------------------------------------
:DoRangeAttack
;--------------------------------------------------------

	GetTime g_nLastAttackTime

	gosub GetTimeToTarget

	if ( g_nTimeToTarget < 1.1 )
		Stop
	endif

	GetTime g_lastRangeAttack
	RangeAttack RangeAttackDone

;
;	Setup our next range attack check...
;
	gosub RangeCheckSetup	

	Exit

;--------------------------------------------------------
:StartRangeAttack
;--------------------------------------------------------

	Target g_hTarget, TRUE

	gosub AggressiveStop
	gosub DoRangeAttack

	exit


;--------------------------------------------------------
:ShouldRangeAttack
;--------------------------------------------------------

	if ( g_bSwooping==TRUE )
		g_bTemp = FALSE
		exit
	endif

	if ( g_bBackingOff==TRUE )
		g_bTemp = FALSE
		exit
	endif

	GetRandomInt 0,100,g_nRandom

	if ( g_nRandom < 40 )
		g_bTemp = FALSE
		exit
	endif
	
	CanRangeAttack g_bTemp

	if ( g_bTemp==FALSE )
		Exit
	Endif
	
	EstimateRangeAttackHit g_hObject

	if ( g_hObject!=g_hTarget )
		g_bTemp = FALSE
		exit
	endif

	g_bTemp = TRUE

	Exit

;--------------------------------------------------------
:BackoffDone
;--------------------------------------------------------

	g_bBackingOff = FALSE

	gosub CanRangeAttack

	if ( g_bCanRangeAttack==FALSE )
		goto BackoffDone,1
	endif

	gosub ShouldRangeAttack

	if ( g_bTemp==TRUE )
		Stop
		g_bSwoopAfterRange = TRUE
		gosub StartRangeAttack
	else
		goto BackoffDone,1
	Endif

	Exit

;--------------------------------------------------------
:OnFoundTarget
;--------------------------------------------------------

	gosub OnFoundTarget,1

	gosub RangeCheckSetup

	if ( g_hTarget!=NULL )
		gosub ShouldRangeAttack
		if ( g_bTemp==TRUE )
			g_bSwoopAfterRange = FALSE
			gosub StartRangeAttack
		Endif
	Endif

	Exit

;--------------------------------------------------------
:SwoopDone
;--------------------------------------------------------

	gosub SwoopDone,1

	gosub RangeCheckSetup

	exit

;--------------------------------------------------------
:FlyRangeInit
;--------------------------------------------------------

	gosub BaseFlyInit


	Exit

