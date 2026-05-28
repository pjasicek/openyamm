;-----------------------------
;	PigPlaylist.inc
;	by SJR
;	12-12-01
;	Purpose:randomly play piggy
;			sounds.
;-----------------------------

#stringarray	spSounds[8]
#string			sSound = ""
#number			nIndex = 0

;-----------------------------
:InitPigPlaylist
;-----------------------------
	ArrayPut spSounds, 0 , "sounds\animsounds\pig\die1.wav"
	ArrayPut spSounds, 1 , "sounds\animsounds\pig\fidget1.wav"
	ArrayPut spSounds, 2 , "sounds\animsounds\pig\fidget2.wav"
	ArrayPut spSounds, 3 , "sounds\animsounds\pig\rest.wav"
	ArrayPut spSounds, 4 , "sounds\animsounds\pig\roll.wav"
	ArrayPut spSounds, 5 , "sounds\animsounds\pig\standdown.wav"
	ArrayPut spSounds, 6 , "sounds\animsounds\pig\standup.wav"
	ArrayPut spSounds, 7 , "sounds\animsounds\pig\wince1.wav"
	ArrayPut spSounds, 8 , "sounds\animsounds\pig\wince2.wav"

	CacheSound "sounds\animsounds\pig\die1.wav"
	CacheSound "sounds\animsounds\pig\fidget1.wav"
	CacheSound "sounds\animsounds\pig\fidget2.wav"
	CacheSound "sounds\animsounds\pig\rest.wav"
	CacheSound "sounds\animsounds\pig\roll.wav"
	CacheSound "sounds\animsounds\pig\standdown.wav"
	CacheSound "sounds\animsounds\pig\standup.wav"
	CacheSound "sounds\animsounds\pig\wince1.wav"
	CacheSound "sounds\animsounds\pig\wince2.wav"

	Exit 1

;-----------------------------
:PlayRandomPig
;-----------------------------
	GetRandomInt 0, 8, nIndex
	ArrayGet spSounds, nIndex, sSound
	PlaySound sSound, DoNothing, 1, 100, 0, 100

	Exit 1

;-----------------------------
:DoNothing
;-----------------------------
	Exit 1