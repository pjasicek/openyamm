;-------------------------------------------------------------
;	NewRange.inc
;	Jeff Leggett
;	10/17/2001
;
;	This script implements the type of monster that has a
;	range attack, but only uses it when the target is too
;	far away to melee or the AI cannot get to the target
;
;	This will work for AI that do good melee damage, and
;	their range is not as powerful...
;
;-------------------------------------------------------------

#include basecrawl.inc

#number				RANGE_ATTACK_CHECK_MIN = 1.0
#number				RANGE_ATTACK_CHECK_MAX = 2.5

#number				g_attackChance = 100


;-------------------------------------------------------------
:PreRangeAttack
;-------------------------------------------------------------
	GetTime g_lastAttackTime

	Stop

	; Make sure we face our target during the attack anim...
	Target g_hTarget, TRUE

	FaceObject g_hTarget, 360


	Exit

;-------------------------------------------------------------
:DoRangeAttack
;-------------------------------------------------------------

	RangeAttack RangeAttackDone

	exit

;-------------------------------------------------------------
:PostRangeAttack
;	
;	virtual function only..
;
;-------------------------------------------------------------

	exit

;-------------------------------------------------------------
:RangeAttackDone
;-------------------------------------------------------------

	gosub AttackDone

	exit

;-------------------------------------------------------------
:StartRangeAttack
;-------------------------------------------------------------

	gosub PreRangeAttack
	gosub DoRangeAttack
	gosub PostRangeAttack

	exit


;-------------------------------------------------------------
:CheckRangeTick
;
;	See if we can range attack the target....
;
;-------------------------------------------------------------

	GetRandomFloat RANGE_ATTACK_CHECK_MIN, RANGE_ATTACK_CHECK_MAX, g_nRandom

	Wait ATTACK_CHECK_WAIT, g_nRandom, CheckRangeTick

	if ( g_hTarget==NULL )
		exit
	endif

	CanRangeAttack g_bCanAttack

	if ( g_bCanAttack==FALSE )
		Exit
	Endif

	EstimateRangeAttackHit g_hObject

	g_attackChance	= 0

	if ( g_hObject==NULL )
		g_attackChance = 20
	else
		if ( g_hObject==g_hTarget )
			g_attackChance = 100
		else
			IsClass g_hObject,AIBase,g_bTemp

			if ( g_bTemp==TRUE )
				g_attackChance = 0
			else
				g_attackChance = 20
			endif
		endif
	endif

	if ( g_attackChance==0 )
		Exit
	endif

	GetRandomInt 0, 100, g_nRandom

	if ( g_nRandom > g_attackChance )
		exit
	endif

	gosub StartRangeAttack

	Exit

;-------------------------------------------------------------
:CheckRangeAttack
;-------------------------------------------------------------

	gosub CheckRangeTick

	Exit

;-------------------------------------------------------------
:CheckRangeAttackStop
;-------------------------------------------------------------

	Wait ATTACK_CHECK_WAIT, 0, DoNothing

	Exit

;-------------------------------------------------------------
:SetupTarget
;-------------------------------------------------------------

	gosub SetupTarget,1
	gosub CheckRangeAttack

	Exit

;-------------------------------------------------------------
:ClearTarget
;-------------------------------------------------------------

	gosub ClearTarget,1
	gosub CheckRangeAttackStop
	
	Exit

;-------------------------------------------------------------
:RangeInit
;-------------------------------------------------------------

;;	gosub BaseInit	
;;	gosub BaseCrawlInit


	Exit

