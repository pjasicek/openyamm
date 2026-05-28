;------------------------------------------------------
;	FLAGS.INC
;
;	This include file contains script equivalents to
;	engine flags....
;------------------------------------------------------


#number FLAG_VISIBLE				= 1			; Is this model visible?
#number FLAG_SHADOW					= 2			; Does this model cast shadows?
#number FLAG_CASTSHADOWS			= 8			; For lights only..
#number FLAG_MODELGOURAUDSHADE		= 8			; For Models only..
#number FLAG_SOLIDLIGHT				= 16		; Use the 'fastlight' method for this light.

#number FLAG_ENVIRONMENTMAP			= 32		; Environment map the model.

#number FLAG_SOLID					= 8192		; Object can't go thru other solid objects.

#number FLAG_BOXPHYSICS				= 16384		; Use simple box physics on this object (used for WorldModels and containers).

#number FLAG_TOUCH_NOTIFY			= 65536		; Gets touch notification.
#number FLAG_GRAVITY				= 131072	; Gravity is applied.
#number FLAG_MODELKEYS				= 524288	; The object won't get get MID_MODELSTRINGKEY messages unless

#number FLAG_GOTHRUWORLD			= 2097152	; Object can pass through world
