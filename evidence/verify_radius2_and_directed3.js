// Exact verifier for the HCP-001 fixed candidate and its full radius-2 edge-flip ball.
// Node.js, standard library only. Vertices are 0..42.
'use strict';

const N = 43;
const E = N * (N - 1) / 2;
const M = 962598; // C(43,5)
const PER_EDGE = 10660; // C(41,3)
const S = new Set([1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21]);
const deletedCycleEdges = new Set([
  '3-4', '4-5', '5-6', '6-7',
  '11-12', '12-13', '13-14', '14-15',
  '20-21', '21-22', '22-23', '23-24',
  '29-30', '30-31', '31-32',
  '37-38', '38-39', '39-40', '40-41',
]);

function edgeId(a, b) {
  if (a > b) [a, b] = [b, a];
  return a * (2 * N - a - 1) / 2 + (b - a - 1);
}
function bad(c) { return c === 0 || c === 10 ? 1 : 0; }

const ends = new Array(E);
const state = new Uint8Array(E);
for (let a = 0; a < N; a++) for (let b = a + 1; b < N; b++) {
  const id = edgeId(a, b), d = b - a;
  ends[id] = [a, b];
  state[id] = ((S.has(d) || S.has(N - d)) && !deletedCycleEdges.has(`${a}-${b}`)) ? 1 : 0;
}

const incidence = new Uint32Array(E * PER_EDGE);
const subsetEdges = new Uint16Array(M * 10);
const fill = new Uint16Array(E);
const counts = new Uint8Array(M);
const vertices = new Uint8Array(M * 5);
let qi = 0;
for (let a = 0; a < N - 4; a++)
for (let b = a + 1; b < N - 3; b++)
for (let c = b + 1; c < N - 2; c++)
for (let d = c + 1; d < N - 1; d++)
for (let e = d + 1; e < N; e++) {
  const v = [a, b, c, d, e];
  for (let k = 0; k < 5; k++) vertices[qi * 5 + k] = v[k];
  let ec = 0, ek = 0;
  for (let x = 0; x < 4; x++) for (let y = x + 1; y < 5; y++) {
    const id = edgeId(v[x], v[y]);
    subsetEdges[qi * 10 + ek++] = id;
    ec += state[id];
    incidence[id * PER_EDGE + fill[id]++] = qi;
  }
  counts[qi++] = ec;
}
if (qi !== M) throw new Error(`enumerated ${qi}, expected ${M}`);

let baseF = 0, baseK = 0, baseI = 0;
const witnesses = [];
for (let q = 0; q < M; q++) if (bad(counts[q])) {
  baseF++;
  if (counts[q] === 10) baseK++; else baseI++;
  witnesses.push(Array.from(vertices.slice(q * 5, q * 5 + 5)));
}

const singleDelta = new Int32Array(E);
let min1 = Infinity, countMin1 = 0;
for (let id = 0; id < E; id++) {
  const step = state[id] ? -1 : 1;
  let delta = 0, off = id * PER_EDGE;
  for (let k = 0; k < PER_EDGE; k++) {
    const c = counts[incidence[off + k]];
    delta += bad(c + step) - bad(c);
  }
  singleDelta[id] = delta;
  const f = baseF + delta;
  if (f < min1) { min1 = f; countMin1 = 1; }
  else if (f === min1) countMin1++;
}

// Intersect the two sorted incidence lists. The correction makes the sum of
// single-edge deltas exact when both flips affect the same five-set.
let min2 = Infinity, countMin2 = 0;
const minPairs = [];
for (let x = 0; x < E - 1; x++) for (let y = x + 1; y < E; y++) {
  const sx = state[x] ? -1 : 1, sy = state[y] ? -1 : 1;
  let correction = 0, i = 0, j = 0;
  const ox = x * PER_EDGE, oy = y * PER_EDGE;
  while (i < PER_EDGE && j < PER_EDGE) {
    const qx = incidence[ox + i], qy = incidence[oy + j];
    if (qx < qy) i++;
    else if (qy < qx) j++;
    else {
      const c = counts[qx];
      correction += bad(c + sx + sy) - bad(c + sx) - bad(c + sy) + bad(c);
      i++; j++;
    }
  }
  const f = baseF + singleDelta[x] + singleDelta[y] + correction;
  if (f < min2) {
    min2 = f; countMin2 = 1; minPairs.length = 0;
    minPairs.push([ends[x], ends[y]]);
  } else if (f === min2) {
    countMin2++;
    if (minPairs.length < 20) minPairs.push([ends[x], ends[y]]);
  }
}

// Directed three-flip repair neighborhood used in the exploratory report:
// (1) add a missing edge of either original I5;
// (2) delete a present edge of a K5 created after (1), other than (1);
// (3) toggle an edge belonging to a violation remaining after (2), distinct
//     from the first two edges. This is not the full radius-3 Hamming sphere.
const firstEdges = new Set();
for (const v of witnesses) for (let i = 0; i < 4; i++) for (let j = i + 1; j < 5; j++) {
  const id = edgeId(v[i], v[j]);
  if (!state[id]) firstEdges.add(id);
}
let repairMin = Infinity, repairTrajectories = 0;
const repairTerminals = new Set(), repairMinExamples = [];
function applyFlip(id) {
  const step = state[id] ? -1 : 1, off = id * PER_EDGE;
  state[id] ^= 1;
  for (let k = 0; k < PER_EDGE; k++) counts[incidence[off + k]] += step;
}
for (const add of firstEdges) {
  applyFlip(add);
  const removable = new Set();
  for (let q = 0; q < M; q++) if (counts[q] === 10) {
    for (let k = 0; k < 10; k++) {
      const id = subsetEdges[q * 10 + k];
      if (id !== add && state[id]) removable.add(id);
    }
  }
  for (const remove of removable) {
    applyFlip(remove);
    let f2 = 0;
    const third = new Set();
    for (let q = 0; q < M; q++) if (bad(counts[q])) {
      f2++;
      for (let k = 0; k < 10; k++) {
        const id = subsetEdges[q * 10 + k];
        if (id !== add && id !== remove) third.add(id);
      }
    }
    for (const id of third) {
      const step = state[id] ? -1 : 1, off = id * PER_EDGE;
      let delta = 0;
      for (let k = 0; k < PER_EDGE; k++) {
        const c = counts[incidence[off + k]];
        delta += bad(c + step) - bad(c);
      }
      const f = f2 + delta;
      repairTrajectories++;
      const tri = [add, remove, id].sort((a, b) => a - b);
      repairTerminals.add(tri[0] * E * E + tri[1] * E + tri[2]);
      if (f < repairMin) {
        repairMin = f; repairMinExamples.length = 0;
        repairMinExamples.push([ends[add], ends[remove], ends[id]]);
      } else if (f === repairMin && repairMinExamples.length < 20) {
        repairMinExamples.push([ends[add], ends[remove], ends[id]]);
      }
    }
    applyFlip(remove);
  }
  applyFlip(add);
}

console.log(JSON.stringify({
  candidate: { edges: state.reduce((a, b) => a + b, 0), K5: baseK, I5: baseI, F: baseF, witnesses },
  radius0: { graphs: 1, minimumF: baseF },
  radius1: { graphs: E, minimumF: min1, minimizers: countMin1 },
  radius2: { graphs: E * (E - 1) / 2, minimumF: min2, minimizers: countMin2, firstMinimizingPairs: minPairs },
  wholeBall: { graphs: 1 + E + E * (E - 1) / 2, minimumF: Math.min(baseF, min1, min2) },
  directedThreeFlipRepair: {
    definition: 'add edge in original I5; delete edge in resulting K5; flip edge in remaining violation',
    firstChoices: firstEdges.size,
    trajectories: repairTrajectories,
    distinctTerminalGraphs: repairTerminals.size,
    minimumF: repairMin,
    firstMinimizingTrajectories: repairMinExamples,
  },
}, null, 2));
