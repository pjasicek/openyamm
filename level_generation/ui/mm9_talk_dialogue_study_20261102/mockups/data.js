// Real MM9 RUDE dialogue states for the three proposals (assets_dev/worlds/mm9/dialogue/rude/).
// Prompts and responses are verbatim, including MM9's double spaces after full stops (the renderer collapses them).
// Row marks are the proposed presentation states: visited (chosen before), new (a quest-key row not chosen yet),
// service (a RUDE service opcode), locked (a service the party cannot use yet), exit (next = -1).
const STATES = {
  // Typical: an entry node, a short top blurb and four choices (p90 of choices per node is 4).
  typical: {
    npc: 'Bjarni Thorvaldssen', place: 'Sturmford', source: 'NPC45.rude, node 45 (TOPBLURB 45)',
    portrait: 'assets/portrait_bjarni.png',
    echo: null,
    text: 'Greetings, adventurers.  What can I do for you?',
    hot: 1,
    choices: [
      {t: 'Is there anything we can do for you?', s: 'visited'},
      {t: "We've rescued Ivsar.", s: 'new'},
      {t: 'About those things you asked us to do..', s: 'visited'},
      {t: 'Sorry to bother you.', exit: true},
    ],
    log: [
      {who: 'npc', t: 'Greetings, adventurers.  What can I do for you?'},
    ],
  },
  // Most choices at once: ten rows of Sven's entry node whose quest keys do not exclude each other
  // (the measured maximum; 14 rows exist, but no state shows all of them).
  many: {
    npc: 'Sven Forkbeard', place: 'Thjorgard', source: 'NPC3.rude, node 3, slots 1 2 5 6 8 9 11 13 15 16',
    portrait: null,
    echo: null,
    text: 'Well met, friends.  What may I do for you?',
    hot: 4,
    choices: [
      {t: "We've come to speak to you about Tamur Leng.", s: 'visited'},
      {t: "We'd like to ask you some questions.", s: 'visited'},
      {t: "We've retrieved Thjorad.", s: 'new'},
      {t: 'Your mine is once again producing Thjorad', s: 'new'},
      {t: 'The Clans have been united.  It is time for the war council.', s: 'new'},
      {t: 'Sven!  It is good to see you!'},
      {t: 'We have found a disturbing letter that you need to read.', s: 'new'},
      {t: 'Harris Willington is the accountant at the General Store.', s: 'new'},
      {t: 'Sven.  It is our fault you are dead.'},
      {t: 'Sorry to bother you.  Goodbye.', exit: true},
    ],
    log: [
      {who: 'npc', t: 'Well met, friends.  What may I do for you?'},
    ],
  },
  // Longest NPC line in MM9 (254 characters) after a choice, then the entry node's choices again.
  long: {
    npc: 'Keith Bloodaxe', place: 'Drangheim', source: 'NPC89.rude, node 10 slot 1 -> node 89 (after the task was accepted, key 128)',
    portrait: null,
    echo: 'What was the task again?',
    text: 'As you may have heard from the villagers, just outside of Drangheim there is a gang known as the Yobboe Gang.  '
      + 'They have been extorting money from the villagers nearby.  Go to the Yobboe camp, defeat the bandits, and return '
      + "the villagers' things to them.",
    hot: 2,
    choices: [
      {t: 'We would like to ask you some questions.', s: 'visited'},
      {t: 'About that promotion quest.', s: 'visited'},
      {t: 'We have completed the task.', s: 'new'},
      {t: 'Thanks for your time.', exit: true},
    ],
    // This conversation so far: the entry blurb, "About that promotion quest." (node 89 slot 3) and node 10.
    log: [
      {who: 'npc', t: 'What do you want?'},
      {who: 'party', t: 'About that promotion quest.'},
      {who: 'npc', t: 'Yes?'},
      {who: 'party', t: 'What was the task again?'},
    ],
  },
  // Services: a skill trainer (skill_trainers.txt: Expert needs rank 4, Master rank 7, no gold).
  service: {
    npc: 'Hrapp Tjorvissen', place: 'Guberland', source: 'NPC174.rude, node 174; skill_trainers.txt rows 174/1, 174/3',
    portrait: null,
    echo: null,
    text: 'Hello.',
    hot: 0,
    choices: [
      {t: "We'd like to become Experts in Meditation.", service: 'Train', note: 'Expert'},
      {t: "We'd like to become Masters in Meditation.", locked: 'needs Meditation 7', note: 'Master'},
      {t: "We'd like to ask you some questions.", s: 'visited'},
      {t: 'Sorry to bother you.', exit: true},
    ],
    log: [
      {who: 'npc', t: 'Hello.'},
    ],
  },
};

const params = new URLSearchParams(location.search);
const stateName = params.get('state') || 'typical';
const state = STATES[stateName] || STATES.typical;
const stageWidth = Number(params.get('w') || 1600);
const touch = params.get('touch') === '1';

// MM9 text uses two spaces after a full stop; HTML collapses them as the proposed renderer would.
function clean(text)
{
  return text.replace(/\s{2,}/g, ' ');
}

function initials(name)
{
  return name.split(/\s+/).map((part) => part[0]).join('').slice(0, 2);
}

function setupStage()
{
  const stage = document.getElementById('stage');
  stage.style.width = stageWidth + 'px';
  stage.style.backgroundImage = `url(assets/backdrop_${stageWidth}x900.jpg)`;
  document.body.classList.toggle('touch', touch);
  document.body.dataset.state = stateName;
  return stage;
}

// Numbered choices: 1-9 then 0; the exit row takes Esc.
function keyLabel(choice, index)
{
  if (choice.exit)
  {
    return 'Esc';
  }
  return index < 9 ? String(index + 1) : '0';
}

function choiceHtml(choice, index, hot)
{
  const classes = ['choice'];
  if (choice.s) classes.push(choice.s);
  if (choice.exit) classes.push('exit');
  if (choice.locked) classes.push('locked');
  if (index === hot) classes.push('hot');
  const mark = choice.s === 'new' ? '<i class="mark new" title="new"></i>'
    : choice.s === 'visited' ? '<i class="mark seen" title="asked before"></i>'
      : choice.exit ? '<i class="mark door"></i>' : '<i class="mark"></i>';
  let tag = '';
  if (choice.service) tag = `<span class="tag svc">${choice.service}${choice.note ? ' · ' + choice.note : ''}</span>`;
  if (choice.locked) tag = `<span class="tag lock">${choice.note ? choice.note + ' · ' : ''}${choice.locked}</span>`;
  return `<div class="${classes.join(' ')}"><span class="key">${keyLabel(choice, index)}</span>${mark}`
    + `<span class="t">${clean(choice.t)}</span>${tag}</div>`;
}

function portraitHtml(extraClass)
{
  if (state.portrait)
  {
    return `<div class="portrait ${extraClass || ''}"><img src="${state.portrait}" alt=""></div>`;
  }
  return `<div class="portrait mono ${extraClass || ''}"><span>${initials(state.npc)}</span></div>`;
}
