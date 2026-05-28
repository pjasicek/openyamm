;--------------------------------------------------
;pledge.inc
; timmy
; handles checking to see if the party got 7 pledges
;

;--------------------------------------------------

#include globals.inc



#Number					BeenDone
#Number					counter
#NumberArray			PledgeArray[7]
#Number					GivePledge
#Number					NoDice=0

;--------------------------------------------------
:reward
;--------------------------------------------------
;****************
;gives reward for uniting the clans
;****************


haskey 277 g_ntemp
if (g_ntemp==0, )
	givekey 277
	giveexp 5000
	Playsound sounds\events\quest.wav, DoNothing, 100, 240, FALSE, 100
	set BeenDone True
	exit
endif
exit

;--------------------------------------------------
:Pledge
;--------------------------------------------------

haskey 265 g_ntemp
if (g_ntemp==0, )
	exit
else

	haskey 277, g_ntemp
	if (g_ntemp==0, )
		
		haskey 269 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 0, 1
		endif
		
		haskey 270 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 1, 1
		endif

		haskey 271 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 2, 1
		endif

		haskey 272 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 3, 1
		endif

		haskey 273 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 4, 1
		endif

		haskey 274 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 5, 1
		endif

		haskey 275 g_ntemp
		if (g_ntemp==1, )
			ArrayPut PledgeArray, 6, 1
		endif

		haskey 276 g_ntemp
		If (g_ntemp==1, )
			ArrayPut PledgeArray, 7, 1
		endif
	endif
endif
gosub CheckAllNPC
exit

;--------------------------------------------------
:CheckAllNPC
;--------------------------------------------------


if ( BeenDone==true )
    exit
endif

Set counter, 0
set NoDice, 0


;--------------------------------------------------
:CheckAllNPCloop
;--------------------------------------------------

if (NODice>1)
	exit
endif
	

ArrayGet PledgeArray, counter, GivePledge
	if (GivePledge==false)
		Add NoDice 1
		endif

Add Counter, 1

If (counter<7)
	Goto CheckAllNPCloop
endif


;...........success.............

gosub reward
exit