;--------------------------------------------------------
;	Healer.inc
;	Jeff Leggett
;
;	This script is used by objects which heal players
;	one time.  That is, once a player is healed by this
;	object, it won't be able to be healed by it again.
;	(Unless it dies and comes back...)
;--------------------------------------------------------

#include globals.inc

#numberArray			g_nPlayerHealedArray[8]
#numberArray			g_nPlayerHealedCountArray[8]

#number					g_nPlayerId
#number					g_nPlayerNbr

; Heal amount defaults to 10... Change this value in your 
; script if you want....

#number					g_nHealAmt=10
#number					g_nHealCount=1

;--------------------------------------------------------
:HealerOnUse
;
;	See if we should heal the object that triggered
;	us..
;
;--------------------------------------------------------

	GetParam 0, g_hObject

	if ( g_hObject==NULL )
		Exit FALSE
	endif

	GetPlayerId g_hObject, g_nPlayerId
	GetPlayerNbr g_hObject, g_nPlayerNbr

	if ( g_nPlayerNbr==-1 )
		; Not a player!							  
		Exit FALSE							  
	endif

	ArrayGet g_nPlayerHealedArray, g_nPlayerNbr, g_nTemp

	if ( g_nTemp==g_nPlayerId )
		ArrayGet g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp
			if ( g_nTemp>=g_nHealCount )

				; they've already Used this item...
				; Don't let them do it again...
				exit FALSE
			endif
	else
		ArrayPut g_nPlayerHealedCountArray, g_nPlayerNbr, 0

	endif

	ArrayGet g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp
	Add g_nTemp, 1
	ArrayPut g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp
	ArrayPut g_nPlayerHealedArray, g_nPlayerNbr, g_nPlayerId

	Heal g_hObject, g_nHealAmt

	Exit

;--------------------------------------------------------
:HealerInit
;
;	You must gosub this routine from your :Main routine
;
;--------------------------------------------------------

;	TraceOn
	AddTrigger Use, HealerOnUse

	Exit