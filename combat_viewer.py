"""Live combat simulator - full fitting model with cap/ammo/module damage."""
import sys, json, time, threading
sys.path.insert(0, '.')
from flask import Flask, Response, render_template_string, request
from server.combat_engine import CombatEngine, make_ship, make_weapon, make_module, DmgType

app = Flask(__name__)

# Battle control state
battle_state = {"paused": False, "stop": False, "restart": False}

HTML = r"""<!DOCTYPE html>
<html><head><title>Combat Simulator</title>
<style>
* { box-sizing: border-box; }
body { background: #0a0a1a; color: #c0c0c0; font-family: 'Courier New', monospace; margin: 0; padding: 15px; height: 100vh; overflow: hidden; }
h1 { color: #4fc3f7; margin: 0; font-size: 18px; display: inline; }
#controls { display: inline; margin-left: 20px; }
#controls button { background: #222; color: #ccc; border: 1px solid #555; padding: 3px 10px; cursor: pointer; font-family: inherit; font-size: 11px; margin: 0 3px; border-radius: 3px; }
#controls button:hover { background: #333; }
#controls button.active { background: #4caf50; color: #000; border-color: #4caf50; }
#status { color: #4fc3f7; font-size: 12px; margin: 6px 0; }
.layout { display: flex; height: calc(100vh - 65px); gap: 12px; }
.fleets { flex: 0 0 40%; display: flex; flex-direction: column; gap: 6px; overflow: hidden; }
.fleet-panel { flex: 1; border: 1px solid #333; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
.fleet-header { padding: 4px 10px; font-weight: bold; font-size: 11px; border-bottom: 1px solid #333; flex-shrink: 0; }
.fleet-header.f0 { background: #1a2a1a; color: #4caf50; }
.fleet-header.f1 { background: #1a1a2a; color: #42a5f5; }
.fleet-header.f2 { background: #2a1a2a; color: #ce93d8; }
.fleet-ships { padding: 4px; overflow-y: auto; flex: 1; display: flex; flex-wrap: wrap; gap: 4px; align-content: flex-start; }
.ship { padding: 4px 6px; border-radius: 3px; font-size: 10px; background: #111; border-left: 3px solid #444; width: 180px; cursor: pointer; position: relative; }
.ship.alive.fc0 { border-left-color: #4caf50; }
.ship.alive.fc1 { border-left-color: #42a5f5; }
.ship.alive.fc2 { border-left-color: #ce93d8; }
.ship.dead { opacity: 0.3; background: #1a0a0a; border-left-color: #f44336; }
.ship-name { font-weight: bold; }
.fittings { color: #a0a0a0; font-size: 9px; }
.hp-bars { margin-top: 2px; }
.hp-row { display: flex; align-items: center; margin: 1px 0; }
.hp-label { width: 9px; font-size: 8px; font-weight: bold; }
.hp-label-s { color: #42a5f5; }
.hp-label-a { color: #ffa726; }
.hp-label-h { color: #ef5350; }
.hp-track { flex: 1; height: 4px; background: #1a1a1a; border-radius: 2px; overflow: hidden; }
.hp-fill-s { height: 100%; background: #42a5f5; transition: width 0.3s; }
.hp-fill-a { height: 100%; background: #ffa726; transition: width 0.3s; }
.hp-fill-h { height: 100%; background: #ef5350; transition: width 0.3s; }
.hp-fill-c { height: 100%; background: #aa66ff; transition: width 0.3s; }
.hp-val { width: 50px; font-size: 8px; text-align: right; color: #b0b0b0; }
.log-panel { flex: 1; border: 1px solid #333; border-radius: 4px; display: flex; flex-direction: column; overflow: hidden; }
.log-header { padding: 4px 10px; font-weight: bold; font-size: 11px; background: #1a1a1a; border-bottom: 1px solid #333; color: #ffa726; flex-shrink: 0; }
#log { flex: 1; overflow-y: auto; padding: 6px; font-size: 10px; line-height: 1.4; }
.log-hit { color: #ffa726; }
.log-miss { color: #888; }
.log-destroy { color: #f44336; font-weight: bold; }
#tooltip { display: none; position: fixed; background: #111; border: 1px solid #4fc3f7; border-radius: 4px; padding: 10px; font-size: 11px; z-index: 999; width: 280px; pointer-events: none; }
#tooltip h3 { margin: 0 0 6px; color: #4fc3f7; font-size: 13px; }
#tooltip .tt-section { margin: 4px 0; color: #ccc; }
#tooltip .tt-label { color: #888; }
#tooltip .tt-warn { color: #f44336; }
</style></head><body>
<h1>Combat Simulator</h1>
<span id="controls">
  <button id="btn-pause" onclick="sendCmd('pause')">Pause</button>
  <button id="btn-restart" onclick="sendCmd('restart')">Restart</button>
  <button id="btn-stop" onclick="sendCmd('stop')">Stop</button>
</span>
<div id="status">Connecting...</div>
<div class="layout">
  <div class="fleets" id="fleets"></div>
  <div style="flex:0 0 35%;display:flex;flex-direction:column;gap:8px;">
    <canvas id="tactical" width="500" height="400" style="background:#060612;border:1px solid #333;border-radius:4px;flex:0 0 400px;"></canvas>
    <div class="log-panel" style="flex:1;">
      <div class="log-header">Battle Log</div>
      <div id="log"></div>
    </div>
  </div>
</div>
<div id="tooltip"></div>
<script>
const ships = {};
let shipState = {}; // live state: {id: {cap, cap_max, ammo:{}, modules_hp:[]}}
let es;
const log = document.getElementById('log');
const tooltip = document.getElementById('tooltip');

function connect() {
  log.innerHTML = '';
  document.getElementById('fleets').innerHTML = '';
  es = new EventSource('/stream');
  es.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'init') {
      const fleetsEl = document.getElementById('fleets');
      fleetsEl.innerHTML = '';
      const fclasses = ['f0','f1','f2'];
      const sclasses = ['fc0','fc1','fc2'];
      data.fleets.forEach((f, i) => {
        factionColors[f.faction] = FC[i];
        const panel = document.createElement('div');
        panel.className = 'fleet-panel';
        panel.innerHTML = '<div class="fleet-header ' + fclasses[i] + '">' + f.faction + ' (' + f.count + ')' + (f.ally ? ' [+' + f.ally + ']' : '') + '</div><div class="fleet-ships" id="fleet-' + i + '"></div>';
        fleetsEl.appendChild(panel);
        renderFleet('fleet-' + i, f.ships, sclasses[i]);
        f.ships.forEach(s => {
          s.faction = f.faction;
          ships[s.id] = s;
          shipState[s.id] = {cap: s.cap, cap_max: s.cap, ammo: s.ammo || {}, weapons: s.weapons, modules: s.modules};
        });
      });
      document.getElementById('status').textContent = 'Battle starting...';
    } else if (data.type === 'tick') {
      document.getElementById('status').textContent = 'Tick ' + data.tick;
      if (data.ship_caps) {
        for (const [id, cap] of Object.entries(data.ship_caps)) {
          if (shipState[id]) shipState[id].cap = cap;
          const ce = document.getElementById('hp-c-'+id);
          const cv = document.getElementById('hpv-c-'+id);
          if (ce && ships[id]) { ce.style.width = (cap/ships[id].cap*100)+'%'; }
          if (cv) cv.textContent = Math.round(cap);
        }
      }
      if (data.pos) onTickPositions(data.pos, data.msls);
    } else if (data.type === 'event') {
      handleEvent(data);
    } else if (data.type === 'end') {
      document.getElementById('status').textContent = 'BATTLE OVER - Winner: ' + data.winner + ' (' + data.ticks + ' ticks)';
      es.close();
    }
  };
}

function sendCmd(cmd) {
  fetch('/control?cmd=' + cmd);
  if (cmd === 'restart') { if (es) es.close(); setTimeout(connect, 500); }
}

function renderFleet(id, shipList, cls) {
  document.getElementById(id).innerHTML = shipList.map(s => {
    const fit = s.weapons ? s.weapons.map(w => w.name+'['+w.size+']').join(', ') : '';
    const mods = s.modules && s.modules.length ? s.modules.map(m => m.name).join(', ') : '';
    return '<div class="ship alive ' + cls + '" id="ship-' + s.id + '" onmouseenter="showTT(event,\'' + s.id + '\')" onmouseleave="hideTT()">' +
    '<div><span class="ship-name">' + s.name + '</span></div>' +
    '<div class="fittings">' + fit + (mods ? ' | ' + mods : '') + '</div>' +
    '<div class="hp-bars">' +
    '<div class="hp-row"><span class="hp-label hp-label-s">S</span><div class="hp-track"><div class="hp-fill-s" id="hp-s-' + s.id + '" style="width:100%"></div></div><span class="hp-val" id="hpv-s-' + s.id + '">' + s.shield + '</span></div>' +
    '<div class="hp-row"><span class="hp-label hp-label-a">A</span><div class="hp-track"><div class="hp-fill-a" id="hp-a-' + s.id + '" style="width:100%"></div></div><span class="hp-val" id="hpv-a-' + s.id + '">' + s.armor + '</span></div>' +
    '<div class="hp-row"><span class="hp-label hp-label-h">H</span><div class="hp-track"><div class="hp-fill-h" id="hp-h-' + s.id + '" style="width:100%"></div></div><span class="hp-val" id="hpv-h-' + s.id + '">' + s.hull + '</span></div>' +
    '<div class="hp-row"><span class="hp-label" style="color:#aa66ff">C</span><div class="hp-track"><div class="hp-fill-c" id="hp-c-' + s.id + '" style="width:100%"></div></div><span class="hp-val" id="hpv-c-' + s.id + '">' + s.cap + '</span></div>' +
    '</div></div>';
  }).join('');
}

function showTT(ev, id) {
  const s = ships[id], st = shipState[id];
  if (!s || !st) return;
  let html = '<h3>' + s.name + ' [' + s.hull_class + ']</h3>';
  html += '<div class="tt-section"><span class="tt-label">Cap:</span> ' + Math.round(st.cap) + '/' + st.cap_max + ' (rech: ' + s.cap_recharge + '/tick)</div>';
  html += '<div class="tt-section"><span class="tt-label">Weapons:</span></div>';
  (st.weapons||[]).forEach(w => {
    html += '<div>  ' + w.name + '[' + w.size + '] ' + w.dmg + ' cyc:' + w.cycle + 't cap:' + w.cap_use + (w.ammo ? ' ammo:' + w.ammo : '') + '</div>';
  });
  if (Object.keys(st.ammo).length) {
    html += '<div class="tt-section"><span class="tt-label">Ammo:</span></div>';
    for (const [k,v] of Object.entries(st.ammo)) {
      html += '<div>  ' + k + ': ' + v + (v <= 20 ? ' <span class="tt-warn">LOW</span>' : '') + '</div>';
    }
  }
  if (st.modules && st.modules.length) {
    html += '<div class="tt-section"><span class="tt-label">Modules:</span></div>';
    st.modules.forEach(m => { html += '<div>  ' + m.name + ' [' + m.type + ']</div>'; });
  }
  tooltip.innerHTML = html;
  tooltip.style.display = 'block';
  tooltip.style.left = (ev.clientX + 15) + 'px';
  tooltip.style.top = (ev.clientY + 10) + 'px';
}
function hideTT() { tooltip.style.display = 'none'; }

function handleEvent(data) {
  const e = data.event;
  let msg = '';
  if (e.event === 'hit') {
    const src = ships[e.source_id], tgt = ships[e.target_id];
    msg = '<span class="log-hit">' + (src?src.name:'?') + ' -> ' + (tgt?tgt.name:'?') + ' [' + e.weapon + '] ' + Math.round(e.damage) + ' ' + e.damage_type + '</span>';
    updateHP(e.target_id, e.remaining_hp);
    addHitFlash(e.source_id, e.target_id, e.damage_type);
  } else if (e.event === 'miss') {
    const src = ships[e.source_id], tgt = ships[e.target_id];
    msg = '<span class="log-miss">' + (src?src.name:'?') + ' -> ' + (tgt?tgt.name:'?') + ' MISS</span>';
  } else if (e.event === 'destroyed') {
    const tgt = ships[e.target_id], src = ships[e.source_id];
    msg = '<span class="log-destroy">** ' + (tgt?tgt.name:'?') + ' DESTROYED by ' + (src?src.name:'?') + ' **</span>';
    document.getElementById('ship-' + e.target_id).className = 'ship dead';
  } else if (e.event === 'module_disabled') {
    const tgt = ships[e.target_id];
    msg = '<span style="color:#ff6600">' + (tgt?tgt.name:'?') + ' MODULE OFFLINE: ' + e.detail + '</span>';
  } else if (e.event === 'module_damaged') {
    const tgt = ships[e.target_id];
    msg = '<span style="color:#cc9900">' + (tgt?tgt.name:'?') + ' module hit: ' + e.detail + '</span>';
  } else if (e.event === 'cap_empty') {
    const tgt = ships[e.target_id];
    msg = '<span style="color:#aa66ff">' + (tgt?tgt.name:'?') + ' CAPACITOR EMPTY</span>';
  }
  // Update ammo state from detail if available
  if (e.ammo_update) { for (const [id,a] of Object.entries(e.ammo_update)) { if(shipState[id]) shipState[id].ammo = a; }}
  if (msg) { log.innerHTML += msg + '<br>'; log.scrollTop = log.scrollHeight; }
}

function updateHP(id, hpStr) {
  const m = hpStr.match(/S:(-?\d+)\/(\d+) A:(-?\d+)\/(\d+) H:(-?\d+)\/(\d+)/);
  if (!m) return;
  const s=Math.max(0,+m[1]),sM=+m[2],a=Math.max(0,+m[3]),aM=+m[4],h=Math.max(0,+m[5]),hM=+m[6];
  const se=document.getElementById('hp-s-'+id),ae=document.getElementById('hp-a-'+id),he=document.getElementById('hp-h-'+id);
  if(se)se.style.width=(sM>0?s/sM*100:0)+'%';
  if(ae)ae.style.width=(aM>0?a/aM*100:0)+'%';
  if(he)he.style.width=(hM>0?h/hM*100:0)+'%';
  const sv=document.getElementById('hpv-s-'+id),av=document.getElementById('hpv-a-'+id),hv=document.getElementById('hpv-h-'+id);
  if(sv)sv.textContent=s;if(av)av.textContent=a;if(hv)hv.textContent=h;
}

// Tactical canvas - velocity extrapolation (no pulsing)
const canvas = document.getElementById('tactical');
const ctx = canvas.getContext('2d');
let shipData = {};          // {id: {x, y, vx, vy}} from server
let shipDisplay = {};       // {id: {x, y}} rendered positions
let missileData = [];      // {x,y,vx,vy} from server
let missileDisplay = [];   // {x,y} rendered
let hitFlashes = [];
const factionColors = {};
let fColorIdx = 0;
const FC = ['#4caf50','#42a5f5','#ce93d8'];
let lastFrame = performance.now();
let lastTick = performance.now();

function animLoop(now) {
  const dt = (now - lastFrame) / 1000; // seconds since last frame
  lastFrame = now;

  // Extrapolate ship positions using velocity
  for (const [id, sd] of Object.entries(shipData)) {
    if (!shipDisplay[id]) { shipDisplay[id] = {x: sd.x, y: sd.y}; }
    // Extrapolate from current display position using server velocity
    shipDisplay[id].x += sd.vx * dt;
    shipDisplay[id].y += sd.vy * dt;
    // Gently correct toward server position to prevent drift
    const errX = sd.x - shipDisplay[id].x;
    const errY = sd.y - shipDisplay[id].y;
    shipDisplay[id].x += errX * 0.05;
    shipDisplay[id].y += errY * 0.05;
  }
  // Missiles: move at their velocity (constant speed, no lerp)
  for (let i = 0; i < missileData.length; i++) {
    if (!missileDisplay[i]) continue;
    const md = missileData[i];
    missileDisplay[i].x += md.vx * dt;
    missileDisplay[i].y += md.vy * dt;
  }
  missileDisplay.length = missileData.length;


  drawTactical();
  requestAnimationFrame(animLoop);
}

function onTickPositions(pos, msls) {
  for (const [id, p] of Object.entries(pos)) {
    shipData[id] = {x: p[0], y: p[1], vx: p[2], vy: p[3]};
    if (!shipDisplay[id]) shipDisplay[id] = {x: p[0], y: p[1]};
  }
  // Missiles: store with velocity for extrapolation
  missileData = (msls || []).map(m => ({x: m.x, y: m.y, vx: m.vx, vy: m.vy}));
  // Snap display to server positions (new missiles appear at correct spot)
  while (missileDisplay.length < missileData.length) {
    const m = missileData[missileDisplay.length];
    missileDisplay.push({x: m.x, y: m.y});
  }
  // Correct existing missiles to server position
  for (let i = 0; i < missileData.length; i++) {
    missileDisplay[i].x = missileData[i].x;
    missileDisplay[i].y = missileData[i].y;
  }
  missileDisplay.length = missileData.length;
  lastTick = performance.now();
}

function drawTactical() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#1a1a2a';
  ctx.lineWidth = 0.5;
  for (let x = 0; x < canvas.width; x += 50) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,canvas.height); ctx.stroke(); }
  for (let y = 0; y < canvas.height; y += 50) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(canvas.width,y); ctx.stroke(); }
  const scale = canvas.width / 45000;
  const ox = canvas.width / 2;
  const oy = canvas.height / 2;
  // Hit flashes
  for (let i = hitFlashes.length - 1; i >= 0; i--) {
    const f = hitFlashes[i];
    ctx.strokeStyle = f.color;
    ctx.lineWidth = 1;
    ctx.globalAlpha = f.ttl / f.maxTtl;
    ctx.beginPath(); ctx.moveTo(f.x1, f.y1); ctx.lineTo(f.x2, f.y2); ctx.stroke();
    ctx.globalAlpha = 1.0;
    f.ttl -= 0.04;
    if (f.ttl <= 0) hitFlashes.splice(i, 1);
  }
  // Missiles - just draw at server positions (they move too fast to interpolate)
  ctx.fillStyle = '#ff6644';
  for (const m of missileDisplay) {
    if (!m) continue;
    const mx = ox + m.x * scale;
    const my = oy + m.y * scale;
    ctx.beginPath(); ctx.arc(mx, my, 1.5, 0, Math.PI*2); ctx.fill();
  }
  // Ships - isosceles triangles with heading, transparent fill + outline
  for (const [id, pos] of Object.entries(shipDisplay)) {
    const s = ships[id];
    if (!s) continue;
    const sx = ox + pos.x * scale;
    const sy = oy + pos.y * scale;
    const fc = factionColors[s.faction] || '#888';
    const r = s.hull_class === 'Cruiser' ? 7 : s.hull_class === 'Destroyer' ? 6 : s.hull_class === 'Frigate' ? 5 : 4;
    // Heading from velocity
    const sd = shipData[id];
    const angle = sd ? Math.atan2(sd.vy, sd.vx) : 0;
    // Draw triangle
    ctx.save();
    ctx.translate(sx, sy);
    ctx.rotate(angle);
    ctx.beginPath();
    ctx.moveTo(r * 1.5, 0);          // nose
    ctx.lineTo(-r, -r * 0.7);        // left rear
    ctx.lineTo(-r, r * 0.7);         // right rear
    ctx.closePath();
    ctx.fillStyle = fc + '33';        // ~20% opacity fill
    ctx.fill();
    ctx.strokeStyle = fc;
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();
    if (r >= 6) {
      ctx.fillStyle = '#999';
      ctx.font = '8px monospace';
      ctx.fillText(s.name.split('(')[0].trim(), sx + r + 4, sy + 3);
    }
  }
}

function addHitFlash(srcId, tgtId, dmgType) {
  const sp = shipDisplay[srcId], tp = shipDisplay[tgtId];
  if (!sp || !tp) return;
  const scale = canvas.width / 45000;
  const ox = canvas.width/2, oy = canvas.height/2;
  const colors = {'EM':'#6666ff','Thermal':'#ff8800','Kinetic':'#aaaaaa','Explosive':'#ff4444'};
  hitFlashes.push({x1:ox+sp.x*scale, y1:oy+sp.y*scale, x2:ox+tp.x*scale, y2:oy+tp.y*scale, color:colors[dmgType]||'#fff', ttl:1.0, maxTtl:1.0});
}

requestAnimationFrame(animLoop);

connect();
</script></body></html>"""


def make_fleet(faction, prefix, size, style="balanced"):
    """Generate fleet with faction-appropriate composition."""
    ships = []
    configs = {
        "shield_heavy": [
            ("Cruiser", 3000, 1000, 600, [
                ("Beam Laser","EM",50,3,"M",15,""), ("Beam Laser","EM",50,3,"M",15,""),
                ("Heavy Missile","Kinetic",65,8,"M",5,"Scourge Missile M"),
            ], 75, 85, 800, 8, [("Shield Booster","utility",20,8,80,0)]),
            ("Frigate", 600, 1200, 500, [
                ("Autocannon","Kinetic",30,2,"S",0,"Fusion Shell S"), ("Autocannon","Kinetic",30,2,"S",0,"Fusion Shell S"),
                ("Rocket Launcher","Explosive",45,6,"S",3,"Inferno Rocket S"),
            ], 140, 40, 400, 5, [("Armor Repairer","utility",18,8,0,60)]),
            ("Fighter", 600, 200, 300, [
                ("Pulse Laser","Thermal",25,2,"S",10,""), ("Pulse Laser","Thermal",25,2,"S",10,""),
            ], 230, 22, 300, 6, []),
            ("Destroyer", 1800, 1200, 800, [
                ("Torpedo Launcher","Explosive",90,10,"L",8,"Nova Torpedo L"), ("Torpedo Launcher","Explosive",90,10,"L",8,"Nova Torpedo L"),
                ("Flak Battery","Kinetic",20,1,"S",0,"Fusion Shell S"),
            ], 90, 70, 600, 6, [("Shield Booster","utility",15,8,60,0)]),
            ("Frigate", 1000, 500, 400, [
                ("Railgun","Kinetic",55,4,"M",12,"Antimatter Charge M"), ("Railgun","Kinetic",55,4,"M",12,"Antimatter Charge M"),
            ], 95, 45, 500, 5, []),
        ],
        "armor_heavy": [
            ("Cruiser", 1200, 2800, 800, [
                ("Pulse Laser","Thermal",55,3,"M",14,""), ("Pulse Laser","Thermal",55,3,"M",14,""),
                ("Flak Battery","Explosive",30,2,"S",0,"Fusion Shell S"),
            ], 70, 90, 700, 6, [("Armor Repairer","utility",22,8,0,80)]),
            ("Frigate", 400, 1600, 600, [
                ("Blaster","Kinetic",40,2,"S",8,"Antimatter Charge S"), ("Blaster","Kinetic",40,2,"S",8,"Antimatter Charge S"),
                ("Blaster","Kinetic",40,2,"S",8,"Antimatter Charge S"),
            ], 130, 42, 450, 5, [("Armor Repairer","utility",15,8,0,50)]),
            ("Fighter", 300, 500, 400, [
                ("Autocannon","Kinetic",28,2,"S",0,"Fusion Shell S"),
                ("Rocket Launcher","Explosive",35,5,"S",2,"Inferno Rocket S"),
            ], 210, 24, 250, 4, []),
            ("Destroyer", 800, 2200, 1000, [
                ("Artillery","Explosive",85,7,"L",0,"Fusion Shell L"), ("Artillery","Explosive",85,7,"L",0,"Fusion Shell L"),
                ("Autocannon","Kinetic",25,2,"S",0,"Fusion Shell S"),
            ], 85, 72, 500, 5, [("Armor Repairer","utility",20,8,0,70)]),
            ("Frigate", 500, 1000, 500, [
                ("Gauss Cannon","EM",60,5,"M",18,"Antimatter Charge M"), ("Gauss Cannon","EM",60,5,"M",18,"Antimatter Charge M"),
            ], 100, 48, 600, 6, []),
        ],
        "balanced": [
            ("Cruiser", 2000, 1800, 700, [
                ("Beam Laser","EM",45,3,"M",14,""), ("Missile Launcher","Kinetic",55,7,"M",5,"Scourge Missile M"),
                ("Flak Battery","Explosive",25,2,"S",0,"Fusion Shell S"),
            ], 80, 80, 700, 7, [("Shield Booster","utility",18,8,70,0)]),
            ("Frigate", 700, 1100, 500, [
                ("Autocannon","Kinetic",32,2,"S",0,"Fusion Shell S"), ("Autocannon","Kinetic",32,2,"S",0,"Fusion Shell S"),
                ("Missile Launcher","Explosive",40,6,"S",3,"Inferno Rocket S"),
            ], 135, 38, 350, 4, []),
            ("Fighter", 450, 350, 350, [
                ("Pulse Laser","Thermal",22,2,"S",8,""), ("Pulse Laser","Thermal",22,2,"S",8,""),
            ], 220, 23, 300, 6, []),
            ("Destroyer", 1400, 1600, 900, [
                ("Railgun","Kinetic",70,5,"L",12,"Spike Charge L"), ("Missile Launcher","Explosive",50,7,"M",4,"Inferno Missile M"),
                ("Flak Battery","Kinetic",18,1,"S",0,"Fusion Shell S"),
            ], 88, 68, 550, 5, [("Armor Repairer","utility",16,8,0,55)]),
            ("Frigate", 800, 700, 450, [
                ("Beam Laser","EM",45,3,"M",14,""), ("Beam Laser","EM",45,3,"M",14,""),
            ], 105, 43, 550, 6, []),
        ],
    }
    templates = configs.get(style, configs["balanced"])
    hull_names = {
        "shield_heavy": ["Phantom","Bulwark","Viper","Tempest","Javelin"],
        "armor_heavy": ["Sentinel","Mauler","Dart","Hammer","Spike"],
        "balanced": ["Centurion","Hornet","Wasp","Tribune","Axiom"],
    }.get(style, ["Ship"]*5)
    for i in range(size):
        t = templates[i % len(templates)]
        hull, sh, ar, hu, wpn_defs, spd, sig, cap, cap_r, mod_defs = t
        ship_name = hull_names[i % len(templates)]
        # Range by weapon size: S=1-3km, M=5-10km, L=15-25km
        range_table = {'S': 2500, 'M': 7500, 'L': 20000}
        tracking_table = {'S': 80, 'M': 50, 'L': 25}
        wpns = [make_weapon(n, dt, dmg, cyc, tracking_table.get(sz,60), range_table.get(sz,7500), sz, cap_use=cu, ammo_id=aid)
                for n, dt, dmg, cyc, sz, cu, aid in wpn_defs]
        mods = [make_module(mn, ms, mc, mcy, shield_boost=msb, armor_repair=mar)
                for mn, ms, mc, mcy, msb, mar in mod_defs]
        ammo = {}
        for w in wpns:
            if w.ammo_id:
                ammo[w.ammo_id] = ammo.get(w.ammo_id, 0) + 150
        display_name = f"{ship_name} ({hull}) {i+1}"
        ships.append(make_ship(f"{prefix}_{i}", display_name, faction, hull,
                               shield=sh, armor=ar, hull=hu, weapons=wpns, speed=spd, signature=sig,
                               cap=cap, cap_recharge=cap_r, modules=mods, ammo=ammo))
    return ships


def create_3faction_battle():
    fleet_tf = make_fleet("Terran Federation", "tf", 7, "shield_heavy")
    fleet_fs = make_fleet("Free States", "fs", 5, "balanced")
    fleet_ic = make_fleet("Iron Compact", "ic", 10, "armor_heavy")
    return fleet_tf, fleet_fs, fleet_ic


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/control')
def control():
    cmd = request.args.get('cmd', '')
    if cmd == 'pause':
        battle_state['paused'] = not battle_state['paused']
    elif cmd == 'stop':
        battle_state['stop'] = True
    elif cmd == 'restart':
        battle_state['stop'] = True
        battle_state['restart'] = True
    return 'ok'


@app.route('/stream')
def stream():
    def generate():
        battle_state['paused'] = False
        battle_state['stop'] = False
        battle_state['restart'] = False

        fleet_tf, fleet_fs, fleet_ic = create_3faction_battle()
        allied = fleet_tf + fleet_fs
        engine = CombatEngine(allied, fleet_ic)

        def ship_data(s):
            return {"id":s.id,"name":s.name,"hull_class":s.hull_class,
                    "shield":s.shield_max,"armor":s.armor_max,"hull":s.hull_max,
                    "cap":s.cap_max,"cap_recharge":s.cap_recharge,
                    "weapons":[{"name":w.name,"size":w.size,"dmg":w.damage_type.value,"cycle":w.cycle_time,"cap_use":w.cap_use,"ammo":w.ammo_id} for w in s.weapons],
                    "modules":[{"name":m.name,"type":m.slot} for m in s.modules],
                    "ammo": dict(s.ammo)}

        init_data = {"type": "init", "fleets": [
            {"faction":"Terran Federation","count":len(fleet_tf),"ally":"Free States","ships":[ship_data(s) for s in fleet_tf]},
            {"faction":"Free States","count":len(fleet_fs),"ally":"Terran Federation","ships":[ship_data(s) for s in fleet_fs]},
            {"faction":"Iron Compact","count":len(fleet_ic),"ships":[ship_data(s) for s in fleet_ic]},
        ]}
        yield f"data: {json.dumps(init_data)}\n\n"
        time.sleep(1)

        all_ships = allied + fleet_ic
        while not engine.finished and engine.tick < 600 and not battle_state['stop']:
            while battle_state['paused'] and not battle_state['stop']:
                time.sleep(0.2)

            if battle_state['stop']:
                break

            events = engine.step()

            # Send cap state + positions + velocities for all alive ships each tick
            caps = {s.id: round(s.cap, 1) for s in all_ships if s.alive}
            positions = {s.id: [round(s.x), round(s.y), round(s.vx,1), round(s.vy,1)] for s in all_ships if s.alive}
            msls = []
            for m in engine.missiles:
                target = next((s for s in all_ships if s.id == m.target_id), None)
                if target:
                    dx = target.x - m.x
                    dy = target.y - m.y
                    d = (dx*dx+dy*dy)**0.5 or 1
                    msls.append({"x":round(m.x),"y":round(m.y),"vx":round(dx/d*m.speed,1),"vy":round(dy/d*m.speed,1)})
                else:
                    msls.append({"x":round(m.x),"y":round(m.y),"vx":0,"vy":0})
            tick_data = {'type':'tick','tick':engine.tick,'ship_caps':caps,'pos':positions,'msls':msls}
            yield f"data: {json.dumps(tick_data)}\n\n"

            for e in events:
                evt = {'tick':e.tick,'event':e.event,'source_id':e.source_id,'target_id':e.target_id,
                       'weapon':e.weapon,'damage':e.damage,'damage_type':e.damage_type,
                       'remaining_hp':e.remaining_hp,'detail':e.detail}
                yield f"data: {json.dumps({'type':'event','event':evt})}\n\n"

            time.sleep(1)

        result = engine.summary()
        yield f"data: {json.dumps({'type':'end','winner':result['winner'],'ticks':engine.tick})}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


if __name__ == '__main__':
    print("Combat Simulator running at http://localhost:5555")
    print("Controls: Pause | Restart | Stop")
    app.run(port=5555, threaded=True)
