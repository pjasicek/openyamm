;--------------------------------------------------
;NoGold.inc
; timmy
; handles Hjarrrand Fixer voice and quest stuff
;--------------------------------------------------

#include globals.inc



; flag variables
#number							Visible = 1
#number							Solid   = 8192
#number							Gravity = 131072

#string		sVoice1
#string		sVoice2

;Init all the voice variables

#string		sAngryFa = "voices\PC\Angry Female\AngryF24a.wav"
#string		sAngryFb = "voices\PC\Angry Female\AngryF24b.wav"

#string		sAngryMa = "voices\PC\Angry Male\AngryM24b.wav"
#string		sAngryMb = "voices\PC\Angry Male\AngryM24c.wav"

#string		sArrogantFa = "voices\PC\Arrogant Female\ArrogantF24b.wav"
#string		sArrogantFb = "voices\PC\Arrogant Female\ArrogantF24c.wav"

#string		sArrogantMa = "voices\PC\Arrogant Male\ArrogantM24b.wav"
#string		sArrogantMb = "voices\PC\Arrogant Male\ArrogantM24c.wav"

#string		sAssertiveFa = "voices\PC\Assertive Female\AssertiveF24a.wav"
#string		sAssertiveFb = "voices\PC\Assertive Female\AssertiveF24b.wav"

#string		sAssertiveMa = "voices\PC\Assertive Male\AssertiveM24a.wav"
#string		sAssertiveMb = "voices\PC\Assertive Male\AssertiveM24b.wav"

#string		sCowardlyFa = "voices\PC\Cowardly Female\CowardlyF24a.wav"
#string		sCowardlyFb = "voices\PC\Cowardly Female\CowardlyF24b.wav"

#string		sCowardlyMa = "voices\PC\Cowardly Male\CowardlyM24a.wav"
#string		sCowardlyMb = "voices\PC\Cowardly Male\CowardlyM24b.wav"

#string		sDimFa = "voices\PC\Dim Female\DimF24b.wav"
#string		sDimFb = "voices\PC\Dim Female\DimF24c.wav"

#string		sDimMa = "voices\PC\Dim Male\DimMF24a.wav"
#string		sDimMb = "voices\PC\Dim Male\DimM24c.wav"

#string		sHalfOrcLichFa = "voices\PC\Half Orc Lich Female\HalfOrcLichF24a.wav"
#string		sHalfOrcLichFb = "voices\PC\Half Orc Lich Female\HalfOrcLichF24c.wav"

#string		sHalfOrcLichMa = "voices\PC\Half Orc Lich Male\HalfOrcLichM24c.wav"

#string		sHappyFa = "voices\PC\Happy Female\HappyF24a.wav"
#string		sHappyFb = "voices\PC\Happy Female\HappyF24b.wav"

#string		sHappyMa = "voices\PC\Happy Male\HappyM24b.wav"
#string		sHappyMb = "voices\PC\Happy Male\HappyM24c.wav"

#string		sLichFa = "voices\PC\Lich Female\LichF39a.wav"
#string		sLichFb = "voices\PC\Lich Female\LichF39b.wav"

#string		sLichMa = "voices\PC\Lich Male\LichM24b.wav"
#string		sLichMb = "voices\PC\Lich Male\LichM24c.wav"

#string		sSarcasticFa = "voices\PC\Sarcastic Female\SarcasticF24b.wav"
#string		sSarcasticFb = "voices\PC\Sarcastic Female\SarcasticF24c.wav"

#string		sSarcasticMa = "voices\PC\Sarcastic Male\SarcasticM24b.wav"
#string		sSarcasticMb = "voices\PC\Sarcastic Male\SarcasticM24c.wav"

;Parameters
;P0 name of wav file
;P1 name of animation to run
;P2  # of times animation runs


;--------------------------------------------------
:NoGold
;--------------------------------------------------



	getrandomInt 1,2 g_ntemp
	if (g_ntemp==1)
		Playsound sVoice1, DoNothing, 100, 240, FALSE, 100
	else
		Playsound sVoice2, DoNothing, 100, 240, FALSE, 100
	endif
	exit





;-------------------------------------
:VoiceInit
;-------------------------------------



getPCVoice g_ntemp


if (g_ntemp==0)
	set sVoice1 sAngryFa
	set sVoice2 sAngryFb
	exit
endif

if (g_ntemp==1)
	set sVoice1 sArrogantFa
	set sVoice2 sArrogantFb
	exit
endif

if (g_ntemp==2)
	set sVoice1 sAssertiveFa
	set sVoice2 sAssertiveFb
	exit
endif

if (g_ntemp==3)
	set sVoice1 sCowardlyFa
	set sVoice2 sCowardlyFb
	exit
endif

if (g_ntemp==4)
	set sVoice1 sDimFa
	set sVoice2 sDimFb
	exit
endif

if (g_ntemp==5)
	set sVoice1 sHappyFa
	set sVoice2 sHappyFb
	exit
endif

if (g_ntemp==6)
	set sVoice1 sSarcasticFa
	set sVoice2 sSarcasticFb
	exit
endif

if (g_ntemp==7)
	set sVoice1 sLichFa
	set sVoice2 sLichFb
	exit
endif

if (g_ntemp==8)
	set sVoice1 sHalfOrcLichFa
	set sVoice2 sHalfOrcLichFb
	exit
endif

if (g_ntemp==9)
	set sVoice1 sAngryMa
	set sVoice2 sAngryMb
	exit
endif

if (g_ntemp==10)
	set sVoice1 sArrogantMa
	set sVoice2 sArrogantMb
	exit
endif

if (g_ntemp==11)
	set sVoice1 sAssertiveMa
	set sVoice2 sAssertiveMb
endif

if (g_ntemp==12)
	set sVoice1 sCowardlyMa
	set sVoice2 sCowardlyMb
	exit
endif

if (g_ntemp==13)
	set sVoice1 sDimMa
	set sVoice2 sDimMb
	exit
endif

if (g_ntemp==14)
	set sVoice1 sHappyMa
	set sVoice2 sHappyMb
	exit
endif

if (g_ntemp==15)
	set sVoice1 sSarcasticMa
	set sVoice2 sSarcasticMb
	exit
endif

if (g_ntemp==16)
	set sVoice1 sLichMa
	set sVoice2 sLichMb
	exit
endif

if (g_ntemp==17)
	set sVoice1 sHalfOrcLichMa
	set sVoice2 sHalfOrcLichMb
	exit
endif

exit



