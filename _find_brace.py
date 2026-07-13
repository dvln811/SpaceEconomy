lines = open('warp_game_work.html','r',encoding='utf-8').readlines()
in_warp = False
depth = 0
for i,l in enumerate(lines):
    if 'else if(warpState' in l and 'warping' in l:
        in_warp = True; depth = 0; start = i
        print(f'Warp starts at line {i+1}')
    if in_warp:
        depth += l.count('{') - l.count('}')
        if depth <= 0 and i > start:
            print(f'Warp block closes at line {i+1}, depth={depth}')
            break
