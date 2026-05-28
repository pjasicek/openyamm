;-------------------------------------------------------------------
;	GLOBALS.INC
;
;	Put commonly used global variables here....
;-------------------------------------------------------------------

;
; I start these all with g_ so we know that they are (global) from 
; an include file...
;
#number				TRUE=1
#number				FALSE=0
#hobject			NULL=0

#number				g_nTemp
#number				g_nRandom
#number				g_bTemp				; for booleans...

#number				g_nDist

#number				g_posX
#number				g_posY
#number				g_posZ

#number				g_velX
#number				g_velY
#number				g_velZ

#number				g_rotX
#number				g_rotY
#number				g_rotZ
#number				g_rotSpin

#hobject			g_hMyObject
#number				g_nCounter

#hobject			g_hObject
#hobject			g_hObject2
#hobject			g_hPlayer
#hobject			g_hTarget

; Use this string for debugOut statements
#string				g_sOut
#string				g_sTemp


;
; These are here for padding only.  This will help to prevent save-game breakage
; for minor script bug fixes.
;

#number				g_bDelayingResurrect=0
#number				g_nPad2
#number				g_nPad3
#number				g_nPad4
#number				g_nPad5

#string				g_sPad1
#string				g_sPad2
#string				g_sPad3
#string				g_sPad4
#string				g_sPad5

#hobject			g_hPad1
#hobject			g_hPad2
#hobject			g_hPad3
#hobject			g_hPad4
#hobject			g_hPad5



;-------------------------------------------------------------------
:DoNothing
;	This function is true to its name.  Useful for canceling
;	callbacks...
;-------------------------------------------------------------------
	Exit

