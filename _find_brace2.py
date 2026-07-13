lines = open('warp_game_work.html','r',encoding='utf-8').readlines()
# Find the warp block opening brace
for i,l in enumerate(lines):
    if 'else if(warpState' in l and 'warping' in l:
        print(f'Line {i+1}: {l.rstrip()[:80]}')
        # Count from next line
        depth = 1  # the { on this line
        for j in range(i+1, min(i+300, len(lines))):
            depth += lines[j].count('{') - lines[j].count('}')
            if depth == 0:
                print(f'Block closes at line {j+1}: {lines[j].rstrip()[:80]}')
                break
            if depth < 0:
                print(f'EXTRA }} at line {j+1}: {lines[j].rstrip()[:80]}')
                break
        break
