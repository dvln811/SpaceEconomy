/**
 * Ship LOD System - Three levels of detail for ship rendering.
 * 
 * LOD 0 (close): Full component mesh (buildShipFromData)
 * LOD 1 (medium): Single merged bounding-box shape per ship
 * LOD 2 (far): Billboard sprite (colored triangle)
 * 
 * Usage:
 *   import { createShipLOD, LOD_DISTANCES } from '/static/ship_lod.js';
 *   const lodGroup = createShipLOD(geoData, { faction, scale, color });
 *   scene.add(lodGroup);
 */
import * as THREE from 'three';
import { buildShipFromData } from '/static/ship_renderer.js';

// Distance thresholds for LOD switching
export const LOD_DISTANCES = {
  high: 0,      // LOD 0: full mesh
  medium: 800,  // LOD 1: simplified box
  low: 2500,    // LOD 2: billboard sprite
};

/**
 * Create LOD 1: a single beveled pod that approximates the ship's bounding box.
 */
function createLOD1(bounds, scale, color) {
  const l = (bounds.length || 2) * scale;
  const h = (bounds.height || 0.5) * scale;
  const w = (bounds.width || 1) * scale;
  
  const bevel = Math.min(l, h, w) * 0.1;
  const hw = w / 2, hh = h / 2;
  const s = new THREE.Shape();
  s.moveTo(-hw + bevel, -hh);
  s.lineTo(hw - bevel, -hh);
  s.lineTo(hw, -hh + bevel);
  s.lineTo(hw, hh - bevel);
  s.lineTo(hw - bevel, hh);
  s.lineTo(-hw + bevel, hh);
  s.lineTo(-hw, hh - bevel);
  s.lineTo(-hw, -hh + bevel);
  s.closePath();
  
  const geo = new THREE.ExtrudeGeometry(s, {
    depth: l, bevelEnabled: true, bevelThickness: bevel * 0.5, bevelSize: bevel * 0.5
  });
  geo.center();
  
  const mat = new THREE.MeshPhongMaterial({
    color: color || 0x0a1428,
    emissive: color ? new THREE.Color(color).multiplyScalar(0.2) : 0x0a1428,
    shininess: 0,
    transparent: true,
    opacity: 0.7,
  });
  
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.y = Math.PI / 2;
  
  // Add edge wireframe
  const edges = new THREE.EdgesGeometry(geo, 15);
  const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({
    color: 0x4fc3f7, transparent: true, opacity: 0.4
  }));
  mesh.add(line);
  
  const group = new THREE.Group();
  group.add(mesh);
  return group;
}

/**
 * Create LOD 2: a billboard sprite (flat colored triangle/diamond shape).
 */
function createLOD2(scale, color) {
  const size = scale * 8;
  const canvas = document.createElement('canvas');
  canvas.width = 32;
  canvas.height = 32;
  const ctx = canvas.getContext('2d');
  
  // Draw a diamond shape
  const c = color ? `#${new THREE.Color(color).getHexString()}` : '#4fc3f7';
  ctx.fillStyle = c;
  ctx.globalAlpha = 0.8;
  ctx.beginPath();
  ctx.moveTo(16, 2);
  ctx.lineTo(30, 16);
  ctx.lineTo(16, 30);
  ctx.lineTo(2, 16);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = c;
  ctx.globalAlpha = 1;
  ctx.lineWidth = 1;
  ctx.stroke();
  
  const texture = new THREE.CanvasTexture(canvas);
  const mat = new THREE.SpriteMaterial({ map: texture, transparent: true, opacity: 0.9 });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(size, size, 1);
  
  const group = new THREE.Group();
  group.add(sprite);
  return group;
}

/**
 * Create a THREE.LOD object with all 3 levels for a ship.
 * 
 * @param {object} geoData - Ship geometry data (from ship_geometry.py)
 * @param {object} opts - { scale, color, faction, showHardpoints }
 * @returns {THREE.LOD}
 */
export function createShipLOD(geoData, opts = {}) {
  const scale = opts.scale || 1;
  const color = opts.color || 0x4fc3f7;
  const bounds = geoData.bounds || { length: 2, height: 0.5, width: 1 };
  
  const lod = new THREE.LOD();
  
  // LOD 0: Full mesh
  const fullGroup = new THREE.Group();
  buildShipFromData(fullGroup, geoData, { showHardpoints: opts.showHardpoints || false });
  fullGroup.scale.set(scale, scale, scale);
  lod.addLevel(fullGroup, LOD_DISTANCES.high);
  
  // LOD 1: Simplified bounding box
  const boxGroup = createLOD1(bounds, scale, color);
  lod.addLevel(boxGroup, LOD_DISTANCES.medium);
  
  // LOD 2: Billboard sprite
  const spriteGroup = createLOD2(scale, color);
  lod.addLevel(spriteGroup, LOD_DISTANCES.low);
  
  return lod;
}

/**
 * Create a dead ship billboard (gray quad with slight glow).
 */
export function createWreckSprite(scale) {
  const size = scale * 6;
  const canvas = document.createElement('canvas');
  canvas.width = 16;
  canvas.height = 16;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#555555';
  ctx.globalAlpha = 0.6;
  ctx.fillRect(2, 2, 12, 12);
  
  const texture = new THREE.CanvasTexture(canvas);
  const mat = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(size, size, 1);
  return sprite;
}

/**
 * Create a loot marker (small bright point).
 */
export function createLootMarker() {
  const canvas = document.createElement('canvas');
  canvas.width = 8;
  canvas.height = 8;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffd54f';
  ctx.globalAlpha = 0.9;
  ctx.beginPath();
  ctx.arc(4, 4, 3, 0, Math.PI * 2);
  ctx.fill();
  
  const texture = new THREE.CanvasTexture(canvas);
  const mat = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(15, 15, 1);
  return sprite;
}
