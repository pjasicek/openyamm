#!/usr/bin/env python3
"""One classified index over every owned animation source: humanoid set, Mixamo and stored Meshy clips.

Usage (repo root or anywhere; plain python3, Blender is only launched to measure new clips):
  build_anim_index.py import-mixamo DIR [DIR ...]
      hard-link new Mixamo downloads into anim_library/mixamo/ (singles at the root, pack ZIPs extracted to
      packs/<Pack>/, the ZIPs archived in anim_library/_archives/mixamo_packs/); files already stored, or removed
      earlier as duplicates, are skipped by content hash
  build_anim_index.py build [--jobs N] [--dry-run]
      measure new clips (Blender, cached by content hash), drop duplicates, classify, move discards to
      mixamo/_discarded/ (and back if a rule changes), write anim_library/index.json and anim_library/INDEX.md
  build_anim_index.py find [--role R] [--weapon W] [--posture P] [--tier T] [--style S] [--source S] [--body B]
                           [--text WORD] [--loop] [--in-place] [--top N] [--json]
      ranked query over index.json (default: tier core, best score first)

Rules live in this file (ROLE_RULES, DISCARD_RULES, WEAPON_RULES, STYLE_RULES); rerun `build` after editing them.
"""
import argparse, collections, hashlib, json, os, re, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
LIB = os.path.join(REPO, 'anim_library')
MIXAMO = os.path.join(LIB, 'mixamo')
DISCARDED = os.path.join(MIXAMO, '_discarded')
CHARACTERS = os.path.join(MIXAMO, 'characters')
PACK_ARCHIVE = os.path.join(LIB, '_archives', 'mixamo_packs')
CACHE = os.path.join(LIB, '_cache')
METRICS = os.path.join(CACHE, 'clip_metrics.jsonl')
REMOVED = os.path.join(CACHE, 'removed_duplicates.json')
INDEX = os.path.join(LIB, 'index.json')
INDEX_MD = os.path.join(LIB, 'INDEX.md')
CATALOGUES = os.path.join(HERE, '..', 'catalogues')
METRICS_SCRIPT = os.path.join(HERE, 'clip_metrics_blender.py')

ENGINE_ROLES = ['standing', 'walking', 'run', 'attack_melee', 'attack_ranged', 'cast', 'hit', 'dying', 'fidget', 'fly']
EXTRA_ROLES = ['block', 'dodge', 'talk', 'npc_work', 'crawl', 'swim', 'fall', 'jump', 'turn', 'transition', 'other']

# Rig-specific ankle height (feet joint over the floor, as a fraction of leg length) for the airborne test.
ANKLE_REF = {'mixamo': 0.318, 'humanoid_set': 0.126}


def rel(p):
    return os.path.relpath(p, REPO)


def sha1_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path, default):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------------------------------------------
# Import

def import_mixamo(dirs):
    os.makedirs(MIXAMO, exist_ok=True)
    os.makedirs(PACK_ARCHIVE, exist_ok=True)
    known = {}
    for path in iter_mixamo_files(include_discarded=True):
        known[sha1_file(path)] = path
    removed = load_json(REMOVED, {})
    added = skipped = 0
    for src_dir in dirs:
        for name in sorted(os.listdir(src_dir)):
            src = os.path.join(src_dir, name)
            low = name.lower()
            if low.endswith('.fbx'):
                h = sha1_file(src)
                if h in known or h in removed:
                    skipped += 1
                    continue
                dst = unique_path(os.path.join(MIXAMO, name))
                link_or_copy(src, dst)
                known[h] = dst
                added += 1
            elif low.endswith('.zip'):
                archived = os.path.join(PACK_ARCHIVE, name)
                if not os.path.exists(archived):
                    link_or_copy(src, archived)
                pack_dir = os.path.join(MIXAMO, 'packs', name[:-4])
                with zipfile.ZipFile(src) as z:
                    for info in z.infolist():
                        if info.is_dir() or not info.filename.lower().endswith('.fbx'):
                            continue
                        data = z.read(info)
                        h = hashlib.sha1(data).hexdigest()
                        if h in known or h in removed:
                            skipped += 1
                            continue
                        dst = unique_path(os.path.join(pack_dir, os.path.basename(info.filename)))
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        with open(dst, 'wb') as f:
                            f.write(data)
                        known[h] = dst
                        added += 1
    print('imported %d new files, skipped %d already stored or removed as duplicates' % (added, skipped))


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists('%s (%d)%s' % (base, i, ext)):
        i += 1
    return '%s (%d)%s' % (base, i, ext)


def link_or_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def iter_mixamo_files(include_discarded=True):
    if not os.path.isdir(MIXAMO):
        return
    for root, dirs, files in os.walk(MIXAMO):
        if not include_discarded and root.startswith(DISCARDED):
            continue
        for f in files:
            if f.lower().endswith('.fbx'):
                yield os.path.join(root, f)


# ---------------------------------------------------------------------------------------------------------------
# Measurement (Blender, cached by content hash)

def load_metrics():
    out = {}
    if os.path.exists(METRICS):
        for line in open(METRICS):
            try:
                r = json.loads(line)
                out[r['sha1']] = r
            except (ValueError, KeyError):
                pass
    return out


def measure_missing(paths_by_sha, cache, jobs):
    todo = [(h, p) for h, p in paths_by_sha.items() if h not in cache]
    if not todo:
        return
    print('measuring %d new clips with %d Blender jobs' % (len(todo), jobs))
    tmp = tempfile.mkdtemp(prefix='anim_metrics_')
    parts = [todo[i::jobs] for i in range(jobs)]
    procs = []
    for i, part in enumerate(parts):
        if not part:
            continue
        lst = os.path.join(tmp, 'part_%02d.txt' % i)
        with open(lst, 'w') as f:
            f.write('\n'.join(p for h, p in part) + '\n')
        out = os.path.join(tmp, 'part_%02d.jsonl' % i)
        log = open(os.path.join(tmp, 'part_%02d.log' % i), 'w')
        procs.append((subprocess.Popen(['blender', '-b', '--factory-startup', '-P', METRICS_SCRIPT, '--', lst, out],
                                       stdout=log, stderr=subprocess.STDOUT), out))
    sha_by_path = {p: h for h, p in todo}
    os.makedirs(CACHE, exist_ok=True)
    with open(METRICS, 'a') as cache_file:
        for proc, out in procs:
            proc.wait()
            if not os.path.exists(out):
                continue
            for line in open(out):
                r = json.loads(line)
                r['sha1'] = sha_by_path[r['path']]
                r.pop('path', None)
                cache[r['sha1']] = r
                cache_file.write(json.dumps(r) + '\n')
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------
# Text rules

def rx(*words):
    return re.compile(r'\b(?:' + '|'.join(words) + r')\b')


DISCARD_RULES = [
    ('firearm', rx(r'rifles?', r'pistols?', r'guns?', 'gunplay', 'handgun', 'shooter', r'grenades?', 'ammo', 'bayonet',
                   r'reload\w*', 'sniper', 'rapid fire', 'shooting gun', 'shooting pistol', 'firing', 'fire rifle',
                   'shoot rifle', 'aiming gun', 'drawing gun', '2hand shooting', '1hand pistol', 'shotgun',
                   'military', 'revolver')),
    ('sport', rx('baseball', 'batter', 'soccer', 'soccerball', 'football', r'goalkeeper\w*', 'goalie', r'golf\w*',
                 'quarterback', 'receiver catch', 'frisbee', 'dribble', 'header', 'throw in', 'penalty',
                 r'skateboard\w*', 'treadmill', 'punching bag', 'speedbag', 'umpire', 'football hike', 'tackle',
                 'kick soccerball', 'intercepting', 'chip', 'tennis', 'basketball')),
    ('dance', rx(r'danc\w*', 'hip hop', r'breakdance\w*', 'bboy', r'uprock\w*', 'flair', 'headspin', 'head spinning',
                 r'freezes?', 'footwork', 'moonwalk', 'thriller', 'salsa', 'samba', 'rumba', 'twerk', 'macarena',
                 'ymca', 'gangnam', 'hokey pokey', 'can can', 'northern soul', 'tut', 'locking', 'shuffling',
                 'rapping', 'singing', 'twist dance', 'belly', 'bellydancing', 'maraschino', 'running man',
                 "rockin' shackle", 'rockin shackle', 'crossleg freeze', 'wave hip hop', 'ginga', 'au', 'au to role',
                 'macaco', 'troca', 'brooklyn')),
    ('exercise', rx(r'squats?', r'burpee\w*', 'plank', 'push up', 'pushup', 'sit up', r'situps?', 'crunch',
                    'jumping jacks', 'kettlebell', 'bicep curl', 'front raises', 'clean and jerk', 'snatch',
                    'sumo high pull', 'warming up', r'stretching', 'jumping rope', 'box jump', 'jump push up',
                    'idle to push up', 'idle to situp', 'situp to idle', 'workout', 'exercise', 'cross jumps')),
    ('modern_or_prop', rx('phone', r'texting', r'typing', 'type to sit', 'sit to type', 'fax', 'filing cabinet',
                          'files', 'car', 'driving', 'honking', r'pilot\w*', 'wheelchair', 'iv pole', 'briefcase',
                          'touchscreen', 'tablet', 'gaming', 'listening to music', 'guitar', 'piano', 'violin',
                          'drums', 'smoking', 'inhaler', 'pill', 'cpr', r'hostage', 'button pushing', 'entering code',
                          'working on device', 'shopping', 'computer', 'camera', 'jumping out of a plane',
                          'hit by car', 'jostled passenger', 'scary clown', 'skinning test', 't pose', 'salute',
                          'drinking fountain', 'military signaling', 'bag', 'touchscreen')),
    ('paired', rx('being carried', 'double leg takedown', 'shoulder throw', 'taken hostage', 'release hostage',
                  'pulled from seat', 'removing driver', 'restrain', 'holding down', r'strangl\w*',
                  'superhuman choke lift', 'getting thrown', 'flying shoulder throw', 'shaking hands', 'assassination',
                  'knock off assailant', 'hold off assailant', 'receiving cpr', 'administering cpr', 'disarmed')),
    ('stunt', rx(r'backflip\w*', r'back flip', 'front flip', r'flips?', 'cartwheel', 'kip up', 'wall run', 'wall crash',
                 r'vault\w*', 'parkour', 'dive roll', 'running dive', 'run to dive', 'forward roll', 'roll left',
                 r'prone roll', 'stand to roll', 'run to rolling', 'falling to roll', 'quick roll', 'running slide',
                 'backslide', 'aerial evade', 'corkscrew', 'stylish flip', 'jump over', 'jumping over into combat',
                 'spin in place', 'spinning', r'teeter\w*', 'edge slip', 'running forward flip')),
    ('climb', rx(r'climb\w*', 'ladder', r'ledge', r'hang\w*', 'shimmy', r'freehang\w*', r'braced\w*', 'rope',
                 'swing into wall', 'start swinging', 'swinging', 'swing to land', r'stairs', 'jump to hang',
                 'rope swinging', 'drop to freehang', 'jumping to hanging', 'wall support')),
    ('cover_stealth', rx(r'cover\w*', 'peek', 'peek around corner', 'look around corner', 'emerge from cover',
                         'taking cover')),
    ('prone', rx(r'prone\w*', 'low crawl', 'crawl backwards in prone')),
    ('comedic_or_medical', rx('catwalk', 'strut', 'strut walking', 'twerk', 'booty', 'blow a kiss', r'kiss\w*',
                              'silly', 'goofy', 'chicken', 'bashful', 'pouting', 'sexy', 'spat in face',
                              'spit reaction', 'vomiting', r'seizure', 'convulsing', 'stroke', 'severe cough',
                              'mild cough', 'getting smashed', 'wobbling', 'slide hip hop walk', 'picking at shirt',
                              'loser')),
    ('static_pose', rx(r'pose')),
]

ROLE_RULES = [
    # (role, regex) in priority order; the first match is the primary role, later matches add secondary roles.
    ('dying', rx(r'death\w*', 'dying', 'die', 'dead', 'killed', 'knocked out', 'knocked unconscious', 'knockdown',
                 'knocked down', 'fall flat', 'falling flat impact', 'sweep fall', 'livershot knockdown',
                 'shoulder hit and fall', 'fall over', 'falling down', 'falling from losing balance')),
    ('cast', rx(r'cast\w*', r'spells?', 'magic attack', 'magic area attack', 'magic heal', 'fireball', 'heal',
                'power up', 'boost', 'summon', 'conjure', 'aoe', 'buff')),
    ('attack_ranged', rx('draw arrow', 'shooting arrow', 'aim overdraw', 'aim recoil', 'aiming fire',
                         'aiming pull', r'throw\w*', 'toss', 'shoot arrow', 'bow aiming', 'crossbow aiming',
                         'crossbow reload')),
    ('block', rx(r'block\w*', 'parry', r'defend\w*', 'shielding face', 'guard')),
    ('hit', rx('hit', 'hits', 'react', 'reacting', 'reaction', r'impact', 'getting hit', 'struck', 'stomach',
               'kidney', 'rib', 'receive', 'receiving', 'taking punch', r'shove\w*', r'stumbl\w*', 'flinch',
               'pain gesture', 'electrocuted', 'getting bit', 'gethit', 'knockback', 'body blow', 'tripping')),
    ('attack_melee', rx(r'attack\w*', r'punch\w*', r'kick\w*', 'jab', 'jabs', 'hook', 'uppercut', 'cross', r'slash\w*',
                        'stab', 'stabbing', 'swing', 'strike', 'smash', 'bash', 'combo', 'headbutt', r'elbow\w*',
                        'knee', 'sweep', 'leg sweep', 'roundhouse', 'bite', 'biting', 'swiping', 'thrust', 'chop',
                        'hell slammer', 'fist fight', 'boxing', 'slammer', 'martelo', 'meia lua', 'chapa',
                        'armada', 'bencao', 'queshada', 'pontera', 'rasteira', 'chapa giratoria', 'chapaeu',
                        'quad punch', 'smashing', 'claw', 'stomp', 'stomping', 'vampiric bite',
                        'neck bite', 'snatch attack')),
    ('dodge', rx(r'dodg\w*', 'evade', 'evading', r'duck\w*', r'esquiva\w*', 'dash')),
    ('fly', rx('flying', 'floating', r'hover\w*', r'levitat\w*', 'fly', 'treading water')),
    ('swim', rx(r'swim\w*', 'paddling')),
    ('fall', rx('falling', 'fall a loop', 'fall b loop', 'falling idle', 'jump loop', 'fall loop', 'relax fall',
                'fall')),
    ('crawl', rx(r'crawl\w*')),
    ('jump', rx(r'jump\w*', 'hop', r'landing', 'land', 'hard landing')),
    ('turn', rx(r'turn\w*', 'pivot', '180', 'change direction')),
    ('run', rx('run', 'running', 'jog', 'jogging', r'sprint\w*', 'charge')),
    ('walking', rx('walk', 'walking', 'walker', r'strafe\w*', r'strafing', 'sneak', 'sneaking', 'stepping forward',
                   'stepping backward', 'step backward', 'step forward', 'side step', 'stepping left', 'quick steps',
                   'pacing')),
    ('transition', rx(r'idle to', 'to idle', 'to standing', 'to crouch', 'to crouched', 'stand to', 'crouch to',
                      'standing to', 'sit to', 'to sit', 'start walking', r'un ?sheath\w*', 'getup', 'stop walking', 'walk to stop',
                      'run to stop', 'running to stop', 'start', 'stop', 'end', 'transition', 'getting up',
                      'stand up', 'standing up', 'waking', r'draw\w*', r'sheath\w*', 'withdrawing', r'equip\w*',
                      r'disarm\w*', 'put back', 'pull out', 'activate', 'revive', 'emerging', 'entry', 'to run',
                      'to sprinting', 'to running', 'to walk', 'pickup', 'idle transition', 'stand up')),
    ('talk', rx(r'talk\w*', 'arguing', 'asking question', 'telling a secret', 'having a meeting', 'listening',
                'greeting', 'calling', 'counting', 'plotting')),
    ('npc_work', rx('digging', 'dig and plant', r'plant\w*', 'pull plant', 'pick fruit', 'harvesting', 'watering',
                    r'wheelbarrow\w*', 'gathering objects', 'picking up', 'pick up', 'carrying', 'holding',
                    'box idle', 'box walk', 'box turn', 'lifting', 'putting down', 'tender placement', r'push\w*',
                    r'pull\w*', 'cow milking', r'petting\w*', 'fishing', 'bartending', 'drinking', 'drink',
                    r'pray\w*', 'rummaging', r'search\w*', 'reaching', 'taking item', r'open\w*', r'clos\w*', 'lid',
                    'patting', 'swatting bugs', 'writing', 'cards', 'dice', 'inspecting', 'finding', 'moving object',
                    'helping out', 'button', 'light torch', 'burn webs', 'torch inspect', 'grab torch')),
    ('fidget', rx('look around', r'looking\w*', 'look behind', 'look over shoulder', 'look away', 'scratch', 'yawn',
                  'bored', 'impatient', r'shrug\w*', r'nod\w*', 'head shake', 'shaking head', r'taunt\w*', 'roar',
                  'roaring', r'flex\w*', 'battlecry', 'chest thump', r'yell\w*', 'shout', r'angry', 'victory',
                  r'cheer\w*', 'fist pump', r'wav\w*', r'point\w*', 'beckoning', r'gesture\w*', r'think\w*',
                  'thoughtful', 'laughing', 'laugh', r'clap\w*', 'excited', 'happy', 'sad', 'crying', 'scared',
                  'terrified', 'surprised', 'relieved', 'disappointed', 'defeat', 'insult', 'threatening',
                  'whatever', 'dismissing', 'agreeing', 'acknowledging', 'no', 'thankful', 'formal bow',
                  'informal bow', 'relax bow', 'wiping sweat', 'shaking it off', 'dizzy', 'rubbing', 'check shoe',
                  'searching pockets', 'rallying', 'focus', 'scream', 'agonizing', 'agony', 'nervously',
                  'being cocky', 'cocky', 'banging fist', 'shake fist', 'hand raising', 'reaching out', 'insult',
                  'annoyed', 'crazy', 'relax no', 'relax yes', 'thumbs up', 'weight shift', 'stunned', 'dizzy idle',
                  'shoulder rubbing', 'writhing', 'patting')),
    ('standing', rx('idle', 'standing', 'stand', 'ready', 'stance', 'breathing', 'neutral', 'standard idle',
                    'crouching', 'crouch', 'kneeling', 'kneel', 'sitting', 'seated', 'laying', 'lying', 'leaning')),
]

WEAPON_RULES = [
    ('crossbow', rx('crossbow')),
    ('bow', rx('longbow', 'arrow', r'2hand bow', 'standing aim', 'aim overdraw', 'aim recoil', 'equip bow',
               'disarm bow', 'bow attack', 'bow aiming', 'bow idle', 'bow walk', 'bow run')),
    ('firearm', rx(r'rifles?', r'pistols?', r'guns?', 'shooting', '2hand shooting', 'shooter')),
    ('sword_shield', rx('sword and shield', 'shield')),
    ('sword_2h', rx('great sword', 'greatsword', 'two hand sword', 'two handed sword', '2hand sword')),
    ('axe', rx('axe', '2hand axe', 'melee axe')),
    ('spear', rx('spear', 'pike', 'lance')),
    ('staff', rx('staff')),
    ('club', rx('club', 'mace', 'hammer', 'heavy weapon')),
    ('dagger', rx('dagger', 'knife', 'double dagger')),
    ('torch', rx('torch')),
    ('sword_1h', rx('sword', 'one hand sword', 'stable sword')),
    ('dual', rx('dual weapon', 'dual')),
    ('one_handed', rx('armed', 'item attack')),
    ('prop', rx('box', 'carrying', 'holding', 'wheelbarrow', 'bag')),
]

STYLE_RULES = [
    ('female', rx('female', 'woman', 'femme', 'girl', 'drunk female')),
    ('zombie', rx('zombie', 'walker walk', 'scary zombie', 'not so scary zombie')),
    ('mutant', rx('mutant')),
    ('creature', rx('creature', 'orc', 'dwarf', 'troll', 'ogre', 'monster', 'vampiric', 'beast', 'warrok')),
    ('injured', rx('injured', 'hurting', 'limp', 'wounded', 'agony')),
    ('drunk', rx('drunk')),
    ('old', rx('old man', 'elderly')),
    ('sneak', rx('sneak', 'sneaking', 'stealth', 'crouch', 'crouched', 'crouching')),
    ('combat', rx('fight', 'fighting', 'combat', 'warrior', 'offensive', 'battle', 'mma', 'boxing', 'ninja',
                  'action idle', 'ready')),
    ('casual', rx('relax', 'casual', 'happy', 'swagger', 'standard')),
    ('magic', rx('magic', 'spell', 'cast', 'casting')),
    ('capoeira', rx('capoeira', 'martelo', 'meia lua', 'chapa', 'armada', 'bencao', 'queshada', 'pontera',
                    'rasteira', 'esquiva', 'chapaeu')),
    ('boxing', rx('boxing', 'jab', 'hook', 'uppercut', 'mma', 'illegal')),
    ('sad', rx('sad', 'defeat', 'disappointed', 'crying')),
    ('emotional', rx('happy', 'excited', 'cheer', 'victory', 'joyful')),
]

PACK_HINTS = [
    (re.compile(r'magic'), {'styles': ['magic']}),
    (re.compile(r'great sword'), {'weapon': 'sword_2h'}),
    (re.compile(r'sword and shield'), {'weapon': 'sword_shield'}),
    (re.compile(r'melee axe'), {'weapon': 'axe'}),
    (re.compile(r'longbow'), {'weapon': 'bow'}),
    (re.compile(r'rifle|pistol|shooter'), {'discard': 'firearm'}),
    (re.compile(r'soccer'), {'discard': 'sport'}),
    (re.compile(r'breakdance'), {'discard': 'dance'}),
    (re.compile(r'capoeira'), {'styles': ['capoeira']}),
    (re.compile(r'zombie'), {'styles': ['zombie']}),
    (re.compile(r'creature'), {'styles': ['creature']}),
    (re.compile(r'injured'), {'styles': ['injured']}),
    (re.compile(r'drunk'), {'styles': ['drunk']}),
    (re.compile(r'female'), {'styles': ['female']}),
    (re.compile(r'farming'), {'roles': ['npc_work']}),
]

# Humanoid-set vocabulary (file names such as RPG-Character@2Hand-Sword-GetHit-F1).
HS_FOLDER_WEAPON = {'1Hand': None, '2Hand Axe': 'axe', '2Hand Bow': 'bow', '2Hand Crossbow': 'crossbow',
                    '2Hand Shooting': 'firearm', '2Hand Spear': 'spear', '2Hand Staff': 'staff',
                    '2Hand Sword': 'sword_2h', 'Armed': 'one_handed', 'Armed-Shield': 'sword_shield',
                    'Unarmed': 'unarmed', 'Relax': 'unarmed', 'Crawl': 'unarmed', 'Swimming': 'unarmed',
                    'Climbing-Ladder': 'unarmed', 'Climbing-Ledge': 'unarmed'}


def norm_text(*parts):
    t = ' '.join(p for p in parts if p).lower()
    t = t.replace('_', ' ').replace('/', ' ').replace('-', ' ')
    t = re.sub(r'(?<=[a-z])(?=\d)', ' ', t)
    t = re.sub(r'[^a-z0-9\' ]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def base_name(path):
    n = os.path.splitext(os.path.basename(path))[0]
    n = re.sub(r'^RPG-Character@', '', n)
    return re.sub(r' \(\d+\)$', '', n)


# ---------------------------------------------------------------------------------------------------------------
# Sources

def collect_sources():
    """Every clip file with its source, display name, pack/set and extra text."""
    clips = []
    for path in iter_mixamo_files(include_discarded=True):
        r = os.path.relpath(path, MIXAMO)
        if r.startswith('characters' + os.sep):
            continue
        parts = r.split(os.sep)
        if parts[0] == '_discarded':
            parts = parts[1:]
        pack = parts[1] if parts[0] == 'packs' and len(parts) > 2 else None
        clips.append({'source': 'mixamo', 'path': path, 'name': base_name(path), 'pack': pack})
    hs = os.path.join(LIB, 'humanoid_set')
    if os.path.isdir(hs):
        for folder in sorted(os.listdir(hs)):
            d = os.path.join(hs, folder)
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.lower().endswith('.fbx'):
                    clips.append({'source': 'humanoid_set', 'path': os.path.join(d, f), 'name': base_name(f),
                                  'set': folder})
    meshy = os.path.join(LIB, 'meshy')
    meshy_cat = {c['action_id']: c for c in load_json(os.path.join(CATALOGUES, 'meshy_library.json'), [])}
    if os.path.isdir(meshy):
        for root, dirs, files in os.walk(meshy):
            for f in files:
                if not f.endswith('.glb'):
                    continue
                path = os.path.join(root, f)
                info = load_json(os.path.join(root, 'info.json'), {})
                folder = os.path.basename(root)
                name = info.get('name') or info.get('prompt') or folder.replace('_', ' ')
                c = meshy_cat.get(info.get('action_id'), {})
                clips.append({'source': 'meshy', 'path': path, 'name': name, 'action_id': info.get('action_id'),
                              'extra': ' '.join(filter(None, [c.get('category'), c.get('sub_category'),
                                                              info.get('prompt')]))})
    return clips


def match_catalogue(clips, metrics):
    cat = load_json(os.path.join(CATALOGUES, 'mixamo_motions.json'), [])
    by_name = collections.defaultdict(list)
    for c in cat:
        by_name[re.sub(r'[^a-z0-9]', '', c['name'].lower())].append(c)
    for clip in clips:
        if clip['source'] != 'mixamo':
            continue
        m = metrics.get(clip['sha1'], {})
        cands = by_name.get(re.sub(r'[^a-z0-9]', '', clip['name'].lower()), [])
        frames = m.get('frames') or 0
        # Downloads carry one or two more frames than the catalogue lists.
        close = [c for c in cands if c.get('frames') is not None and -3 <= (c['frames'] - frames) <= 1]
        if not close:
            clip['catalogue'] = {'match': 'none' if not cands else 'name_only', 'candidates': len(cands)}
            if cands:
                clip['descriptions'] = sorted({c['description'] for c in cands if c.get('description')})[:4]
            continue
        close.sort(key=lambda c: abs(c['frames'] + 1.5 - frames))
        best = close[0]
        clip['catalogue'] = {'match': 'unique' if len(close) == 1 else 'ambiguous', 'mixamo_id': best['id'],
                             'preview_gif': best.get('preview_gif'), 'candidates': len(close)}
        clip['descriptions'] = sorted({c['description'] for c in close if c.get('description')})[:4]
        clip['catalogue_tags'] = sorted({t for c in close for t in c.get('tags', [])})
        clip['supports_in_place'] = any(c.get('supports_in_place') for c in close)


# ---------------------------------------------------------------------------------------------------------------
# Classification

def classify(clip, m, standing_ref):
    src = clip['source']
    desc = ' '.join(clip.get('descriptions', []))
    text = norm_text(clip['name'], clip.get('set'), clip.get('extra'))
    full = norm_text(clip['name'], desc, clip.get('pack'), clip.get('set'), clip.get('extra'),
                     ' '.join(clip.get('catalogue_tags', [])))
    discard = []
    for reason, pat in DISCARD_RULES:
        if pat.search(text) or (reason in ('firearm', 'sport', 'modern_or_prop') and pat.search(full)):
            discard.append(reason)
    roles = []
    for role, pat in ROLE_RULES:
        if pat.search(text):
            roles.append(role)
    if not roles:
        for role, pat in ROLE_RULES:
            if pat.search(full):
                roles.append(role)
    weapon = None
    for w, pat in WEAPON_RULES:
        if pat.search(text) or pat.search(full):
            weapon = w
            break
    styles = [s for s, pat in STYLE_RULES if pat.search(full)]
    pack = (clip.get('pack') or '').lower()
    for pat, hint in PACK_HINTS:
        if pack and pat.search(pack):
            if 'discard' in hint and hint['discard'] not in discard:
                discard.append(hint['discard'])
            if 'weapon' in hint and weapon in (None, 'prop', 'one_handed'):
                weapon = hint['weapon']
            styles += hint.get('styles', [])
            roles += [r for r in hint.get('roles', []) if r not in roles]
    if src == 'humanoid_set':
        hw = HS_FOLDER_WEAPON.get(clip.get('set'))
        if hw and weapon in (None, 'prop', 'one_handed', 'dual'):
            weapon = hw
        if hw == 'firearm' and 'firearm' not in discard:
            discard.append('firearm')
        if re.search(r'\bpistol\b', text) and 'firearm' not in discard:
            discard.append('firearm')
    if weapon == 'firearm' and 'firearm' not in discard:
        discard.append('firearm')
    if weapon in ('bow', 'crossbow') and 'firearm' in discard and not re.search(r'rifle|pistol|gun', full):
        discard.remove('firearm')
    styles = sorted(set(styles))
    rifle_pose = False
    if 'firearm' in discard and not DISCARD_RULES[0][1].search(text) and src == 'mixamo' and \
            roles and roles[0] in ('dying', 'hit'):
        # Only the description mentions the rifle: a usable fall with the arms in a rifle grip.
        discard.remove('firearm')
        rifle_pose = True
        if weapon == 'firearm':
            weapon = None

    # Primary role, with a few disambiguations.
    role = roles[0] if roles else 'other'
    if role == 'transition' and any(r in roles for r in ('attack_melee', 'dying')) and \
            not re.search(r'\b(draw|sheath|equip|disarm|activate)\b', text):
        role = 'attack_melee' if 'attack_melee' in roles else 'dying'
    if role == 'turn' and any(r in roles for r in ('dying', 'attack_melee', 'hit')):
        role = next(r for r in roles if r in ('dying', 'attack_melee', 'hit'))
    if role == 'fall' and 'dying' in roles:
        role = 'dying'
    if role in ('hit',) and 'attack_melee' in roles and re.search(r'\b(attack|punch|kick|slash)\b', text) and \
            not re.search(r'\b(react|reaction|receive|getting|gethit)\b', text):
        role = 'attack_melee'
    if role == 'standing' and 'fidget' in roles:
        role = 'fidget'
    if role == 'jump' and 'attack_melee' in roles:
        role = 'attack_melee'
    if role in ('run', 'walking') and 'attack_melee' in roles and re.search(r'attack|swing|slash', text):
        role = 'attack_melee'
    if role in ('run', 'walking') and 'fly' in roles:
        role = 'fly'
    if role == 'block' and 'hit' in roles and re.search(r'gethit|react', text):
        role = 'hit'
    if re.search(r'\bdice\b', text):
        role = 'npc_work'
    if role in ('walking', 'run') and re.search(r'\b(start|stop|stopping|starting)\b', text):
        role = 'transition'
    if 'dying' in roles and role == 'fidget' and re.search(r'\bdeath|dying\b', text):
        role = 'dying'

    rec = {'role': role, 'roles': list(dict.fromkeys([role] + roles)), 'weapon': weapon, 'styles': styles}
    if m.get('error'):
        rec['tier'] = 'discard'
        rec['discard_reasons'] = ['unreadable: ' + m['error']]
        return rec

    # Motion facts.
    s = m['series']
    ref = standing_ref.get(src, 1.0)
    head = [h / ref for h in s['head_ratio']]
    head_med = sorted(head)[len(head) // 2]

    def posture_of(h):
        if h >= 0.88:
            return 'standing'
        if h >= 0.76:
            return 'stance'
        if h >= 0.56:
            return 'crouched'
        if h >= 0.33:
            return 'low'
        return 'lying'

    ankle = ANKLE_REF.get(src, min(s['feet_min']))
    airborne = sum(1 for f in s['feet_min'] if f > ankle + 0.3) / len(s['feet_min'])
    post = posture_of(head_med)
    if airborne > 0.85 and role not in ('dying', 'hit'):
        post = 'airborne'
    rec['posture'] = post
    rec['posture_start'] = posture_of(head[0])
    rec['posture_end'] = posture_of(head[-1])
    rec['airborne'] = round(airborne, 2)
    rec['head_ratio'] = round(head_med, 3)

    exc, net = m['root_excursion'], (m['root_net_fwd'] ** 2 + m['root_net_right'] ** 2) ** 0.5
    if exc < 0.35:
        root = 'in_place'
    elif role in ('walking', 'run', 'crawl', 'swim', 'fly') or exc < 1.2:
        root = 'root_motion' if exc >= 1.2 else 'drift'
    else:
        root = 'travel'
    rec['root'] = root
    rec['root_travel_legs'] = round(exc, 2)
    direction = 'none'
    if role in ('walking', 'run', 'crawl', 'fly', 'swim'):
        if re.search(r'\b(back|backward|backwards)\b', text):
            direction = 'back'
        elif re.search(r'\b(left|right|strafe|strafing|sideways|side)\b', text):
            direction = 'side'
        elif re.search(r'\b(arc|circle|turn|turning)\b', text):
            direction = 'arc'
        else:
            direction = 'forward'
        if root in ('root_motion', 'drift') and net > 0.8:
            fwd, right = m['root_net_fwd'], m['root_net_right']
            if abs(right) > abs(fwd) * 1.2:
                direction = 'side'
            elif fwd < 0:
                direction = 'back'
            elif direction == 'none':
                direction = 'forward'
    rec['direction'] = direction
    # Net facing change wrapped to +-180: a full spin ends facing the way it started.
    turn = (m['yaw_net_deg'] + 180.0) % 360.0 - 180.0
    rec['turn_deg'] = round(turn, 1)
    rec['loop'] = m['loop_err'] < 0.06
    rec['duration_s'] = m['duration_s']
    rec['frames'] = m['frames']
    rec['fps'] = m['fps']
    rec['static'] = m['activity'] < 0.002
    if role in ('attack_melee', 'attack_ranged', 'cast'):
        rec['impact_s'] = m['hand_peak_t']
    rec['feet_planted'] = m['foot_travel'] < 0.35

    # Motion-based discards.
    if rec['static'] and 'static_pose' not in discard and role not in ('dying',):
        discard.append('static')
    if role in ('turn',):
        discard.append('turn_in_place')
    if role == 'transition':
        discard.append('transition')
    if role == 'jump':
        discard.append('jump')
    if root == 'travel' and exc > 3.0 and role not in ('walking', 'run', 'crawl', 'fly', 'swim'):
        discard.append('travels')
    if abs(turn) > 50 and role not in ('dying', 'dodge', 'fall', 'swim', 'fly'):
        discard.append('turns')
    if role not in ('dying', 'hit', 'crawl', 'fall', 'fly', 'swim') and post == 'lying':
        discard.append('lying')
    if role not in ('dying', 'hit') and re.search(r'\b(sitting|seated|sit|laying|lying|kneel|kneeling|'
                                                 r'sleeping)\b', text):
        discard.append('sitting_lying_kneeling')
    if role == 'standing' and post in ('low', 'lying') and not re.search(r'\bcrouch\w*', text):
        discard.append('sitting_lying_kneeling')

    # Body suitability.
    body = ['humanoid']
    if any(x in styles for x in ('zombie', 'mutant', 'creature')):
        body.append('monster_humanoid')
    if role == 'fly' or (post == 'airborne' and role in ('standing', 'fall', 'fidget')):
        body.append('flyer')
    rec['body'] = body
    rec['gender'] = 'female' if 'female' in styles else 'neutral'

    discard = list(dict.fromkeys(discard))
    if discard:
        rec['tier'] = 'discard'
        rec['discard_reasons'] = discard
        return rec
    core = role in ENGINE_ROLES
    caveats = []
    if role in ('walking', 'run') and direction not in ('forward',):
        caveats.append('direction_' + direction)
    if role in ('standing', 'walking', 'run', 'fly') and not rec['loop']:
        caveats.append('not_loopable')
    if role in ('attack_melee', 'attack_ranged', 'cast', 'hit') and post in ('crouched', 'low'):
        caveats.append('crouched')
    if role in ('standing', 'walking', 'run', 'fidget') and (post in ('crouched', 'low') or
                                                             re.search(r'\bcrouch\w*', text)):
        caveats.append('crouched')
    if role == 'walking' and re.search(r'\bsteps?\b', text):
        caveats.append('single_step')
    if weapon == 'prop':
        caveats.append('prop')
    if rifle_pose:
        caveats.append('rifle_pose')
    if role == 'dying' and rec['posture_end'] not in ('lying', 'low'):
        caveats.append('ends_upright')
    if any(x in styles for x in ('drunk', 'capoeira', 'sad')):
        caveats.append('special_style')
    if root == 'travel' and not (role == 'dying' and exc <= 2.5):
        caveats.append('root_travel')
    if role in ('attack_melee', 'cast', 'attack_ranged', 'hit', 'fidget') and m['duration_s'] > 5.0:
        caveats.append('long')
    rec['caveats'] = caveats
    rec['tier'] = 'core' if core and not caveats else 'maybe'
    rec['score'] = score(rec, m)
    return rec


def score(rec, m):
    """Default ranking for an adult male humanoid MM actor (higher is better); see INDEX.md."""
    role, post = rec['role'], rec['posture']
    s = 50.0
    s += {'standing': 25, 'stance': 18, 'crouched': -5, 'low': -20, 'lying': -25, 'airborne': 0}.get(post, 0)
    if role == 'dying':
        s += 15 if rec['posture_end'] in ('lying', 'low') else -15
        s -= 10 * max(0.0, rec['root_travel_legs'] - 1.5)
    if role == 'fly':
        s += 25 if post == 'airborne' else -10
    if role in ('standing', 'walking', 'run', 'fly'):
        s += 12 if rec['loop'] else -12
    if role in ('walking', 'run'):
        s += 10 if rec['direction'] == 'forward' else -15
    if role in ('attack_melee', 'attack_ranged', 'cast', 'hit', 'dying', 'fidget', 'standing'):
        s += 8 if rec['root'] == 'in_place' else (0 if rec['root'] == 'drift' else -8)
    if role in ('attack_melee', 'cast', 'hit'):
        s += 8 if rec['feet_planted'] else -4
    span = {'attack_melee': (0.6, 2.2), 'attack_ranged': (0.6, 3.0), 'cast': (0.7, 3.0), 'hit': (0.3, 1.6),
            'dying': (1.0, 4.5), 'standing': (1.5, 10.0), 'fidget': (1.5, 7.0), 'walking': (0.6, 2.5),
            'run': (0.4, 1.6), 'fly': (0.8, 6.0)}.get(role)
    if span:
        d = rec['duration_s']
        s += 6 if span[0] <= d <= span[1] else -6
    styles = rec['styles']
    s -= 10 if 'female' in styles else 0
    s -= 8 if any(x in styles for x in ('drunk', 'injured', 'sad', 'capoeira', 'old')) else 0
    s -= 3 * len(rec.get('caveats', []))
    if abs(rec['turn_deg']) > 20 and role not in ('dying',):
        s -= 5
    return round(s, 1)


# ---------------------------------------------------------------------------------------------------------------
# Duplicates

def pose_diff(a, b):
    t = n = 0
    for k in ('head_ratio', 'hips_ratio', 'feet_min', 'yaw'):
        sc = 100.0 if k == 'yaw' else 1.0
        for x, y in zip(a['series'][k], b['series'][k]):
            t += abs(x - y) / sc
            n += 1
    return t / max(n, 1)


def prefer(clip):
    """Lower sorts first: single downloads over pack copies, then plain names, then shorter paths."""
    return (clip.get('pack') is not None, '(' in os.path.basename(clip['path']), len(clip['path']), clip['path'])


def find_duplicates(clips, metrics):
    """exact: identical sampled motion. root_motion_variant: a pack copy of an in-place single (same name and
    frame count, same body motion, only the hips travel differs)."""
    groups = collections.defaultdict(list)
    for c in clips:
        m = metrics.get(c['sha1'])
        if m and not m.get('error'):
            groups[(c['source'], m['motion_hash'])].append(c)
    for g in groups.values():
        g.sort(key=prefer)
        for dup in g[1:]:
            dup['duplicate_of'] = g[0]
            g[0].setdefault('duplicates', []).append(rel(dup['path']))
    by_key = collections.defaultdict(list)
    for c in clips:
        if c['source'] == 'mixamo' and 'duplicate_of' not in c:
            m = metrics.get(c['sha1'])
            if m and not m.get('error'):
                by_key[(c['name'].lower(), m['frames'])].append(c)
    for g in by_key.values():
        singles = [c for c in g if c.get('pack') is None]
        packs = [c for c in g if c.get('pack') is not None]
        for p in packs:
            best, bd = None, 1.0
            for s in singles:
                d = pose_diff(metrics[p['sha1']], metrics[s['sha1']])
                if d < bd:
                    best, bd = s, d
            if best is None or bd > 0.02:
                continue
            pm, sm = metrics[p['sha1']], metrics[best['sha1']]
            if pm['root_excursion'] > sm['root_excursion'] + 0.5:
                if 'root_motion_file' not in best:
                    best['root_motion_file'] = p
                    p['variant_of'] = best
                else:
                    p['duplicate_of'] = best
                    best.setdefault('duplicates', []).append(rel(p['path']))
            else:
                p['duplicate_of'] = best
                best.setdefault('duplicates', []).append(rel(p['path']))
        # Pack copies of pack-only clips that differ only by pack.
    return


# ---------------------------------------------------------------------------------------------------------------
# Build

def clip_id(clip, m):
    prefix = {'mixamo': 'mx', 'humanoid_set': 'hs', 'meshy': 'me'}[clip['source']]
    slug = re.sub(r'[^a-z0-9]+', '_', clip['name'].lower()).strip('_')[:48]
    return '%s/%s_%s' % (prefix, slug, (m.get('motion_hash') or clip['sha1'])[:6])


def build(jobs, dry_run):
    clips = collect_sources()
    metrics = load_metrics()
    for c in clips:
        c['sha1'] = sha1_file(c['path'])
    measure_missing({c['sha1']: c['path'] for c in clips}, metrics, jobs)
    # Pack characters (skinned meshes) are not clips.
    keep = []
    for c in clips:
        m = metrics.get(c['sha1'], {})
        if c['source'] == 'mixamo' and m.get('has_mesh'):
            dst = os.path.join(CHARACTERS, re.sub(r'[^a-z0-9]+', '_', c['name'].lower()).strip('_') + '.fbx')
            if not dry_run:
                os.makedirs(CHARACTERS, exist_ok=True)
                if os.path.exists(dst):
                    os.remove(c['path'])
                else:
                    os.replace(c['path'], dst)
            continue
        keep.append(c)
    clips = keep
    match_catalogue(clips, metrics)
    find_duplicates(clips, metrics)

    # Standing reference per rig: median head height over plain standing idles.
    refs = collections.defaultdict(list)
    for c in clips:
        m = metrics.get(c['sha1'], {})
        t = norm_text(c['name'])
        if not m.get('error') and re.search(r'\bidle\b', t) and \
                not re.search(r'crouch|sit|kneel|lay|lying|prone|crawl|swim|climb|hang|ledge|fall', t):
            refs[c['source']].append(m['head_ratio']['median'])
    standing_ref = {k: sorted(v)[len(v) // 2] for k, v in refs.items() if v}
    standing_ref.setdefault('meshy', 1.0)

    removed = load_json(REMOVED, {})
    entries = []
    moves = []
    for c in clips:
        m = metrics.get(c['sha1'], {})
        if 'duplicate_of' in c:
            if c['source'] == 'mixamo':
                removed[c['sha1']] = rel(c['duplicate_of']['path'])
                moves.append((c['path'], None))
            continue
        if 'variant_of' in c:
            continue
        rec = classify(c, m, standing_ref)
        entry = {'id': clip_id(c, m), 'source': c['source'], 'name': c['name']}
        if c.get('descriptions'):
            entry['description'] = c['descriptions'][0] if len(c['descriptions']) == 1 else c['descriptions']
        entry.update(rec)
        # File placement: Mixamo discards live in mixamo/_discarded/, everything else in place.
        path = c['path']
        if c['source'] == 'mixamo':
            want = target_path(path, rec['tier'] == 'discard')
            if want != path:
                moves.append((path, want))
                path = want
            rm = c.get('root_motion_file')
            if rm:
                rm_want = target_path(rm['path'], rec['tier'] == 'discard')
                if rm_want != rm['path']:
                    moves.append((rm['path'], rm_want))
                entry['files'] = {'in_place': rel(path), 'root_motion': rel(rm_want)}
            entry['file'] = rel(path)
            if c.get('pack'):
                entry['pack'] = c['pack']
            if c.get('catalogue'):
                entry['catalogue'] = c['catalogue']
        elif c['source'] == 'humanoid_set':
            entry['file'] = rel(path)
            set_glb = os.path.join(LIB, 'humanoid_set', c['set'] + '.glb')
            clip_name = re.sub(r'[^A-Za-z0-9]', '', base_name(path))
            entry['files'] = {'root_motion': rel(path)}
            if os.path.exists(set_glb):
                entry['files']['in_place_glb'] = rel(set_glb)
                entry['glb_clip'] = clip_name
            entry['set'] = c['set']
        else:
            entry['file'] = rel(path)
            if c.get('action_id') is not None:
                entry['meshy_action_id'] = c['action_id']
        if c.get('duplicates'):
            entry['duplicates_removed'] = len(c['duplicates'])
        entries.append(entry)

    if dry_run:
        report(entries, standing_ref, removed, dry=True)
        return
    for src, dst in moves:
        if dst is None:
            if os.path.exists(src):
                os.remove(src)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(src, unique_path(dst) if os.path.exists(dst) else dst)
    prune_empty_dirs(MIXAMO)
    write_json(REMOVED, removed)
    entries.sort(key=lambda e: (e['tier'] != 'core', e['tier'] == 'discard', e['role'], -e.get('score', 0), e['id']))
    write_json(INDEX, {'version': 1, 'standing_ref': standing_ref, 'roles': ENGINE_ROLES + EXTRA_ROLES,
                       'clips': entries})
    report(entries, standing_ref, removed, dry=False)


def target_path(path, discard):
    r = os.path.relpath(path, MIXAMO)
    inside = r.startswith('_discarded' + os.sep)
    if discard and not inside:
        return os.path.join(DISCARDED, r)
    if not discard and inside:
        return os.path.join(MIXAMO, r[len('_discarded') + 1:])
    return path


def prune_empty_dirs(top):
    for root, dirs, files in os.walk(top, topdown=False):
        if root != top and not os.listdir(root):
            os.rmdir(root)


def report(entries, standing_ref, removed, dry):
    tiers = collections.Counter((e['source'], e['tier']) for e in entries)
    print('standing reference', standing_ref)
    for src in ('mixamo', 'humanoid_set', 'meshy'):
        print('%-13s core %4d  maybe %4d  discard %4d' % (src, tiers[(src, 'core')], tiers[(src, 'maybe')],
                                                          tiers[(src, 'discard')]))
    print('duplicates removed (all time):', len(removed))
    if not dry:
        write_markdown(entries, standing_ref, removed)
        print('wrote', rel(INDEX), 'and', rel(INDEX_MD))


def write_markdown(entries, standing_ref, removed):
    tiers = collections.Counter((e['source'], e['tier']) for e in entries)
    reasons = collections.Counter(r for e in entries for r in e.get('discard_reasons', []))
    roles = collections.Counter((e['role'], e['tier']) for e in entries)
    lines = ['# Animation library index', '',
             'Generated by `level_generation/creatures/claude_shared/anim_library/build_anim_index.py build`; do not '
             'edit by hand. Data: `index.json` (one entry per unique clip). Query it with',
             '`build_anim_index.py find --role attack_melee --weapon unarmed --top 20`.', '',
             '| Source | Core | Maybe | Discard |', '|---|---|---|---|']
    for src in ('mixamo', 'humanoid_set', 'meshy'):
        lines.append('| %s | %d | %d | %d |' % (src, tiers[(src, 'core')], tiers[(src, 'maybe')],
                                                tiers[(src, 'discard')]))
    lines += ['', 'Duplicates removed from `mixamo/` (identical motion or pack copies): %d. Pack copies that only '
              'add root travel are kept as `files.root_motion` of their in-place clip.' % len(removed), '',
              '## Tiers', '',
              '- **core**: fits an engine clip role (%s) cleanly: standing or combat stance, in place or strippable '
              'travel, forward locomotion that loops.' % ', '.join(ENGINE_ROLES),
              '- **maybe**: usable with a caveat (`caveats`: backward/side locomotion, crouched, not loopable, drunk '
              'or other special style, long) or a role the engine does not play yet (block, dodge, talk, NPC work, '
              'crawl, swim, fall).',
              '- **discard**: never fits MM6–MM8 actors (`discard_reasons`); Mixamo discards are moved to '
              '`mixamo/_discarded/`.', '',
              'Discard reasons: ' + ', '.join('%s %d' % kv for kv in reasons.most_common()), '',
              '## Fields', '',
              '- `role` (primary) and `roles`; `weapon` (unarmed, sword_1h, sword_shield, sword_2h, axe, club, spear, '
              'staff, dagger, bow, crossbow, torch, one_handed, prop); `styles` (female, zombie, mutant, creature, '
              'injured, drunk, sneak, combat, casual, magic, capoeira, boxing, ...); `body` (humanoid, '
              'monster_humanoid, flyer).',
              '- `posture`: median head height against the rig\'s standing idle: standing (>= 0.88), stance '
              '(0.76–0.88, combat crouch), crouched, low, lying, airborne (feet off the floor for most of the clip); '
              '`posture_start`/`posture_end`.',
              '- `root`: in_place (hips travel < 0.35 leg lengths), drift (< 1.2), root_motion (locomotion with '
              'travel to strip and use as stride), travel (one-shot that moves the body; discarded except deaths '
              'and dodges). `direction` for locomotion. `turn_deg` net facing change.',
              '- `loop`, `duration_s`, `frames`, `fps`, `impact_s` (hand speed peak of attacks and casts: a release '
              'hint), `feet_planted`, `score` (default ranking for an adult male humanoid: standing posture, in '
              'place, planted feet, role-typical duration, loopable locomotion; female/special styles rank lower).',
              '- `file` (clip file), `files.in_place`/`files.root_motion` (Mixamo pack copies with travel), '
              '`files.in_place_glb` + `glb_clip` (humanoid set: per-clip FBX carry root motion, the set GLB is in '
              'place), `catalogue.preview_gif` (Mixamo preview; `match` unique/ambiguous by name and frame count).',
              '', 'Ratios are measured, not hand-checked: always preview a clip before using it.', '',
              '## Core and maybe counts by role', '', '| Role | Core | Maybe |', '|---|---|---|']
    for r in ENGINE_ROLES + EXTRA_ROLES:
        if roles[(r, 'core')] or roles[(r, 'maybe')]:
            lines.append('| %s | %d | %d |' % (r, roles[(r, 'core')], roles[(r, 'maybe')]))
    lines += ['', '## Top core candidates per role', '',
              'Best eight per source by the default male-humanoid ranking; filter with `find` for weapons, styles or '
              'other bodies.', '']
    for r in ENGINE_ROLES:
        top = []
        for src in ('mixamo', 'humanoid_set', 'meshy'):
            top += sorted((e for e in entries if e['role'] == r and e['tier'] == 'core' and e['source'] == src),
                          key=lambda e: -e['score'])[:8]
        if not top:
            continue
        lines.append('### %s' % r)
        lines.append('')
        lines.append('| Score | Id | Weapon | Posture | Root | Dur | Styles |')
        lines.append('|---|---|---|---|---|---|---|')
        for e in top:
            lines.append('| %s | `%s` | %s | %s | %s | %.2f | %s |' % (
                e['score'], e['id'], e['weapon'] or '', e['posture'], e['root'], e['duration_s'],
                ', '.join(e['styles'])))
        lines.append('')
    open(INDEX_MD, 'w').write('\n'.join(lines) + '\n')


# ---------------------------------------------------------------------------------------------------------------
# Query

def find(args):
    data = load_json(INDEX, None)
    if not data:
        sys.exit('no index; run build first')
    out = []
    for e in data['clips']:
        if args.tier != 'any' and e['tier'] != args.tier and not (args.tier == 'usable' and e['tier'] != 'discard'):
            continue
        if args.role and args.role not in e.get('roles', []):
            continue
        if args.weapon and (e.get('weapon') or 'unarmed') != args.weapon:
            continue
        if args.posture and e.get('posture') != args.posture:
            continue
        if args.style and args.style not in e.get('styles', []):
            continue
        if args.no_style and args.no_style in e.get('styles', []):
            continue
        if args.source and e['source'] != args.source:
            continue
        if args.body and args.body not in e.get('body', []):
            continue
        if args.text and args.text.lower() not in (e['name'] + ' ' + str(e.get('description', ''))).lower():
            continue
        if args.loop and not e.get('loop'):
            continue
        if args.in_place and e.get('root') != 'in_place':
            continue
        out.append(e)
    out.sort(key=lambda e: -e.get('score', 0))
    out = out[:args.top]
    if args.json:
        print(json.dumps(out, indent=1))
        return
    for e in out:
        print('%5s  %-46s %-6s %-13s %-9s %-11s %5.2fs %s  %s' % (
            e.get('score', ''), e['id'], e['tier'], e.get('weapon') or '-', e.get('posture', '-'),
            e.get('root', '-'), e.get('duration_s', 0), ','.join(e.get('styles', [])), e['file']))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('import-mixamo')
    p.add_argument('dirs', nargs='+')
    p = sub.add_parser('build')
    p.add_argument('--jobs', type=int, default=12)
    p.add_argument('--dry-run', action='store_true')
    p = sub.add_parser('find')
    p.add_argument('--role')
    p.add_argument('--weapon')
    p.add_argument('--posture')
    p.add_argument('--tier', default='core', help='core, maybe, discard, usable (core+maybe) or any')
    p.add_argument('--style')
    p.add_argument('--no-style')
    p.add_argument('--source')
    p.add_argument('--body')
    p.add_argument('--text')
    p.add_argument('--loop', action='store_true')
    p.add_argument('--in-place', action='store_true')
    p.add_argument('--top', type=int, default=25)
    p.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'import-mixamo':
        import_mixamo([os.path.expanduser(d) for d in a.dirs])
    elif a.cmd == 'build':
        build(a.jobs, a.dry_run)
    else:
        find(a)


main()
