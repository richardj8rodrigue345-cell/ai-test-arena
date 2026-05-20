#!/usr/bin/env python3
import json, re, urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROUND_ID='short-horizon-round-003'
TITLE='Short Horizon Round 003'
OUT_DIRS=[Path('/var/www/aitestarena/rounds/short-horizon-round-003'),Path('/root/firstmeet_github_upload/site/aitestarena/rounds/short-horizon-round-003')]

def fetch_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':'AITestArena candidate generator','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=25) as r:
        return json.loads(r.read().decode('utf-8'))

def dt(x):
    if not x:return None
    try:
        d=datetime.fromisoformat(str(x).replace('Z','+00:00'))
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception:
        return None

def clean(x): return re.sub(r'\s+',' ',str(x or '')).strip()
def slug(x): return re.sub(r'[^a-zA-Z0-9]+','-',x.lower()).strip('-')[:70] or 'card'
def bad(q):
    ql=q.lower().strip()
    if len(q)<28:return True
    if ql.startswith(('yes ','no ','yes$','no$','yes $','no $')):return True
    if ql.count('yes ')+ql.count('no ')>=2:return True
    for b in ['aitestarena','agent register','forecast submission','validation issue','github repository','virtual credit budget','smoke test','non-smoke']:
        if b in ql:return True
    return False

def poly_url(m):
    if m.get('slug'): return 'https://polymarket.com/event/'+str(m['slug']).strip('/')
    if m.get('marketSlug'): return 'https://polymarket.com/event/'+str(m['marketSlug']).strip('/')
    if m.get('conditionId'): return 'https://polymarket.com/market/'+str(m['conditionId'])
    if m.get('id'): return 'https://polymarket.com/market/'+str(m['id'])
    return 'https://polymarket.com/'

def poly_deadline(m):
    for k in ['endDate','endDateIso','end_date','close_time','expiration_time']:
        d=dt(m.get(k))
        if d:return d
    return None

def volume(m):
    for k in ['volumeNum','volume','liquidityNum','liquidity','open_interest']:
        try:return float(m.get(k) or 0)
        except Exception:pass
    return 0.0

def load_poly(days):
    now=datetime.now(timezone.utc); maxd=now+timedelta(days=days)
    rows=[]; errors=[]; rejected=[]
    for url in ['https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500','https://gamma-api.polymarket.com/markets?closed=false&limit=500']:
        try:
            obj=fetch_json(url); rows += obj if isinstance(obj,list) else (obj.get('markets') or obj.get('data') or [])
        except Exception as e: errors.append({'url':url,'error':repr(e)})
    out=[]; seen=set()
    for m in rows:
        q=clean(m.get('question') or m.get('title') or m.get('name'))
        if not q or q in seen: continue
        seen.add(q); d=poly_deadline(m); u=poly_url(m)
        if bad(q): rejected.append({'title':q,'source_url':u,'reason':'bad title'}); continue
        if not d or d<=now or d>maxd: rejected.append({'title':q,'source_url':u,'reason':'outside short horizon'}); continue
        out.append({'title':q,'deadline':d,'source':'polymarket','source_url':u,'volume':volume(m)})
    out.sort(key=lambda x:(x['deadline'],-x['volume']))
    return out[:3], rejected[:25], errors

def meta_pool(deadline_iso):
    return [
        ('short-003-meta-01-three-valid-agent-submissions','Will at least 3 unique AI agents submit valid Round 003 forecasts before the deadline?','YES if at least 3 unique non-smoke agent_ids have accepted valid Round 003 forecast submissions before the deadline.','NO if fewer than 3 unique non-smoke agent_ids have accepted valid Round 003 forecast submissions before the deadline.','Measures whether the round attracted enough real agent participation to be useful.'),
        ('short-003-meta-02-one-external-agent-submission','Will at least 1 non-owner external AI agent submit a valid Round 003 forecast before the deadline?','YES if at least one accepted non-smoke Round 003 forecast is submitted by an agent not controlled by the site owner/operator before the deadline.','NO if no non-owner external AI agent submits an accepted non-smoke Round 003 forecast before the deadline.','Separates real third-party interest from owner-operated/demo-agent activity.'),
        ('short-003-meta-03-two-model-providers','Will Round 003 receive valid forecasts from at least 2 different model providers before the deadline?','YES if accepted non-smoke submissions include at least 2 distinct model/provider labels.','NO if submissions come from fewer than 2 distinct model/provider labels before the deadline.','Tests whether the benchmark attracts more than one model family.'),
        ('short-003-meta-04-public-discussion','Will Round 003 receive at least 1 public external mention or discussion before the deadline?','YES if at least one public non-owner post, comment, article, issue, or social mention links to or clearly discusses Round 003 before the deadline.','NO if no public non-owner external mention/discussion is found before the deadline.','Measures whether the round creates visible outside attention.'),
    ]

def make_pack(days):
    now=datetime.now(timezone.utc); ext,rejected,errors=load_poly(days)
    deadline=max([x['deadline'] for x in ext]+[now+timedelta(days=min(7,days))]) if ext else now+timedelta(days=min(7,days))
    cards=[]
    for i,x in enumerate(ext,1):
        cards.append({'position':i,'track':'external_market','card_id_suggestion':f"short-003-ext-{i:02d}-{slug(x['title'])}",'title':x['title'],'source':x['source'],'source_url':x['source_url'],'deadline_utc':x['deadline'].isoformat(),'yes_rule':'YES if the linked public market resolves YES according to the public market/source outcome.','no_rule':'NO if the linked public market resolves NO or does not meet the YES condition by settlement.','public_verification':'Verify through the linked public market page and settlement note.','why_interesting':'External public-event calibration card.','quality_notes':[]})
    for cid,title,yes,no,why in meta_pool(deadline.isoformat())[:max(0,5-len(cards))]:
        cards.append({'position':len(cards)+1,'track':'platform_meta','card_id_suggestion':cid,'title':title,'source':'aitestarena_public_status','source_url':'https://aitestarena.com/leaderboard/','deadline_utc':deadline.isoformat(),'yes_rule':yes,'no_rule':no,'public_verification':'Verify through the public Round 003 final status/leaderboard or settlement report.','why_interesting':why,'quality_notes':['platform_meta card','smoke tests excluded']})
    status='OK' if len(cards)==5 and len(ext)>=1 else 'WARN'
    return {'schema':'aitestarena.round_candidate_pack.v1','audit_id':'candidate-pack-'+now.strftime('%Y%m%d-%H%M%S'),'status':status,'summary':f"Short hybrid candidate: {len(ext)} external_market + {len(cards)-len(ext)} platform_meta; horizon {days} days.",'generated_at':now.isoformat(),'round_candidate':{'round_id_suggestion':ROUND_ID,'round_title':TITLE,'status':'candidate_pending_review','recommended_deadline_utc':deadline.isoformat(),'cards_count':len(cards),'mix':{'external_market':len(ext),'platform_meta':len(cards)-len(ext)},'cards':cards},'rejected_candidates':rejected,'source_errors':errors,'quality_check':{'short_horizon_days':days,'no_machine_fragments':all(not bad(c['title']) for c in cards),'tracks_clearly_labeled':all(c['track'] in ['external_market','platform_meta'] for c in cards),'external_cards_found':len(ext),'total_cards_target':5},'safe_to_promote_to_open':False,'requires_human_approval':True,'next_actions':['DeepSeek audits candidate_cards.json.','Owner approves or rejects.','Only after approval, promote to current/open.']}

def render(pack):
    rows=''.join([f"<article class='card'><div><b>{c['position']}. {c['track']}</b></div><h2>{c['title']}</h2><p><b>Source:</b> <a href='{c['source_url']}'>{c['source']}</a></p><p><b>Deadline:</b> {c['deadline_utc']}</p><p><b>YES:</b> {c['yes_rule']}</p><p><b>NO:</b> {c['no_rule']}</p></article>" for c in pack['round_candidate']['cards']])
    return "<!doctype html><meta charset='utf-8'><title>Round003 candidate</title><style>body{background:#050914;color:#eef4ff;font-family:Arial;line-height:1.55}main{max-width:1000px;margin:auto;padding:30px}.card{background:#0b1220;border:1px solid #20304a;border-radius:18px;padding:18px;margin:16px 0}a{color:#63f03a}</style><main><h1>Round003 candidate cards</h1><p>candidate_pending_review · safe_to_promote_to_open=false</p>"+rows+"</main>"

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--deadline-days',type=int,default=10); args=ap.parse_args()
    pack=make_pack(args.deadline_days)
    for d in OUT_DIRS:
        d.mkdir(parents=True,exist_ok=True)
        (d/'candidate_cards.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (d/'candidate_cards.html').write_text(render(pack),encoding='utf-8')
    print(json.dumps({'status':pack['status'],'summary':pack['summary'],'cards_count':pack['round_candidate']['cards_count'],'mix':pack['round_candidate']['mix'],'candidate_json':[str(d/'candidate_cards.json') for d in OUT_DIRS]},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
