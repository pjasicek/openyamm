// All geometry uses the unchanged 1024 x 1536 painted master's coordinates.
// Integrate horizontal slices as a solid of revolution, then invert the resulting
// volume tables. Equal height changes do not transfer equal amounts of sand.
const width = 1024;
const height = 1536;
const sliceHeight = 2;
const sliceCount = height / sliceHeight;
const tableSteps = 512;

const glass = [
  ['M', 366, 332], ['Q', 512, 351, 663, 332],
  ['C', 699, 368, 718, 419, 710, 482], ['C', 700, 553, 652, 609, 594, 656],
  ['C', 552, 690, 532, 709, 528, 734], ['C', 531, 759, 555, 785, 594, 816],
  ['C', 661, 870, 704, 936, 713, 1002], ['C', 723, 1071, 701, 1135, 670, 1167],
  ['Q', 512, 1206, 351, 1167], ['C', 321, 1138, 303, 1074, 314, 1006],
  ['C', 324, 937, 367, 873, 428, 822], ['C', 469, 787, 493, 760, 494, 734],
  ['C', 492, 710, 468, 686, 429, 656], ['C', 368, 607, 321, 547, 313, 481],
  ['C', 305, 420, 325, 367, 366, 332], ['Z']
];
const path = commands => commands.map(command => command.join(' ')).join(' ');
export const glassPath = path(glass);

export function chamber(turns) {
  return turns % 2
    ? {neck: height - 734, bottom: height - 330}
    : {neck: 734, bottom: 1186};
}

export function mound(turns, fillHeight, heapCorrection = heapCorrections[turns]) {
  const c = chamber(turns);
  const totalHeight = (c.bottom - c.neck) * fillHeight;
  // Near full, the larger bulb needs a steeper heap to hold the shared amount
  // while still reaching the neck. After inversion, no sand is left suspended.
  const heapHeight = Math.min(totalHeight,
    180 * Math.pow(fillHeight, .56) + heapCorrection * Math.pow(fillHeight, 4));
  const radius = 350 * Math.pow(fillHeight, .56);
  const tip = Math.min(18, radius * .2);
  const top = c.bottom - totalHeight;
  const level = top + heapHeight;
  const commands = fillHeight <= 0 ? [] : [
    ['M', 512 - radius, level],
    ['C', 512 - radius * .59, level - heapHeight * .15,
      512 - tip * 3, top + heapHeight * .18, 512 - tip, top + 3],
    ['Q', 512, top - 2, 512 + tip, top + 3],
    ['C', 512 + tip * 3, top + heapHeight * .18,
      512 + radius * .62, level - heapHeight * .12, 512 + radius, level],
    ['L', 512 + radius, c.bottom + 40], ['L', 512 - radius, c.bottom + 40], ['Z']
  ];
  const crest = fillHeight <= 0 ? '' : `M${512-tip} ${top+3}Q512 ${top-2} ${512+tip} ${top+3}
    C${512+radius*.2} ${top+heapHeight*.3} ${512+radius*.52} ${level-heapHeight*.18} ${512+radius*.73} ${level}
    C${512+radius*.29} ${level-heapHeight*.08} ${512-radius*.1} ${top+heapHeight*.22} ${512-tip} ${top+3}Z`;
  return {commands, d: path(commands), crest, top};
}

// Flatten the very same curves that SVG draws; no separately approximated bulb shape.
function outline(commands) {
  const points = [];
  for (const [command, ...values] of commands) {
    if (command === 'Z') {
      points.push(points[0]);
    } else if (command === 'M' || command === 'L') {
      points.push(values);
    } else {
      const start = points.at(-1);
      for (let i = 1; i <= 32; ++i) {
        const t = i / 32, s = 1 - t;
        points.push([0, 1].map(axis => command === 'Q'
          ? s*s*start[axis] + 2*s*t*values[axis] + t*t*values[axis+2]
          : s*s*s*start[axis] + 3*s*s*t*values[axis] + 3*s*t*t*values[axis+2] + t*t*t*values[axis+4]));
      }
    }
  }
  return points;
}

function scanlines(points) {
  const rows = Array.from({length: sliceCount}, () => []);
  for (let i = 1; i < points.length; ++i) {
    const [x0, y0] = points[i-1], [x1, y1] = points[i];
    const begin = Math.max(0, Math.ceil(Math.min(y0, y1) / sliceHeight - .5));
    const end = Math.min(sliceCount, Math.ceil(Math.max(y0, y1) / sliceHeight - .5));
    for (let row = begin; row < end; ++row) {
      const y = (row + .5) * sliceHeight;
      rows[row].push(x0 + (y-y0) / (y1-y0) * (x1-x0));
    }
  }
  for (const row of rows) row.sort((a, b) => a-b);
  return rows;
}

const glassOutline = outline(glass);
const glassRows = [scanlines(glassOutline),
  scanlines(glassOutline.map(([x, y]) => [width-x, height-y]))];

export function pileVolumes(turns, fillHeight, heapCorrection = heapCorrections[turns]) {
  const sandRows = scanlines(outline(mound(turns, fillHeight, heapCorrection).commands));
  return Float64Array.from(sandRows, (sand, row) => {
    const wall = glassRows[turns % 2][row];
    let volume = 0;
    for (let s = 0; s < sand.length; s += 2) {
      for (let g = 0; g < wall.length; g += 2) {
        const left = Math.max(sand[s], wall[g]) - width/2;
        const right = Math.min(sand[s+1], wall[g+1]) - width/2;
        // Average the two radial halves. This also handles the curved end caps.
        if (right > left) volume += (right*Math.abs(right) - left*Math.abs(left)) / 2;
      }
    }
    return volume * Math.PI * sliceHeight;
  });
}

const sum = values => values.reduce((total, value) => total+value, 0);
export const measurePile = (turns, fillHeight, heapCorrection) => sum(pileVolumes(turns, fillHeight, heapCorrection));

// The painted bulbs are slightly different sizes. Use one shared amount that fits
// either bulb, instead of creating/destroying sand each time the glass turns over.
const originalVolumes = [0, 1].map(turns => measurePile(turns, 1, 0));
export const totalVolume = Math.min(...originalVolumes);
const heapCorrections = [0, 1].map(turns => {
  if (originalVolumes[turns] === totalVolume) return 0;
  let low = 0, high = chamber(turns).bottom-chamber(turns).neck-180;
  for (let i = 0; i < 40; ++i) {
    const mid = (low+high)/2;
    if (measurePile(turns, 1, mid) > totalVolume) low = mid;
    else high = mid;
  }
  return (low+high)/2;
});
const tables = [0, 1].map(turns => Float64Array.from({length: tableSteps+1},
  (_, i) => measurePile(turns, i/tableSteps)));

function lowerBound(values, target) {
  let low = 0, high = values.length-1;
  while (low < high) {
    const mid = Math.floor((low+high)/2);
    if (values[mid] < target) low = mid+1;
    else high = mid;
  }
  return low;
}

function heightForVolume(turns, target) {
  if (target <= 0) return 0;
  const table = tables[turns];
  const high = lowerBound(table, target), low = high-1;
  return (low + (target-table[low])/(table[high]-table[low])) / tableSteps;
}

const upperCumulative = [0, 1].map(turns => {
  const volumes = pileVolumes(1-turns, 1).reverse();
  const cumulative = [0];
  for (const volume of volumes) cumulative.push(cumulative.at(-1) + volume);
  return cumulative;
});

export function sandState(turns, progress) {
  const p = Math.max(0, Math.min(1, progress));
  const fillHeight = p === 1 ? 1 : heightForVolume(turns, p*tables[turns].at(-1));
  const cumulative = upperCumulative[turns];
  const target = p*cumulative.at(-1);
  const high = lowerBound(cumulative, target), low = high-1;
  const cutLevel = p === 0 ? 0 : p === 1 ? height
    : sliceHeight * (low + (target-cumulative[low])/(cumulative[high]-cumulative[low]));
  return {lower: mound(turns, fillHeight), upper: mound(1-turns, 1),
    fillHeight, upperCut: cutLevel};
}
