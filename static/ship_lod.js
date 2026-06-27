/**
 * Ship LOD System - Screen-size based (like UE5).
 * 
 * LOD switches based on projected screen percentage, not raw distance.
 * screenSize = (objectRadius * screenHeight) / (distance * 2 * tan(fov/2))
 * 
 * LOD 0: > 5% screen (full mesh)
 * LOD 1: 1-5% screen (merged bounding box)
 * LOD 2: 0.2-1% screen (billboard sprite)
 * LOD 3: < 0.2% (dot/hidden)
 */
import * as THREE from 'three';
import { buildShipFromData } from '/static/ship_renderer.js';

export const LOD_THRESHOLDS = {
  lod0: 0.05,   // > 5% screen = full detail
  lod1: 0.01,   // 1-5% = simplified
  lod2: 0.002,  // 0.2-1% = billboard
  // below 0.2% = dot or hidden
};

/**
 * Calculate screen size fraction for an object.
 */
export function getScreenSize(objectRadius, distance, fovRad, screenHeight) {
  if (distance <= 0) return 1;
  return (objectRadius * screenHeight) / (distance * 2 * Math.tan(fovRad / 2));
}

/**
 * Determine which LOD level to use based on screen size.
 */
export function getLODLevel(screenFraction) {
  if (screenFraction >= LOD_THRESHOLDS.lod0) return 0;
  if (screenFraction >= LOD_THRESHOLDS.lod1) return 1;
  if (screenFraction >= LOD_THRESHOLDS.lod2) return 2;
  return 3;
}

/**
 * Create LOD 1: single bounding-box pod.
 */
export function createLOD1(bounds, scale, color) {
  const l = (bounds.length || 2) * scale;
  const h = (bounds.height || 0.5) * scale;
  const w = (bounds.width || 1) * scale;
  const bevel = Math.min(l, h, w) * 0.1;
  const hw = w/2, hh = h/2;
  const s = new THREE.Shape();
  s.moveTo(-hw+bevel,-hh); s.lineTo(hw-bevel,-hh); s.lineTo(hw,-hh+bevel);
  s.lineTo(hw,hh-bevel); s.lineTo(hw-bevel,hh); s.lineTo(-hw+bevel,hh);
  s.lineTo(-hw,hh-bevel); s.lineTo(-hw,-hh+bevel); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, {depth:l, bevelEnabled:true, bevelThickness:bevel*0.5, bevelSize:bevel*0.5});
  geo.center();
  const mat = new THREE.MeshPhongMaterial({color:color||0x0a1428, emissive:0x0a1428, shininess:0, transparent:true, opacity:0.7});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.y = Math.PI/2;
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo,15), new THREE.LineBasicMaterial({color:0x4fc3f7,transparent:true,opacity:0.4})));
  const group = new THREE.Group(); group.add(mesh);
  return group;
}

/**
 * Create LOD 2: billboard sprite (diamond).
 */
export function createLOD2(scale, color) {
  const size = scale * 8;
  const canvas = document.createElement('canvas');
  canvas.width=32; canvas.height=32;
  const ctx = canvas.getContext('2d');
  const c = color ? `#${new THREE.Color(color).getHexString()}` : '#4fc3f7';
  ctx.fillStyle=c; ctx.globalAlpha=0.8;
  ctx.beginPath(); ctx.moveTo(16,2); ctx.lineTo(30,16); ctx.lineTo(16,30); ctx.lineTo(2,16); ctx.closePath(); ctx.fill();
  ctx.strokeStyle=c; ctx.globalAlpha=1; ctx.lineWidth=1; ctx.stroke();
  const tex = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map:tex, transparent:true, opacity:0.9}));
  sprite.scale.set(size, size, 1);
  const group = new THREE.Group(); group.add(sprite);
  return group;
}

/**
 * Create LOD 3: tiny dot.
 */
export function createLOD3(color) {
  const canvas = document.createElement('canvas');
  canvas.width=4; canvas.height=4;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color ? `#${new THREE.Color(color).getHexString()}` : '#4fc3f7';
  ctx.fillRect(0,0,4,4);
  const tex = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map:tex, transparent:true, opacity:0.6}));
  sprite.scale.set(4, 4, 1);
  const group = new THREE.Group(); group.add(sprite);
  return group;
}

/**
 * Create wreck sprite (gray quad).
 */
export function createWreckSprite(scale) {
  const size = scale * 6;
  const canvas = document.createElement('canvas');
  canvas.width=16; canvas.height=16;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#444'; ctx.globalAlpha=0.7; ctx.fillRect(2,2,12,12);
  const tex = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true}));
  sprite.scale.set(size,size,1);
  return sprite;
}

/**
 * Create loot marker (gold dot).
 */
export function createLootMarker() {
  const canvas = document.createElement('canvas');
  canvas.width=8; canvas.height=8;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#ffd54f'; ctx.globalAlpha=0.9;
  ctx.beginPath(); ctx.arc(4,4,3,0,Math.PI*2); ctx.fill();
  const tex = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true}));
  sprite.scale.set(15,15,1);
  return sprite;
}
