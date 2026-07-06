/**
 * Planet Texture Generator Module
 * Generates procedural planet textures using 3D simplex noise heightmaps + color ramps.
 * Usage: import { generatePlanetTexture } from '/static/planet_textures.js';
 *        const texture = generatePlanetTexture(THREE, planetId, planetType);
 */

// 3D Simplex Noise
class PlanetNoise {
  constructor(seed) {
    this.perm = new Uint8Array(512);
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    let s = seed || 0;
    const rng = () => { s = (s * 1664525 + 1013904223) & 0xFFFFFFFF; return (s >>> 0) / 4294967296; };
    for (let i = 255; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [p[i], p[j]] = [p[j], p[i]]; }
    for (let i = 0; i < 512; i++) this.perm[i] = p[i & 255];
    this.g3 = [[1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],[1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],[0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]];
  }
  dot3(g, x, y, z) { return g[0]*x + g[1]*y + g[2]*z; }
  n3(x, y, z) {
    const F = 1/3, G = 1/6;
    const s2 = (x + y + z) * F;
    const i = Math.floor(x + s2), j = Math.floor(y + s2), k = Math.floor(z + s2);
    const t = (i + j + k) * G;
    const x0 = x - (i - t), y0 = y - (j - t), z0 = z - (k - t);
    let i1, j1, k1, i2, j2, k2;
    if (x0 >= y0) { if (y0 >= z0) { i1=1;j1=0;k1=0;i2=1;j2=1;k2=0; } else if (x0 >= z0) { i1=1;j1=0;k1=0;i2=1;j2=0;k2=1; } else { i1=0;j1=0;k1=1;i2=1;j2=0;k2=1; } }
    else { if (y0 < z0) { i1=0;j1=0;k1=1;i2=0;j2=1;k2=1; } else if (x0 < z0) { i1=0;j1=1;k1=0;i2=0;j2=1;k2=1; } else { i1=0;j1=1;k1=0;i2=1;j2=1;k2=0; } }
    const x1=x0-i1+G, y1=y0-j1+G, z1=z0-k1+G;
    const x2=x0-i2+2*G, y2=y0-j2+2*G, z2=z0-k2+2*G;
    const x3=x0-1+3*G, y3=y0-1+3*G, z3=z0-1+3*G;
    const ii=i&255, jj=j&255, kk=k&255;
    const gi0=this.perm[ii+this.perm[jj+this.perm[kk]]]%12;
    const gi1=this.perm[ii+i1+this.perm[jj+j1+this.perm[kk+k1]]]%12;
    const gi2=this.perm[ii+i2+this.perm[jj+j2+this.perm[kk+k2]]]%12;
    const gi3=this.perm[ii+1+this.perm[jj+1+this.perm[kk+1]]]%12;
    let n0=0, n1=0, n2=0, n3=0;
    let t0=0.6-x0*x0-y0*y0-z0*z0; if(t0>0){t0*=t0;n0=t0*t0*this.dot3(this.g3[gi0],x0,y0,z0);}
    let t1=0.6-x1*x1-y1*y1-z1*z1; if(t1>0){t1*=t1;n1=t1*t1*this.dot3(this.g3[gi1],x1,y1,z1);}
    let t2=0.6-x2*x2-y2*y2-z2*z2; if(t2>0){t2*=t2;n2=t2*t2*this.dot3(this.g3[gi2],x2,y2,z2);}
    let t3=0.6-x3*x3-y3*y3-z3*z3; if(t3>0){t3*=t3;n3=t3*t3*this.dot3(this.g3[gi3],x3,y3,z3);}
    return 32 * (n0 + n1 + n2 + n3);
  }
  fbm(x, y, z, oct) {
    let v=0, a=1, f=1, m=0;
    for (let i=0; i<oct; i++) { v += a * this.n3(x*f, y*f, z*f); m += a; a *= 0.5; f *= 2; }
    return v / m;
  }
  ridged(x, y, z, oct) {
    let v=0, a=1, f=1, m=0;
    for (let i=0; i<oct; i++) { let n = this.n3(x*f, y*f, z*f); n = 1 - Math.abs(n); n *= n; v += a*n; m += a; a *= 0.5; f *= 2; }
    return v / m;
  }
}

// Presets (locked settings per type category)
const PRESETS = {
  terrestrial: { sL: 0.7, wL: 0.88, sM: 2.5, wM: 0.4, sS: 8, wS: 0.27, sea: 0.52 },
  ocean:       { sL: 0.7, wL: 0.16, sM: 4.1, wM: 0.29, sS: 8, wS: 0.12, sea: 0.8 },
  gas:         { sL: 1.4, wL: 0.7,  sM: 4.1, wM: 0.29, sS: 8, wS: 0.12, sea: 0.1 },
};

// Color ramps per planet type
const RAMPS = {
  terrestrial: [[0,[10,20,80]],[.35,[20,40,120]],[.45,[30,60,140]],[.48,[160,150,100]],[.52,[40,100,40]],[.65,[30,80,30]],[.75,[60,50,30]],[.85,[100,90,80]],[.95,[180,180,180]],[1,[240,245,250]]],
  ocean:       [[0,[5,12,50]],[.3,[10,25,80]],[.5,[15,40,110]],[.6,[20,55,130]],[.7,[25,70,140]],[.8,[30,90,100]],[.88,[40,120,80]],[.93,[50,100,50]],[1,[80,130,70]]],
  desert:      [[0,[100,60,30]],[.2,[140,90,45]],[.4,[180,130,70]],[.55,[200,150,85]],[.7,[170,115,55]],[.85,[130,80,40]],[1,[60,40,20]]],
  rocky:       [[0,[50,45,40]],[.25,[70,65,55]],[.4,[90,82,72]],[.55,[75,68,58]],[.7,[105,95,85]],[.85,[85,78,68]],[1,[120,110,100]]],
  ice:         [[0,[120,140,160]],[.2,[150,170,190]],[.4,[170,190,210]],[.55,[140,155,175]],[.7,[185,205,225]],[.85,[200,215,235]],[1,[220,235,248]]],
  volcanic:    [[0,[20,8,2]],[.2,[40,15,5]],[.4,[70,25,8]],[.55,[50,18,5]],[.7,[100,35,10]],[.82,[180,60,0]],[.9,[255,100,0]],[1,[255,180,40]]],
  gas_giant:   [[0,[120,70,25]],[.15,[180,115,45]],[.3,[140,85,35]],[.45,[200,140,60]],[.55,[160,95,40]],[.7,[220,160,75]],[.8,[150,90,35]],[.9,[190,130,55]],[1,[240,180,90]]],
  ice_giant:   [[0,[20,45,100]],[.2,[35,70,140]],[.35,[25,55,115]],[.5,[50,95,165]],[.65,[35,75,130]],[.8,[60,110,180]],[.9,[40,85,150]],[1,[75,130,200]]],
};

function sampleRamp(ramp, t) {
  t = Math.max(0, Math.min(1, t));
  for (let i = 0; i < ramp.length - 1; i++) {
    if (t <= ramp[i+1][0]) {
      const t0 = ramp[i][0], t1 = ramp[i+1][0];
      const f = (t - t0) / (t1 - t0);
      const c0 = ramp[i][1], c1 = ramp[i+1][1];
      return [c0[0]+(c1[0]-c0[0])*f, c0[1]+(c1[1]-c0[1])*f, c0[2]+(c1[2]-c0[2])*f];
    }
  }
  return ramp[ramp.length - 1][1];
}

// Simple string hash
function _hash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) { h = ((h << 5) - h) + str.charCodeAt(i); h |= 0; }
  return h;
}

/**
 * Generate a planet texture as a THREE.CanvasTexture.
 * @param {object} THREE - Three.js library reference
 * @param {string} planetId - unique ID for seeding
 * @param {string} planetType - e.g. 'terrestrial', 'gas_giant', 'ocean', etc.
 * @param {boolean} isPlanet - true for planets (512x256), false for moons (256x128)
 * @returns {THREE.CanvasTexture}
 */
export function generatePlanetTexture(THREE, planetId, planetType, isPlanet = true) {
  const seed = Math.abs(_hash(planetId));
  const isGas = (planetType === 'gas_giant' || planetType === 'ice_giant');
  const isOcean = (planetType === 'ocean');
  const pr = isGas ? PRESETS.gas : isOcean ? PRESETS.ocean : PRESETS.terrestrial;
  const ramp = RAMPS[planetType] || RAMPS[isGas ? 'gas_giant' : 'terrestrial'];

  const W = isPlanet ? 512 : 256;
  const H = isPlanet ? 256 : 128;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');

  const na = new PlanetNoise(seed);
  const nb = new PlanetNoise(seed + 57);
  const nc = new PlanetNoise(seed + 137);
  const nd = new PlanetNoise(seed + 200);

  // Pass 1: generate raw heightmap
  const heights = new Float32Array(W * H);
  let hMin = 1e9, hMax = -1e9;

  for (let y = 0; y < H; y++) {
    const lat = (y / H) * Math.PI;
    const sinL = Math.sin(lat), cosL = Math.cos(lat);
    const latN = y / H;

    for (let x = 0; x < W; x++) {
      const lon = (x / W) * Math.PI * 2;
      const bx = sinL * Math.cos(lon), by = sinL * Math.sin(lon), bz = cosL;
      let h;

      if (isGas) {
        const bf = 10 + (seed % 8);
        const turb = na.fbm(bx*pr.sM, by*pr.sM, bz*pr.sM, 5) * 0.3;
        const bv = Math.sin((latN * bf + turb) * Math.PI);
        h = Math.sign(bv) * Math.pow(Math.abs(bv), 0.5) * 0.5 + 0.5;
        h += nd.fbm(bx*pr.sS + latN*5, by*0.5, bz*pr.sS, 4) * 0.15;
      } else {
        const tw = pr.wL + pr.wM + pr.wS;
        const lg = na.fbm(bx*pr.sL, by*pr.sL, bz*pr.sL, 6);
        const md = nb.fbm(bx*pr.sM, by*pr.sM, bz*pr.sM, 5);
        const sm = nc.ridged(bx*pr.sS, by*pr.sS, bz*pr.sS, 4);
        h = (lg * pr.wL + md * pr.wM + sm * pr.wS) / (tw || 1);
      }

      heights[y * W + x] = h;
      if (h < hMin) hMin = h;
      if (h > hMax) hMax = h;
    }
  }

  // Pass 2: normalize + apply color ramp
  const hRange = hMax - hMin || 1;
  const img = ctx.createImageData(W, H);

  for (let i = 0; i < heights.length; i++) {
    let h = (heights[i] - hMin) / hRange; // normalized 0-1

    // Sea level remap (non-gas only)
    if (!isGas) {
      const sl = pr.sea;
      if (h < sl) {
        h = (h / sl) * 0.45; // below sea → ocean portion of ramp
      } else {
        h = 0.45 + ((h - sl) / (1 - sl)) * 0.55; // above sea → land portion
      }
    }

    h = Math.max(0, Math.min(1, h));
    const c = sampleRamp(ramp, h);
    img.data[i*4]   = c[0] | 0;
    img.data[i*4+1] = c[1] | 0;
    img.data[i*4+2] = c[2] | 0;
    img.data[i*4+3] = 255;
  }

  ctx.putImageData(img, 0, 0);

  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  return tex;
}
