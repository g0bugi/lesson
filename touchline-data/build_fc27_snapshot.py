import json, time, urllib.parse, urllib.request
from pathlib import Path

BASE='https://drop-api.ea.com/rating/ea-sports-fc'
OUT=Path(__file__).resolve().parent
TARGET={'Premier League':'Premier League','LALIGA EA SPORTS':'LaLiga','Bundesliga':'Bundesliga',"Ligue 1 McDonald's":'Ligue 1','Serie A Enilive':'Serie A','Serie A':'Serie A'}
HEADERS={'Accept':'application/json,text/plain,*/*','Origin':'https://www.ea.com','Referer':'https://www.ea.com/','User-Agent':'Mozilla/5.0 TOUCHLINE-Snapshot/1.0'}

def fetch_page(offset, retries=8):
    q=urllib.parse.urlencode({'locale':'en','limit':100,'gender':0,'offset':offset})
    req=urllib.request.Request(BASE+'?'+q, headers=HEADERS)
    last=None
    for attempt in range(1,retries+1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last=e
            time.sleep(min(20, 1.5*attempt*attempt))
    raise RuntimeError(f'offset {offset}: {last}')

def v(stats,key):
    x=(stats or {}).get(key)
    return x.get('value') if isinstance(x,dict) else None

def clean(p):
    s=p.get('stats') or {}
    return {
      'id':p.get('id'),'name':p.get('commonName') or ' '.join(x for x in [p.get('firstName'),p.get('lastName')] if x),
      'first_name':p.get('firstName'),'last_name':p.get('lastName'),'common_name':p.get('commonName'),
      'league_name':p.get('leagueName'),'league':TARGET.get(p.get('leagueName')),
      'team_label':(p.get('team') or {}).get('label',''),'position_short_label':(p.get('position') or {}).get('shortLabel',''),
      'nationality_label':(p.get('nationality') or {}).get('label',''),'overall_rating':p.get('overallRating'),
      'preferred_foot':p.get('preferredFoot'),'skill_moves':p.get('skillMoves'),'weak_foot':p.get('weakFootAbility'),
      'alternate_positions':[x.get('shortLabel') for x in (p.get('alternatePositions') or []) if x and x.get('shortLabel')],
      **{f'stat_{k}':v(s,k) for k in ['pac','sho','pas','dri','def','phy','acceleration','sprint_speed','positioning','finishing','shot_power','long_shots','volleys','penalties','vision','crossing','free_kick_accuracy','short_passing','long_passing','curve','agility','balance','reactions','ball_control','dribbling','composure','interceptions','heading_accuracy','defensive_awareness','standing_tackle','sliding_tackle','jumping','stamina','strength','aggression','gk_diving','gk_handling','gk_kicking','gk_positioning','gk_reflexes']}
    }

def main():
    all_count=0; big5=[]; offset=0; seen=set(); started=time.time()
    while True:
        data=fetch_page(offset); items=data.get('items') or []
        if not items: break
        all_count += len(items)
        for p in items:
            if p.get('leagueName') in TARGET:
                row=clean(p)
                if row['id'] not in seen:
                    seen.add(row['id']); big5.append(row)
        print(f'offset={offset} page={len(items)} total={all_count} big5={len(big5)}', flush=True)
        if len(items)<100: break
        offset += 100
        time.sleep(1.2)
    big5.sort(key=lambda x:(['Premier League','LaLiga','Bundesliga','Ligue 1','Serie A'].index(x['league']) if x['league'] in ['Premier League','LaLiga','Bundesliga','Ligue 1','Serie A'] else 99, x['team_label'], -(x['overall_rating'] or 0), x['name']))
    clubs={}
    for p in big5: clubs.setdefault(p['league'],set()).add(p['team_label'])
    manifest={'source':'EA SPORTS FC official Ratings API','season':'2026/27','generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'all_male_rows_seen':all_count,'big5_players':len(big5),'clubs_by_league':{k:len(v) for k,v in clubs.items()},'elapsed_seconds':round(time.time()-started,1)}
    (OUT/'fc27-big5.json').write_text(json.dumps({'manifest':manifest,'players':big5},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
