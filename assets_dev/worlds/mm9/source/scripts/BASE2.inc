;--------------------------------------------------------
;	Base2.inc
;	Jeff Leggett
;	10/03/2001
;
;	New and improved base script.  
;
;	Cleaner
;	More modular
;	Makes more use of function overloading...
;
;	Additions to basecrawl.inc:
;		strafe attacks
;		evasive maneuvers
;	
;
;--------------------------------------------------------

#include basecrawl.inc
#include baseevade.inc

#number				g_nStrafeAttackPct = 80

;--------------------------------------------------------
:TargetMoving
;--------------------------------------------------------

	gosub TargetMoving,1

	Exit

;--------------------------------------------------------
:TargetStill
;--------------------------------------------------------

	if ( g_bStrafeAttack==FALSE )
		gosub TargetStill,1
	endif

	Exit

;--------------------------------------------------------
:PostAttack
;
;	overloaded to potentially do a strafe attack...
;
;--------------------------------------------------------

	g_bStrafeAttack = FALSE

	gosub PostAttack, 1
	gosub IsTargetMoving

	if ( g_bTemp==FALSE )

		GetRandomInt 0, 100, g_nRandom

		if ( g_nRandom < g_nStrafeAttackPct )
			g_bPickDir = TRUE
			gosub BE_AttackStrafe
			g_bPickDir = TRUE
			g_bStrafeAttack = TRUE
		Endif
	endif

	traceOFF

	exit


;--------------------------------------------------------
:BaseInit
;--------------------------------------------------------

	gosub BaseCrawlInit
	
	Exit

