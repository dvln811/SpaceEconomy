/**
 * Planet Texture Module (Web Worker based - non-blocking)
 * 
 * Usage:
 *   import { generatePlanetTexture, pregenPlanetTextures, clearPlanetTextureCache } from '/static/planet_textures.js';
 *   
 *   // Get texture (returns placeholder immediately, updates when ready)
 *   const tex = generatePlanetTexture(THREE, planetId, planetType, isPlanet);
 *   
 *   // Pre-generate all system textures (async, calls onDone when complete)
 *   pregenPlanetTextures(THREE, objects, priorityId, onDone);
 *   
 *   // Clear cache on system change
 *   clearPlanetTextureCache();
 */

let _worker = null;
const _texCache = new Map();       // id -> THREE.CanvasTexture (completed)
const _pendingCallbacks = new Map(); // id -> [{resolve}]
let _THREE = null;

let _normalCache = new Map(); // id -> THREE.CanvasTexture (normal map)
let _roughnessCache = new Map(); // id -> THREE.CanvasTexture (roughness map)

export function getNormalMap(planetId) {
  return _normalCache.get(planetId) || null;
}

export function getRoughnessMap(planetId) {
  return _roughnessCache.get(planetId) || null;
}

function getWorker() {
  if (!_worker) {
    _worker = new Worker('/static/planet_texture_worker.js');
    _worker.onmessage = function(e) {
      const { id, width, height, pixels, normalPixels, roughnessPixels } = e.data;
      // Create color canvas
      const canvas = document.createElement('canvas');
      canvas.width = width; canvas.height = height;
      const ctx = canvas.getContext('2d');
      const imgData = new ImageData(new Uint8ClampedArray(pixels), width, height);
      ctx.putImageData(imgData, 0, 0);
      
      // Create Three.js textures
      if (_THREE) {
        const tex = new _THREE.CanvasTexture(canvas);
        tex.wrapS = _THREE.RepeatWrapping;
        tex.wrapT = _THREE.ClampToEdgeWrapping;
        _texCache.set(id, tex);
        
        // Create normal map texture
        if (normalPixels) {
          const nCanvas = document.createElement('canvas');
          nCanvas.width = width; nCanvas.height = height;
          const nCtx = nCanvas.getContext('2d');
          const nImgData = new ImageData(new Uint8ClampedArray(normalPixels), width, height);
          nCtx.putImageData(nImgData, 0, 0);
          const normalTex = new _THREE.CanvasTexture(nCanvas);
          normalTex.wrapS = _THREE.RepeatWrapping;
          normalTex.wrapT = _THREE.ClampToEdgeWrapping;
          _normalCache.set(id, normalTex);
        }
        
        // Create roughness map texture
        if (roughnessPixels) {
          const rCanvas = document.createElement('canvas');
          rCanvas.width = width; rCanvas.height = height;
          const rCtx = rCanvas.getContext('2d');
          const rImgData = new ImageData(new Uint8ClampedArray(roughnessPixels), width, height);
          rCtx.putImageData(rImgData, 0, 0);
          const roughTex = new _THREE.CanvasTexture(rCanvas);
          roughTex.wrapS = _THREE.RepeatWrapping;
          roughTex.wrapT = _THREE.ClampToEdgeWrapping;
          _roughnessCache.set(id, roughTex);
        }
        
        // Update any meshes waiting for this texture
        if (_pendingCallbacks.has(id)) {
          _pendingCallbacks.get(id).forEach(cb => cb(tex));
          _pendingCallbacks.delete(id);
        }
      }
    };
  }
  return _worker;
}

/**
 * Get a planet texture. Returns cached texture if available,
 * otherwise returns a solid-color placeholder and queues generation.
 * When ready, the mesh's material.map will be updated automatically.
 */
export function generatePlanetTexture(THREE, planetId, planetType, isPlanet = true) {
  _THREE = THREE;
  
  // Return cached if available
  if (_texCache.has(planetId)) return _texCache.get(planetId);
  
  // Create a placeholder texture (solid color based on type)
  const colors = {
    terrestrial: '#1a4020', ocean: '#0a2050', desert: '#8a6030',
    rocky: '#504840', ice: '#90a8c0', volcanic: '#401008',
    gas_giant: '#805020', ice_giant: '#304880', super_earth: '#2a4a2a',
  };
  const col = colors[planetType] || '#404040';
  const placeholder = document.createElement('canvas');
  placeholder.width = 4; placeholder.height = 4;
  const pctx = placeholder.getContext('2d');
  pctx.fillStyle = col;
  pctx.fillRect(0, 0, 4, 4);
  const tex = new THREE.CanvasTexture(placeholder);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  _texCache.set(planetId, tex);
  
  // Queue generation in worker
  getWorker().postMessage({ id: planetId, planetType: planetType || 'rocky', isPlanet });
  
  // When worker completes, swap the texture content
  if (!_pendingCallbacks.has(planetId)) _pendingCallbacks.set(planetId, []);
  _pendingCallbacks.get(planetId).push((realTex) => {
    // Copy the real texture's image to the placeholder (so existing meshes update)
    tex.image = realTex.image;
    tex.needsUpdate = true;
  });
  
  return tex;
}

/**
 * Pre-generate textures for all planets/moons in a system.
 * Non-blocking (uses worker). Calls onDone when ALL are complete.
 * Priority planet is sent first.
 */
export function pregenPlanetTextures(THREE, objects, priorityId, onDone) {
  _THREE = THREE;
  const bodies = objects.filter(o => (o.type === 'planet' || o.type === 'moon') && o.planet_type);
  
  if (bodies.length === 0) { if (onDone) onDone(); return; }
  
  // Sort priority first
  bodies.sort((a, b) => {
    if (a.id === priorityId) return -1;
    if (b.id === priorityId) return 1;
    return 0;
  });
  
  let remaining = 0;
  
  for (const obj of bodies) {
    if (_texCache.has(obj.id) && _texCache.get(obj.id).image.width > 4) continue; // already done (not placeholder)
    remaining++;
    const isPlanet = obj.type === 'planet';
    
    getWorker().postMessage({ id: obj.id, planetType: obj.planet_type, isPlanet });
    
    if (!_pendingCallbacks.has(obj.id)) _pendingCallbacks.set(obj.id, []);
    _pendingCallbacks.get(obj.id).push((realTex) => {
      // Update existing placeholder if any
      if (_texCache.has(obj.id)) {
        const existing = _texCache.get(obj.id);
        existing.image = realTex.image;
        existing.needsUpdate = true;
      }
      remaining--;
      if (remaining <= 0 && onDone) { onDone(); onDone = null; }
    });
  }
  
  // If nothing needed generation
  if (remaining === 0 && onDone) onDone();
}

/**
 * Clear the texture cache (call when leaving a system).
 */
export function clearPlanetTextureCache() {
  _texCache.forEach(tex => { if (tex.dispose) tex.dispose(); });
  _texCache.clear();
  _normalCache.forEach(tex => { if (tex.dispose) tex.dispose(); });
  _normalCache.clear();
  _roughnessCache.forEach(tex => { if (tex.dispose) tex.dispose(); });
  _roughnessCache.clear();
  _pendingCallbacks.clear();
}
