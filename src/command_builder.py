def shell_quote(s):
    return "'" + str(s).replace("'", "'\\''") + "'"

def build_cmd(g):
    o = g.get('launchOpts') or {}
    game_env = {}
    if o.get('mangohud'):   game_env['MANGOHUD'] = '1'
    if o.get('winefsr'):    game_env['WINE_FULLSCREEN_FSR'] = '1'
    lsfg = o.get('lsfg')
    if lsfg:
        if lsfg.get('profile'):  game_env['LSFGVK_PROFILE'] = lsfg['profile']
        if lsfg.get('legacy') and lsfg.get('legacyProfile'):
            game_env['LSFG_PROCESS'] = lsfg['legacyProfile']
    for pair in (o.get('env') or []):
        if pair.get('k'): game_env[pair['k']] = pair.get('v', '')

    gs = o.get('gamescope')
    if gs:
        gs_env = {}
        if gs.get('wsi') is False: gs_env['ENABLE_GAMESCOPE_WSI'] = '0'
        gscmd = 'gamescope'
        if gs.get('gw') and gs.get('gh'): gscmd += f" -w {gs['gw']} -h {gs['gh']}"
        if gs.get('ww') and gs.get('wh'): gscmd += f" -W {gs['ww']} -H {gs['wh']}"
        if gs.get('fs'):     gscmd += ' -f'
        if gs.get('gk'):     gscmd += ' --grab'
        if gs.get('gc'):     gscmd += ' --force-grab-cursor'
        if gs.get('ma'):     gscmd += ' --mangoapp'
        if gs.get('filter'): gscmd += f" --filter {gs['filter']}"
        gs_part   = ' '.join(f"{k}={shell_quote(v)}" for k,v in gs_env.items())
        game_part = ' '.join(f"{k}={shell_quote(v)}" for k,v in game_env.items())
        before = f"env {gs_part} " if gs_part else ""
        after  = f"env {game_part} " if game_part else ""
        return f"{before}{gscmd} -- {after}{g['exec']}".strip()

    game_part = ' '.join(f"{k}={shell_quote(v)}" for k,v in game_env.items())
    after = f"env {game_part} " if game_part else ""
    return f"{after}{g['exec']}".strip()
