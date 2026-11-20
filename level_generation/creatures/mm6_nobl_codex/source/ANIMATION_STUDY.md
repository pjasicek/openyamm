# MM6 Swordsman motion study

Native authority: ../mm6_nobl/native and native_variants; timing: native_actions.json.
Descriptors 586-588; palettes 777/778/779. Raw SFT time units are 1/16 second.

- Standing: upright, narrow stance, sword in the right hand beside thigh and directed down/forward; free hand beside hip. Preserve native upright stance when adapting the source guard.
- Walk: six frames, 0.75 s; restrained alternating steps, cloak trails behind calves, sword remains clear of body.
- Attack (both slots share it): six front-only frames, 0.75 s. Low ready; right hand moves outward, then sweeps sword across the front to the left; final blade nearly horizontal across the waist. No stab or overhead chop. SwordAttackR1 selected as starting motion after front/side/three-quarter preview. Review and adapt its sweep if necessary. Preserve source rotation frames and 30 fps keys.
- Hit: six front-only frames, 0.75 s. Fit within the native action window.
- Death: five frames, 0.625 s native; head bows, bends at hips, falls to both knees and then forward, sword retained. Allow a longer believable model fall and hold its final pose as Dead.
- Fidget: six frames, 0.75 s native, with a duplicate first source frame. Source ArmedBoost1 is only a stress-pose candidate; inspect native fidget before final selection.
- No spells or missile attacks in native table. Ranged presentation aliases melee. No invented cast or spell sockets.

Initial clips: ArmedIdle, ArmedWalk, ArmedRunForward, SwordAttackR1, ArmedGetHitF1, ArmedDeath1. Fingers solved locally on the sword handle; no source finger animation. ROM extremes in work/rom.json define stress poses.

Palette A olive cloak/burgundy tunic; B blue cloak/blue-violet tunic; C magenta cloak/dark brown tunic. Hair, skin, dark limbs and metal retain native colours.

Native fidget inspected: five unique front frames (six records), chiefly a blink with minimal stance shift. ArmedBoost1 is rejected for Fidget; reuse a quiet ArmedIdle breathing cycle with restrained authored head movement.

Death source selected after preview: Armed-Shield.glb / ShieldDeath1 bends, kneels and falls forward, matching native nobldie. UnarmedDeath1 and 2HandSwordDeath1 fall backwards and are rejected. Shield is not included; the body animation and sword-hand motion are reused.

Standing and Fidget use RelaxIdle as the upright body base; the relaxed right wrist will be fitted to the armed grip if the sword axis is wrong in the clay preview. Source keys and ROM extraction run at 30 fps.
