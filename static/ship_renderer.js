/**
 * Ship Renderer - builds Three.js geometry from ship component data.
 * Usage: import { buildShipFromData, MATERIALS } from '/static/ship_renderer.js';
 * Requires Three.js to be available via importmap.
 */
import * as THREE from 'three';

export const MATERIALS = {
  hull: () => new THREE.MeshPhongMaterial({color:0x0a1428, emissive:0x0a1428, shininess:0, transparent:true, opacity:0.7}),
  engine: () => new THREE.MeshPhongMaterial({color:0x0a1428, emissive:0x0a1020, shininess:0, transparent:true, opacity:0.7}),
  cargo: () => new THREE.MeshPhongMaterial({color:0x1a1808, emissive:0x0a0a05, shininess:0, transparent:true, opacity:0.7}),
  mining: () => new THREE.MeshPhongMaterial({color:0x1a1028, emissive:0x0a0818, shininess:0, transparent:true, opacity:0.7}),
  weapon: () => new THREE.MeshPhongMaterial({color:0x1a1018, emissive:0x100508, shininess:0, transparent:true, opacity:0.7}),
  shield: () => new THREE.MeshPhongMaterial({color:0x0a1a0a, emissive:0x050a05, shininess:0, transparent:true, opacity:0.7}),
  accent: () => new THREE.MeshPhongMaterial({color:0x1a2040, emissive:0x0a0a1a, shininess:0, transparent:true, opacity:0.7}),
};

const EDGE_COLOR = {hull:0x4fc3f7, engine:0x5a7a9a, cargo:0xffd54f, mining:0xab47bc, weapon:0xef5350, shield:0x66bb6a, accent:0xef5350};
const HP_COLORS = {defense:0x66bb6a, utility:0x4fc3f7, industrial:0xffd54f, mining:0xab47bc, weapon:0xef5350, shield:0x66bb6a};

function addEdges(mesh, material) {
  if (!mesh.geometry) return;
  const col = EDGE_COLOR[material] || 0x4fc3f7;
  const edges = new THREE.EdgesGeometry(mesh.geometry, 15);
  const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({color:col, transparent:true, opacity:0.5}));
  mesh.add(line);
}

export function buildShipFromData(scene, data, options = {}) {
  const showHardpoints = options.showHardpoints !== false;
  const group = new THREE.Group();

  for (const comp of data.components) {
    const mat = (MATERIALS[comp.material] || MATERIALS.hull)();
    const [px, py, pz] = comp.pos;
    const [rx, ry, rz] = comp.rot || [0,0,0];
    let mesh = null;

    switch(comp.type) {
      case 'pod': {
        const {length, height, width} = comp.params;
        const b=0.04, hw=width/2, hh=height/2;
        const s = new THREE.Shape();
        s.moveTo(-hh+b,-hw); s.lineTo(hh-b,-hw); s.lineTo(hh,-hw+b);
        s.lineTo(hh,hw-b); s.lineTo(hh-b,hw); s.lineTo(-hh+b,hw);
        s.lineTo(-hh,hw-b); s.lineTo(-hh,-hw+b); s.closePath();
        const g = new THREE.ExtrudeGeometry(s, {depth:length, bevelEnabled:true, bevelThickness:0.01, bevelSize:0.01});
        g.center();
        mesh = new THREE.Mesh(g, mat);
        if (rx === 0 && ry === 0 && rz === 0) mesh.rotation.y = Math.PI/2;
        break;
      }
      case 'cylinder': {
        const {r_top, r_bot, length} = comp.params;
        const g = new THREE.CylinderGeometry(r_top, r_bot, length, 8);
        mesh = new THREE.Mesh(g, mat);
        if (rx === 0 && ry === 0 && rz === 0 && !comp.params.vertical) mesh.rotation.z = Math.PI/2;
        break;
      }
      case 'cone': {
        const {radius, length} = comp.params;
        const g = new THREE.ConeGeometry(radius, length, 8);
        mesh = new THREE.Mesh(g, mat);
        if (rx === 0 && ry === 0 && rz === 0 && !comp.params.vertical) mesh.rotation.z = Math.PI/2;
        break;
      }
      case 'spine': {
        const {length, radius, flange_r} = comp.params;
        const grp = new THREE.Group();
        const s = new THREE.Shape();
        for(let i=0;i<=6;i++){const a=Math.PI*2*i/6; if(i===0)s.moveTo(Math.cos(a)*radius,Math.sin(a)*radius); else s.lineTo(Math.cos(a)*radius,Math.sin(a)*radius);}
        const bg = new THREE.ExtrudeGeometry(s,{depth:length,bevelEnabled:false}); bg.center();
        const body = new THREE.Mesh(bg, mat); body.rotation.y=Math.PI/2; grp.add(body);
        const fg = new THREE.CylinderGeometry(flange_r,flange_r,0.04,8);
        const fA = new THREE.Mesh(fg, mat); fA.rotation.z=Math.PI/2; fA.position.x=-length/2-0.02; grp.add(fA);
        const fB = new THREE.Mesh(fg.clone(), mat); fB.rotation.z=Math.PI/2; fB.position.x=length/2+0.02; grp.add(fB);
        grp.position.set(px, py, pz);
        group.add(grp);
        grp.traverse(child => { if(child.isMesh) addEdges(child, comp.material); });
        continue;
      }
      case 'box': {
        const {x, y, z} = comp.params;
        mesh = new THREE.Mesh(new THREE.BoxGeometry(x, y, z), mat);
        break;
      }
      case 'sphere': {
        const {radius, half} = comp.params;
        const g = half ? new THREE.SphereGeometry(radius, 8, 6, 0, Math.PI*2, 0, Math.PI/2) : new THREE.SphereGeometry(radius, 8, 6);
        mesh = new THREE.Mesh(g, mat);
        break;
      }
      case 'torus': {
        const {radius, tube} = comp.params;
        mesh = new THREE.Mesh(new THREE.TorusGeometry(radius, tube, 6, 12), mat);
        if (rx === 0 && ry === 0 && rz === 0) mesh.rotation.y = Math.PI/2;
        break;
      }
      case 'wedge': {
        const {profile, depth} = comp.params;
        const s = new THREE.Shape();
        profile.forEach((p,i) => i===0 ? s.moveTo(p[0],p[1]) : s.lineTo(p[0],p[1]));
        s.closePath();
        const g = new THREE.ExtrudeGeometry(s, {depth, bevelEnabled:true, bevelThickness:0.01, bevelSize:0.01});
        g.center();
        mesh = new THREE.Mesh(g, mat);
        break;
      }
      case 'hardpoint': {
        if (!showHardpoints) continue;
        const {slot_type} = comp.params;
        const col = HP_COLORS[slot_type] || 0xffffff;
        const g = new THREE.OctahedronGeometry(0.05);
        mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({color:col, wireframe:true, transparent:true, opacity:0.8}));
        break;
      }
      default: continue;
    }
    if (mesh) {
      mesh.position.set(px, py, pz);
      mesh.rotation.x += rx; mesh.rotation.y += ry; mesh.rotation.z += rz;
      group.add(mesh);
      if (comp.type !== 'hardpoint') addEdges(mesh, comp.material);
    }
  }
  scene.add(group);
  return group;
}
