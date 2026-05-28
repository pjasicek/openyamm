;--------------------------------------------------
;United.inc
; timmy
; handles checking to see if 5 of the 6 clans are united and giving key 178
;
; Keys:
; Sven (3) 34
; Kira (239) 82
;Bjarni (45) 38
; Sigmund (87) 51
; Markel (127) 63
; Tryygva (180) 74
; 5 clans united 178
;--------------------------------------------------





#number					BeenDone
#number					ClanOn
#NumberArray			ClanArray[5]
#Number					counter
#number					Key_1
#number					Key_2
#number					Key_3
#number					Key_4
#number					Key_5
#string					Jarl  



;--------------------------------------------------
:United
; called in OnRudeExit
;--------------------------------------------------
;****************
;gives reward for uniting the clans
;****************


Haskey 179, g_ntemp
if (g_ntemp==0, )
; checks to see if they already have got the reward.
	Haskey 83, g_ntemp
	if (g_ntemp==1, )
	; checks to see if they've United the clans
		GiveKey 179
		GiveExp 26500
		GiveGold 6000
		; gives reward
		exit
	endif
endif
exit

;--------------------------------------------------
:OnCheck
;--------------------------------------------------

haskey 178, g_ntemp
if (g_ntemp==0, )

	g_ncounter = 0

	Haskey Key_1, g_ntemp
	if (g_ntemp==1, )
		g_ncounter = g_ncounter + 1
;		ArrayPut ClanArray, 0, 1
	endif
	
	Haskey Key_2, g_ntemp
	if (g_ntemp==1, )
		g_ncounter = g_ncounter + 1
;		ArrayPut ClanArray, 1, 1
	endif

	Haskey key_3, g_ntemp
	if (g_ntemp==1, )
		g_ncounter = g_ncounter + 1
;		ArrayPut ClanArray, 2, 1
	endif

	Haskey Key_4, g_ntemp
	if (g_ntemp==1, )
		g_ncounter = g_ncounter + 1
;		ArrayPut ClanArray, 3, 1
	endif

	Haskey key_5, g_ntemp
	if (g_ntemp==1, )
		g_ncounter = g_ncounter + 1
;		ArrayPut ClanArray, 4, 1
	endif


	if (g_ncounter == 5)
		givekey 178
		set BeenDone, true
		exit
	endif

;gosub checkallclans
endif
exit

;--------------------------------------------------
:CheckAllClans
;--------------------------------------------------


if ( BeenDone==true )
    exit
endif

Set counter, 0


;--------------------------------------------------
:CheckAllClansloop
;--------------------------------------------------


	

ArrayGet ClanArray, counter, ClanOn
	if (ClanOn==false)
		exit
	endif

Add Counter, 1

If (counter<5)
	Goto CheckAllClansloop
endif


;...........success.............

givekey 178

set BeenDone, true
wait 1 0.2, DoNothing
exit

;-------------------------------------
:SvenInit
;-------------------------------------

Set Key_1, 82
Set Key_2, 38
Set Key_3, 51
Set Key_4, 63
Set Key_5, 74
exit

;-------------------------------------
:KiraInit
;-------------------------------------

Set Key_1, 34
Set Key_2, 38
Set Key_3, 51
Set Key_4, 63
Set Key_5, 74


exit

;-------------------------------------
:BjarniInit
;-------------------------------------

Set Key_1, 82
Set Key_2, 34
Set Key_3, 51
Set Key_4, 63
Set Key_5, 74

exit

;-------------------------------------
:MarkelInit
;-------------------------------------

Set Key_1, 82
Set Key_2, 38
Set Key_3, 51
Set Key_4, 34
Set Key_5, 74
exit

;-------------------------------------
:SigmundInit
;-------------------------------------

Set Key_1, 82
Set Key_2, 38
Set Key_3, 34
Set Key_4, 63
Set Key_5, 74

exit

;-------------------------------------
:TryygvaInit
;-------------------------------------

Set Key_1, 82
Set Key_2, 38
Set Key_3, 51
Set Key_4, 63
Set Key_5, 34
exit

;--------------------------------------------------
:UnitedInit
;--------------------------------------------------

;traceon 
;Don't Forget to Delete this!

If (Jarl==Sven, )
	Gosub SvenInit
	exit
Endif

If (Jarl==Kira, )
	Gosub KiraInit
	exit
Endif

If (Jarl==Bjarni, )
	Gosub BjarniInit
	exit
Endif

If (Jarl==Markel, )
	Gosub MarkelInit
	exit
Endif

If (Jarl==Sigmund, )
	Gosub SigmundInit
	exit
Endif

If (Jarl==Tryygva, )
	Gosub TryygvaInit
	exit
Endif


exit

