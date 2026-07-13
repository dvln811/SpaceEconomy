lines = open('warp_game_work.html','r',encoding='utf-8').readlines()

new_approach = '''      // APPROACH: distance-based (like warp_test). Spawns while SSG still moving.
      const approachTriggerKm = Math.max(10000, (window._warpOrbitOffsetKm || 50000) * 3);
      const approachSpawnUnits = approachTriggerKm * 10;
      const remainingAU = window._warpTotalDist - Math.min(dist, window._warpTotalDist);
      const remainingKm = remainingAU * 150000000;
      
      if(!window._approachStarted && window._departDone && remainingKm <= approachTriggerKm){
        window._approachStarted = true;
        if(!lsgGroup){ lsgGroup = new THREE.Group(); scene.add(lsgGroup); }
        const targetObj = localState.objects.find(o => o.id === warpTargetId);
        if(targetObj && targetObj.station_id && stationModels[targetObj.station_id]){
          const m = stationModels[targetObj.station_id];
          m.position.set(0, 0, 0); m.visible = true; lsgGroup.add(m);
        } else if(targetObj && targetObj.type === 'gate' && gateModels[targetObj.id]){
          const m = gateModels[targetObj.id];
          m.position.set(0, 0, 0); m.visible = true; lsgGroup.add(m);
        }
        const toX = targetObj.ss_x - window._playerSS.x;
        const toY = (targetObj.ss_y||0) - (window._playerSS.y||0);
        const toZ = targetObj.ss_z - window._playerSS.z;
        const toLen = Math.sqrt(toX*toX + toY*toY + toZ*toZ) || 1;
        window._lsgApproachDir = {x:toX/toLen, y:toY/toLen, z:toZ/toLen};
        window._approachTriggerKm = approachTriggerKm;
        window._approachSpawnUnits = approachSpawnUnits;
      }
      
      // SLIDE LSG based on remaining distance
      if(window._approachStarted && lsgGroup){
        const trigKm = window._approachTriggerKm || 10000;
        const spawnU = window._approachSpawnUnits || 100000;
        const t2 = 1 - Math.min(1, remainingKm / trigKm);
        const pos = spawnU + (LSG_STOP_DIST - spawnU) * t2;
        const dir = window._lsgApproachDir || {x:warpHeading.x, y:warpHeading.y, z:warpHeading.z};
        lsgGroup.position.set(dir.x * pos, dir.y * pos, dir.z * pos);
      }

'''

lines[1110:1156] = [new_approach]
open('warp_game_work.html','w',encoding='utf-8').writelines(lines)
print('Done')
