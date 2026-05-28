;---------------------------------------------------
;	BaseSwim.Inc
;	Jeff Leggett
;	11/07/2001
;
;
;	Base script for monsters that SWIM...
;
;---------------------------------------------------

#include baseCrawl.inc

;--------------------------------------------------------
:LocalShouldRunAway
;--------------------------------------------------------
	g_bTemp = FALSE

	GetStat g_hObject,IsInWater,g_bTemp

	if ( g_bTemp==FALSE )
		g_bTemp	= TRUE
		exit
	endif

	g_bTemp = FALSE

	Exit

;--------------------------------------------------------
:ShouldRunAway
;
;	Set g_hObject to the object you're asking about
;	g_bTemp will be set to TRUE or FALSE
;
;--------------------------------------------------------
	gosub LocalShouldRunAway
	if ( g_bTemp==TRUE )
		Exit
	Endif

	gosub ShouldRunAway,1

	Exit

;----------------------------------------------------------
:BaseShouldRun
;----------------------------------------------------------

	gosub LocalShouldRunAway
	if ( g_bTemp==TRUE )
		Exit
	Endif

	gosub BaseShouldRun,1

	Exit

;----------------------------------------------------------
:BaseSwimStartup
;----------------------------------------------------------
	SetIdle
	Exit

;----------------------------------------------------------
:BaseSwimInit
;----------------------------------------------------------
	wait 29,0.1,BaseSwimStartup
	gosub BaseCrawlInit
	exit
