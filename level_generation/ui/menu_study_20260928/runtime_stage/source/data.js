'use strict';

// Values are deliberate review defaults, not a read of the user's settings or saves.
// Each setting points to its existing INI owner. See README.md for runtime adoption requirements.
window.MENU_DATA = {
  sections: [
    {id: 'gameplay', name: 'Gameplay', title: 'Gameplay', subtitle: 'Information, feedback, and exploration'},
    {id: 'video', name: 'Video', title: 'Video', subtitle: 'Display and appearance'},
    {id: 'audio', name: 'Audio', title: 'Audio', subtitle: 'Volume 0–9 · Zero mutes a channel'},
    {id: 'controls', name: 'Mouse & Controls', title: 'Mouse & Controls', subtitle: 'Choose how you explore'},
    {id: 'keyboard', name: 'Keyboard', title: 'Keyboard', subtitle: 'Find an action. Choose a key.'},
  ],
  settings: [
    {id:'bolster_monsters', section:'gameplay', group:'Challenge', name:'Monster scaling', type:'toggle', value:false,
      ini:'features.bolster_monsters', desc:'Scale monsters with the party. Apply when entering an area.'},
    {id:'quest_markers', section:'gameplay', group:'Exploration', name:'Quest markers', type:'toggle', value:true,
      ini:'gameplay.quest_markers', desc:'Show quest markers where the game provides them.'},
    {id:'combat_text', section:'gameplay', group:'Combat feedback', name:'Floating combat text', type:'toggle', value:true,
      ini:'gameplay.combat_text', desc:'Show damage and combat messages in the world.'},
    {id:'combat_actor_hp_bars', section:'gameplay', group:'Combat feedback', name:'Enemy health bars', type:'toggle', value:true,
      ini:'gameplay.combat_actor_hp_bars', desc:'Show health bars on combat actors.'},
    {id:'combat_target_panel', section:'gameplay', group:'Combat feedback', name:'Target information', type:'toggle', value:false,
      ini:'gameplay.combat_target_panel', desc:'Show the combat target panel.'},
    {id:'show_hits', section:'gameplay', group:'Combat feedback', name:'Hit messages', type:'toggle', value:true,
      ini:'controls.show_hits', desc:'Report attacks in the status text.'},
    {id:'context_action_popup', section:'gameplay', group:'Interaction', name:'Context action menu', type:'toggle', value:false,
      ini:'gameplay.context_action_popup', desc:'Offer contextual actions for the object under the pointer.'},
    {id:'skip_event_cutscenes', section:'gameplay', group:'Story', name:'Skip event cutscenes', type:'toggle', value:false,
      ini:'video.skip_event_cutscenes', desc:'Skip event movies. Leave off for a first adventure.'},
    {id:'window_mode', section:'video', group:'Display', name:'Display mode', type:'select', value:'windowed',
      ini:'video.window_mode', options:[['windowed','Windowed'],['windowed_fullscreen','Borderless'],['fullscreen','Fullscreen']],
      desc:'Changes must be confirmed within 15 seconds.'},
    {id:'resolution', section:'video', group:'Display', name:'Resolution', type:'select', value:'1600x900',
      ini:'video.resolution', options:[['1280x720','1280 × 720'],['1600x900','1600 × 900'],['1920x1080','1920 × 1080'],['2560x1440','2560 × 1440']],
      desc:'Borderless uses your desktop resolution.'},
    {id:'vsync', section:'video', group:'Display', name:'Vertical sync', type:'toggle', value:false,
      ini:'video.vsync', desc:'Reduce screen tearing by syncing frames to the display.'},
    {id:'view_distance', section:'video', group:'World detail', name:'View distance', type:'select', value:'default',
      ini:'video.view_distance', options:[['default','World default'],['32768','Extended'],['unlimited','Unlimited']],
      desc:'Longer distances can reduce performance outdoors.'},
    {id:'texture_filtering', section:'video', group:'World detail', name:'Smooth textures', type:'toggle', value:true,
      ini:'video.texture_filtering', desc:'Filter texture pixels instead of showing sharp texel edges.'},
    {id:'terrain_anisotropy', section:'video', group:'World detail', name:'Ground texture clarity', type:'select', value:'8x',
      ini:'video.terrain_anisotropy', options:[['2x','2×'],['4x','4×'],['8x','8×'],['16x','16×']],
      desc:'Keep distant ground textures sharper. Uses anisotropic terrain filtering.'},
    {id:'terrain_decorations', section:'video', group:'World detail', name:'Terrain details', type:'toggle', value:false,
      ini:'video.terrain_decorations', desc:'Draw extra terrain decorations where available.'},
    {id:'cinematic_grading', section:'video', group:'Colour & effects', name:'Cinematic colour', type:'toggle', value:true,
      ini:'video.cinematic_grading', desc:'Apply the cinematic colour treatment.'},
    {id:'cinematic_strength', section:'video', group:'Colour & effects', name:'Colour intensity', type:'range', value:60, min:0, max:100,
      ini:'video.cinematic_strength', unit:'%', depends:'cinematic_grading', desc:'Adjust the strength of cinematic colour.'},
    {id:'colored_lights', section:'video', group:'Colour & effects', name:'Coloured lighting', type:'toggle', value:true,
      ini:'video.colored_lights', desc:'Use the colours of nearby light sources.'},
    {id:'tinting', section:'video', group:'Colour & effects', name:'Colour tinting', type:'toggle', value:true,
      ini:'video.tinting', desc:'Retain the original tinting option.'},
    {id:'blood_splats', section:'video', group:'Colour & effects', name:'Blood splats', type:'toggle', value:true,
      ini:'video.blood_splats', desc:'Show blood splat effects.'},
    {id:'melee_hit_blood_effects', section:'video', group:'Colour & effects', name:'Melee blood effects', type:'toggle', value:false,
      ini:'gameplay.melee_hit_blood_effects', desc:'Add blood effects when melee attacks connect.'},
    {id:'sound_volume', section:'audio', group:'Volume', name:'Sound effects', type:'range', value:7, min:0, max:9,
      ini:'audio.sound_volume', unit:'/ 9', desc:'Weapons, spells, interface sounds, and the world.'},
    {id:'music_volume', section:'audio', group:'Volume', name:'Music', type:'range', value:6, min:0, max:9,
      ini:'audio.music_volume', unit:'/ 9', desc:'Music in menus, towns, and dungeons.'},
    {id:'voice_volume', section:'audio', group:'Volume', name:'Voices', type:'range', value:8, min:0, max:9,
      ini:'audio.voice_volume', unit:'/ 9', desc:'Spoken character reactions and dialogue.'},
    {id:'walksound', section:'audio', group:'World sounds', name:'Footsteps', type:'toggle', value:true,
      ini:'controls.walksound', desc:'Play walking and running sounds.'},
    {id:'control_scheme', section:'controls', group:'Input style', name:'Control preset', type:'select', value:'modern',
      ini:'controls.control_scheme', options:[['modern','Modern'],['classic','Classic']],
      desc:'Modern: WASD, left-click attack, E to use. Classic: arrow keys, A to attack, left-click to use.'},
    {id:'mouse_sensitivity', section:'controls', group:'Look & movement', name:'Mouse sensitivity', type:'range', value:100, min:0, max:100,
      ini:'controls.mouse_sensitivity', unit:'%', desc:'The response of mouse movement. Zero disables mouse look movement.'},
    {id:'turn_rate', section:'controls', group:'Look & movement', name:'Turn rate', type:'select', value:'smooth',
      ini:'controls.turn_rate', options:[['16x','16×'],['32x','32×'],['smooth','Smooth']],
      desc:'Preserve the original turning-speed choices.'},
    {id:'always_run', section:'controls', group:'Look & movement', name:'Always run', type:'toggle', value:true,
      ini:'controls.always_run', desc:'Use running movement by default.'},
    {id:'flip_on_exit', section:'controls', group:'Look & movement', name:'Face away on exit', type:'toggle', value:false,
      ini:'controls.flip_on_exit', desc:'Turn the party away from the doorway when leaving a house.'},
  ],
  worlds: [
    {id:'enroth', name:'Enroth', game:'Might and Magic VI', home:'New Sorpigal', image:'enroth.png',
      text:'A troubled kingdom. Forgotten temples. A world on the edge of ruin.'},
    {id:'antagarich', name:'Antagarich', game:'Might and Magic VII', home:'Emerald Island', image:'antagarich.png',
      text:'A castle to claim. Ancient rivalries. A choice between light and dark.'},
    {id:'jadame', name:'Jadame', game:'Might and Magic VIII', home:'Dagger Wound Islands', image:'jadame.png',
      text:'Unlikely allies. Elemental upheaval. An adventure beyond the familiar.'},
  ],
  saves: [
    {id:'manual1', name:'The road to Goblinwatch', world:'enroth', place:'New Sorpigal', kind:'Manual',
      date:'1 January 1168', time:'Monday · 9:42 AM', modified:'28 Sep · 00:18', preview:true},
    {id:'auto', name:'Autosave', world:'enroth', place:'Goblinwatch', kind:'Automatic',
      date:'1 January 1168', time:'Monday · 10:04 AM', modified:'28 Sep · 00:15', reference:2072},
    {id:'quick', name:'Quicksave', world:'enroth', place:'New Sorpigal', kind:'Quick',
      date:'1 January 1168', time:'Monday · 9:36 AM', modified:'28 Sep · 00:12', preview:true},
    {id:'manual2', name:'Before choosing', world:'antagarich', place:'Harmondale', kind:'Manual',
      date:'15 January 1168', time:'Monday · 11:03 AM', modified:'27 Sep · 21:30', reference:2071},
    {id:'manual3', name:'A passage to Ravenshore', world:'jadame', place:'Ravenshore', kind:'Manual',
      date:'8 January 1172', time:'Monday · 4:10 PM', modified:'27 Sep · 20:17'},
    {id:'manual4', name:'The first morning', world:'enroth', place:'New Sorpigal', kind:'Manual',
      date:'1 January 1168', time:'Monday · 8:00 AM', modified:'27 Sep · 19:50', preview:true},
  ],
  fixedBindings: [
    {key:'Escape', label:'Open / close menu'}, {key:'F9', label:'Quicksave'}, {key:'F10', label:'Quickload'},
    {key:'1–5', label:'Select party member'},
  ],
  stats: ['Might','Intellect','Personality','Endurance','Accuracy','Speed','Luck'],
};

// Imported from the current binding registry; unimplemented actions stay in binding_audit.json.
window.MENU_DATA.bindings = [
  {
    "id": "forward",
    "name": "Forward",
    "group": "Movement",
    "code": "KeyW"
  },
  {
    "id": "backward",
    "name": "Backward",
    "group": "Movement",
    "code": "KeyS"
  },
  {
    "id": "left",
    "name": "Move / turn left",
    "group": "Movement",
    "code": "KeyA"
  },
  {
    "id": "right",
    "name": "Move / turn right",
    "group": "Movement",
    "code": "KeyD"
  },
  {
    "id": "jump",
    "name": "Jump",
    "group": "Movement",
    "code": "KeyX"
  },
  {
    "id": "cast_ready",
    "name": "Cast quick spell",
    "group": "Combat",
    "code": "KeyQ"
  },
  {
    "id": "attack",
    "name": "Attack",
    "group": "Combat",
    "code": "MouseLeft"
  },
  {
    "id": "trigger",
    "name": "Interact ahead",
    "group": "Interaction",
    "code": "Space"
  },
  {
    "id": "cast",
    "name": "Open spellbook",
    "group": "Combat",
    "code": "KeyC"
  },
  {
    "id": "char_cycle",
    "name": "Next character",
    "group": "Party & books",
    "code": "Tab"
  },
  {
    "id": "quest",
    "name": "Quest book",
    "group": "Party & books",
    "code": "KeyI"
  },
  {
    "id": "quick_ref",
    "name": "Quick reference",
    "group": "Party & books",
    "code": "KeyZ"
  },
  {
    "id": "rest",
    "name": "Rest",
    "group": "Party & books",
    "code": "KeyR"
  },
  {
    "id": "history",
    "name": "History",
    "group": "Party & books",
    "code": "KeyH"
  },
  {
    "id": "use",
    "name": "Use / interact",
    "group": "Interaction",
    "code": "KeyE"
  },
  {
    "id": "map_book",
    "name": "Map book",
    "group": "Party & books",
    "code": "KeyL"
  },
  {
    "id": "always_run_toggle",
    "name": "Toggle always run",
    "group": "Movement",
    "code": "KeyU"
  },
  {
    "id": "look_up",
    "name": "Look Up",
    "group": "Camera",
    "code": "PageDown"
  },
  {
    "id": "look_down",
    "name": "Look Down",
    "group": "Camera",
    "code": "Delete"
  },
  {
    "id": "center_view",
    "name": "Centre view",
    "group": "Camera",
    "code": "End"
  },
  {
    "id": "zoom_in",
    "name": "Zoom In",
    "group": "Camera",
    "code": "NumpadAdd"
  },
  {
    "id": "zoom_out",
    "name": "Zoom Out",
    "group": "Camera",
    "code": "NumpadSubtract"
  },
  {
    "id": "fly_up",
    "name": "Fly Up",
    "group": "Movement",
    "code": "KeyJ"
  },
  {
    "id": "fly_down",
    "name": "Fly Down",
    "group": "Movement",
    "code": "KeyK"
  },
  {
    "id": "land",
    "name": "Land",
    "group": "Movement",
    "code": "Home"
  },
  {
    "id": "double_speed",
    "name": "Toggle double speed",
    "group": "System",
    "code": "F2"
  }
];
// Exact class starting skills, sampled from the shared base table.
window.MENU_DATA.classes = {
  "Archer": {
    "fixed": [
      "Bow",
      "AirMagic"
    ],
    "optional": [
      "Sword",
      "Axe",
      "Spear",
      "LeatherArmor",
      "FireMagic",
      "WaterMagic",
      "Perception",
      "Armsmaster",
      "Learning"
    ]
  },
  "Cleric": {
    "fixed": [
      "Mace",
      "BodyMagic"
    ],
    "optional": [
      "Staff",
      "Shield",
      "LeatherArmor",
      "SpiritMagic",
      "MindMagic",
      "Merchant",
      "Meditation",
      "Perception",
      "Learning"
    ]
  },
  "Priest": {
    "fixed": [
      "Mace",
      "BodyMagic"
    ],
    "optional": [
      "Staff",
      "Shield",
      "LeatherArmor",
      "SpiritMagic",
      "MindMagic",
      "Merchant",
      "Meditation",
      "Perception",
      "Learning"
    ]
  },
  "Druid": {
    "fixed": [
      "Dagger",
      "EarthMagic"
    ],
    "optional": [
      "Mace",
      "LeatherArmor",
      "WaterMagic",
      "SpiritMagic",
      "BodyMagic",
      "Meditation",
      "Perception",
      "Alchemy",
      "Learning"
    ]
  },
  "Knight": {
    "fixed": [
      "Sword",
      "LeatherArmor"
    ],
    "optional": [
      "Axe",
      "Spear",
      "Bow",
      "Shield",
      "ChainArmor",
      "RepairItem",
      "Bodybuilding",
      "Perception",
      "Armsmaster"
    ]
  },
  "Monk": {
    "fixed": [
      "Dodging",
      "Unarmed"
    ],
    "optional": [
      "Staff",
      "Sword",
      "Dagger",
      "Spear",
      "LeatherArmor",
      "Bodybuilding",
      "Perception",
      "IdentifyMonster",
      "Armsmaster"
    ]
  },
  "Paladin": {
    "fixed": [
      "Mace",
      "SpiritMagic"
    ],
    "optional": [
      "Sword",
      "Dagger",
      "Axe",
      "Shield",
      "LeatherArmor",
      "Merchant",
      "RepairItem",
      "Bodybuilding",
      "Armsmaster"
    ]
  },
  "Ranger": {
    "fixed": [
      "Axe",
      "Perception"
    ],
    "optional": [
      "Sword",
      "Dagger",
      "Bow",
      "LeatherArmor",
      "Bodybuilding",
      "DisarmTraps",
      "Dodging",
      "IdentifyMonster",
      "Armsmaster"
    ]
  },
  "Thief": {
    "fixed": [
      "Dagger",
      "Stealing"
    ],
    "optional": [
      "Bow",
      "LeatherArmor",
      "IdentifyItem",
      "Merchant",
      "Perception",
      "DisarmTraps",
      "Dodging",
      "Alchemy",
      "Learning"
    ]
  },
  "Sorcerer": {
    "fixed": [
      "Staff",
      "FireMagic"
    ],
    "optional": [
      "Dagger",
      "LeatherArmor",
      "AirMagic",
      "WaterMagic",
      "EarthMagic",
      "IdentifyItem",
      "Merchant",
      "IdentifyMonster",
      "Alchemy"
    ]
  },
  "Necromancer": {
    "fixed": [
      "Staff",
      "DarkMagic"
    ],
    "optional": [
      "Dagger",
      "LeatherArmor",
      "FireMagic",
      "AirMagic",
      "WaterMagic",
      "Meditation",
      "IdentifyMonster",
      "Alchemy",
      "Learning"
    ]
  }
};
// Native paperdoll layers and x2 placements, matching CharacterDollTable import and creation preview.
window.MENU_DATA.dolls = {
  "3": {
    "background": "backdolm.png",
    "width": 350,
    "height": 756,
    "layers": [
      {
        "file": "pc03bod.png",
        "x": 60,
        "y": 62,
        "width": 262,
        "height": 650
      },
      {
        "file": "pc03lhu.png",
        "x": 276,
        "y": 300,
        "width": 52,
        "height": 108
      },
      {
        "file": "pc03rhd.png",
        "x": 58,
        "y": 220,
        "width": 84,
        "height": 170
      }
    ]
  },
  "4": {
    "background": "backdoll.png",
    "width": 350,
    "height": 756,
    "layers": [
      {
        "file": "pc04bod.png",
        "x": 120,
        "y": 94,
        "width": 166,
        "height": 594
      },
      {
        "file": "pc04lho.png",
        "x": 234,
        "y": 296,
        "width": 50,
        "height": 142
      },
      {
        "file": "pc04rhd.png",
        "x": 50,
        "y": 264,
        "width": 94,
        "height": 118
      }
    ]
  },
  "5": {
    "background": "backdolm.png",
    "width": 350,
    "height": 756,
    "layers": [
      {
        "file": "pc05bod.png",
        "x": 58,
        "y": 68,
        "width": 272,
        "height": 638
      },
      {
        "file": "pc05lhu.png",
        "x": 276,
        "y": 300,
        "width": 52,
        "height": 108
      },
      {
        "file": "pc05rhd.png",
        "x": 58,
        "y": 220,
        "width": 84,
        "height": 170
      }
    ]
  },
  "6": {
    "background": "backdoll.png",
    "width": 350,
    "height": 756,
    "layers": [
      {
        "file": "pc06bod.png",
        "x": 120,
        "y": 94,
        "width": 166,
        "height": 594
      },
      {
        "file": "pc06lho.png",
        "x": 234,
        "y": 296,
        "width": 50,
        "height": 142
      },
      {
        "file": "pc06rhd.png",
        "x": 50,
        "y": 264,
        "width": 94,
        "height": 118
      }
    ]
  },
  "7": {
    "background": "backdolm.png",
    "width": 350,
    "height": 756,
    "layers": [
      {
        "file": "pc07bod.png",
        "x": 58,
        "y": 68,
        "width": 272,
        "height": 638
      },
      {
        "file": "pc07lhu.png",
        "x": 276,
        "y": 300,
        "width": 52,
        "height": 108
      },
      {
        "file": "pc07rhd.png",
        "x": 58,
        "y": 220,
        "width": 84,
        "height": 170
      }
    ]
  }
};
