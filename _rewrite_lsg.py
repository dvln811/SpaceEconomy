lines = open('warp_game_work.html','r',encoding='utf-8').readlines()

new_lsg = '''      // ── LSG (departure, approach, completion) ──
      const LSG_SPAWN_DIST = 500000; // 50,000 km in scene units
      const LSG_STOP_DIST = 100;     // 10 km in scene units

      // DEPARTURE: slide current LSG away
      if(!window._departDone){
        if(!window._lsgDepartStart) window._lsgDepartStart = t;
        const departT = (t - window._lsgDepartStart) / 3.0;
        if(departT < 1.0 && lsgGroup && lsgGroup.children.length > 0){
          window._ssgFrozen = true;
          const d = Math.pow(departT, 4) * LSG_SPAWN_DIST;
          if(!window._lsgStartPos) window._lsgStartPos = lsgGroup.position.clone();
          lsgGroup.position.copy(window._lsgStartPos).addScaledVector(warpHeading, -d);
        } else {
          window._departDone = true;
          window._ssgFrozen = false;
          window._lsgStartPos = null;
          if(lsgGroup) while(lsgGroup.children.length) lsgGroup.remove(lsgGroup.children[0]);
        }
      }

      // SSG POSITION (only when not frozen)
      if(!window._ssgFrozen){
        const cd = Math.min(dist, window._warpTotalDist);
        window._playerSS.x = window._warpFromSS.x + warpHeading.x * cd;
        window._playerSS.y = (window._warpFromSS.y||0) + warpHeading.y * cd;
        window._playerSS.z = window._warpFromSS.z + warpHeading.z * cd;
      }

      // APPROACH: when SSG done, spawn LSG, slide to ship
      if(!window._approachStarted && window._departDone && dist >= window._warpTotalDist){
        window._approachStarted = true;
        window._ssgFrozen = true;
        window._approachStart = t;
        if(!lsgGroup){ lsgGroup = new THREE.Group(); scene.add(lsgGroup); }
        // Spawn ALL objects at correct scale
        const targetObj = localState.objects.find(o => o.id === warpTargetId);
        if(targetObj && targetObj.station_id && stationModels[targetObj.station_id]){
          const m = stationModels[targetObj.station_id];
          m.position.set(0, 0, 0); m.visible = true; lsgGroup.add(m);
        } else if(targetObj && targetObj.type === 'gate' && gateModels[targetObj.id]){
          const m = gateModels[targetObj.id];
          m.position.set(0, 0, 0); m.visible = true; lsgGroup.add(m);
        }
        lsgGroup.position.set(warpHeading.x * LSG_SPAWN_DIST, warpHeading.y * LSG_SPAWN_DIST, warpHeading.z * LSG_SPAWN_DIST);
      }

      // SLIDE LSG to ship
      if(window._approachStarted && lsgGroup){
        const at = Math.min(1, (t - window._approachStart) / 4.0);
        const eased = 1 - Math.pow(1 - at, 3);
        const pos = LSG_SPAWN_DIST + (LSG_STOP_DIST - LSG_SPAWN_DIST) * eased;
        lsgGroup.position.set(warpHeading.x * pos, warpHeading.y * pos, warpHeading.z * pos);

        // COMPLETION
        if(at >= 1.0){
          if(localState && localState.objects){
            localState.objects.forEach(o => o.is_anchor = false);
            const d2 = localState.objects.find(o => o.id === warpTargetId);
            if(d2) d2.is_anchor = true;
          }
          playerHeading.copy(warpHeading);
          playerSpeed = 0;
          warpState = 'none';
          warpTargetId = null;
          warpTargetPos = null;
          window._ssgFrozen = false;
          window._approachStarted = false;
          window._approachStart = null;
          window._departDone = false;
          window._lsgDepartStart = null;
          window._warpPhases = null;
          document.getElementById('warpTarget').textContent = '';
          if(warpStreaks) warpStreaks.visible = false;
        }
      }

'''

lines[1078:1182] = [new_lsg]
open('warp_game_work.html','w',encoding='utf-8').writelines(lines)
print('Done - replaced LSG section')
