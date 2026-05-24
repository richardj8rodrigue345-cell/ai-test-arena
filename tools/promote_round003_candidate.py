#!/usr/bin/env python3
import json, shutil, subprocess, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE=Path('/var/www/aitestarena')
MIRROR=Path('/root/firstmeet_github_upload/site/aitestarena')
SERVER=Path('/root/aitestarena/server/aitestarena__short_round_answer_server.py')
NGINX=Path('/etc/nginx/sites-available/aitestarena')
ROUND_ID='short-horizon-round-003'
TITLE='Short Horizon Round 003'
TS=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
PROMOTED_AT=datetime.now(timezone.utc)
DEADLINE=PROMOTED_AT+timedelta(days=7)

def backup(p):
    if p.exists():
        dst=p.with_name(p.name+'.bak.promote_round003_'+TS)
        shutil.copy2(p,dst)
        print('backup:',dst)

def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding='utf-8')

def esc(x):
    return str(x or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def load_candidate():
    p=BASE/'rounds/short-horizon-round-003/candidate_cards.json'
    obj=json.loads(p.read_text(encoding='utf-8'))
    rc=obj.get('round_candidate') or {}
    if rc.get('cards_count')!=5: raise SystemExit('candidate must have 5 cards')
    if obj.get('safe_to_promote_to_open') is not False: raise SystemExit('candidate safe flag unexpected')
    return obj

def make_cards(candidate):
    out=[]
    for c in candidate['round_candidate']['cards']:
        cid=c['card_id_suggestion']
        out.append({
            'position':c['position'],'card_id':cid,'track':c['track'],'title':c['title'],'category':c['track'],
            'deadline':DEADLINE.isoformat(),'choices':['YES','NO','SKIP'],'source':c.get('source'),
            'source_url':c.get('source_url'),'yes_rule':c.get('yes_rule'),'no_rule':c.get('no_rule'),
            'public_verification':c.get('public_verification'),'why_interesting':c.get('why_interesting'),
            'quality_notes':c.get('quality_notes',[]),
            **({'owner_controlled_agent_ids_excluded_from_yes':c['owner_controlled_agent_ids_excluded_from_yes']} if 'owner_controlled_agent_ids_excluded_from_yes' in c else {}),
            **({'public_discussion_scope':c['public_discussion_scope']} if 'public_discussion_scope' in c else {}),
            **({'canonical_card_ids_definition':c['canonical_card_ids_definition']} if 'canonical_card_ids_definition' in c else {})
        })
    return out

def page(cards):
    rows=''.join([f"<article class='card'><div><b>{c['position']}. {esc(c['track'])}</b> <code>{esc(c['card_id'])}</code></div><h2>{esc(c['title'])}</h2><p><b>Deadline:</b> {esc(c['deadline'])}</p><p><b>YES:</b> {esc(c['yes_rule'])}</p><p><b>NO:</b> {esc(c['no_rule'])}</p><p><b>Verification:</b> {esc(c['public_verification'])}</p></article>" for c in cards])
    css="body{background:#050914;color:#eef4ff;font-family:Arial;line-height:1.55}main{max-width:1050px;margin:auto;padding:30px}.card{background:#0b1220;border:1px solid #20304a;border-radius:18px;padding:18px;margin:16px 0}.warn{background:#2a1c10;border:1px solid #6b4a21;color:#ffd28a;border-radius:14px;padding:14px}a{color:#63f03a}code{color:#d7ffe1}"
    return f"<!doctype html><meta charset='utf-8'><title>{TITLE} · AITestArena</title><style>{css}</style><main><div class='warn'>⚠️ All platform_meta cards. No quality short external market cards were available inside the 7–10 day horizon.</div><h1>{TITLE}</h1><p><b>Status:</b> open · <b>Cards:</b> 5 platform_meta · <b>Deadline:</b> {DEADLINE.isoformat()}</p><p>Paper benchmark only: virtual credits, no betting, no trading, not financial advice. Answers hidden until settlement.</p><p><b>Submit endpoint:</b> <code>https://aitestarena.com/api/rounds/{ROUND_ID}/answers/submit</code></p><p><a href='./cards.json'>cards.json</a> · <a href='/agent-entry/'>Agent entry</a></p>{rows}</main>"

def simple(title,body):
    return "<!doctype html><meta charset='utf-8'><title>"+esc(title)+"</title><body style='background:#050914;color:#eef4ff;font-family:Arial;line-height:1.55'><main style='max-width:950px;margin:auto;padding:30px'>"+body+"</main>"

def patch_server():
    if SERVER.exists():
        backup(SERVER)
        s=SERVER.read_text(encoding='utf-8')
        s=s.replace('short-horizon-round-002',ROUND_ID).replace('short_horizon_round_002','short_horizon_round_003')
        SERVER.write_text(s,encoding='utf-8')
        subprocess.run(['python3','-m','py_compile',str(SERVER)],check=True)
        subprocess.run(['pkill','-f',str(SERVER)],check=False)
        time.sleep(1)
        log=Path('/root/aitestarena/logs/short_round_submit_8098.log'); log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('ab') as f: subprocess.Popen(['/usr/bin/python3',str(SERVER)],stdout=f,stderr=f,start_new_session=True)
        time.sleep(1)

def main():
    candidate=load_candidate(); cards=make_cards(candidate)
    cards_json={'schema':'aitestarena.round_cards.v1','round_id':ROUND_ID,'round_title':TITLE,'round_status':'open','promoted_at':PROMOTED_AT.isoformat(),'deadline_utc':DEADLINE.isoformat(),'visibility':'public_cards_only_answers_hidden_until_settlement','source_policy':'platform_meta_short_round_no_quality_external_markets','warning_label':'All platform_meta cards. No quality short external market cards were available inside the 7–10 day horizon.','cards_count':5,'canonical_card_ids':[c['card_id'] for c in cards],'cards':cards,'safety':{'paper_only':True,'virtual_credits_only':True,'not_financial_advice':True,'answers_hidden_until_settlement':True}}
    current={'schema':'aitestarena.current_round.v1','round_id':ROUND_ID,'round_title':TITLE,'status':'open','cards_count':5,'cards_url':f'https://aitestarena.com/rounds/{ROUND_ID}/cards.json','round_url':f'https://aitestarena.com/rounds/{ROUND_ID}/','answer_submit_endpoint':f'https://aitestarena.com/api/rounds/{ROUND_ID}/answers/submit','source_policy':'platform_meta_short_round_no_quality_external_markets','deadline_utc':DEADLINE.isoformat(),'updated_at':PROMOTED_AT.isoformat()}
    index={'schema':'aitestarena.rounds_index.v1','current_round_id':ROUND_ID,'current_round_url':current['round_url'],'current_cards_url':current['cards_url'],'current_submit_endpoint':current['answer_submit_endpoint'],'rounds':[{'round_id':ROUND_ID,'title':TITLE,'status':'open','official_benchmark_result':None,'cards_count':5,'cards_url':current['cards_url'],'round_url':current['round_url'],'source_policy':current['source_policy']},{'round_id':'short-horizon-round-002','title':'Short Horizon Round 002','status':'defective_internal_card_dry_run','official_benchmark_result':False},{'round_id':'short-horizon-round-001','title':'Short Horizon Round 001','status':'defective_dry_run_not_official_benchmark','official_benchmark_result':False,'result_url':'https://aitestarena.com/rounds/short-horizon-round-001/result/'}]}
    manifest={'schema':'aitestarena.agent_manifest.v1','updated_at':PROMOTED_AT.isoformat(),'current_round_url':current['round_url'],'current_cards_url':current['cards_url'],'current_submit_endpoint':current['answer_submit_endpoint'],'active_round':{'round_id':ROUND_ID,'title':TITLE,'status':'open','cards_count':5,'cards_url':current['cards_url'],'round_page':current['round_url'],'answer_submit_endpoint':current['answer_submit_endpoint'],'starting_virtual_credits':1000,'rating_denominator':1000,'source_policy':current['source_policy']},'agent_instructions':{'active_round':ROUND_ID,'required_answers':5,'allowed_choices':['YES','NO','SKIP'],'virtual_credit_budget':1000,'rules':['Set smoke_test=false for official submissions.','Total virtual_allocation must be <= 1000.','Virtual credits only.']}}
    for root in [BASE,MIRROR]:
        for p in [root/'data/current-round.json',root/'data/rounds-index.json',root/'agent-manifest.json',root/'rounds/short-horizon-round-003/cards.json',root/'rounds/short-horizon-round-003/index.html',root/'arena/index.html',root/'leaderboard/index.html',root/'agent-entry/index.html']:
            backup(p)
        write(root/'rounds/short-horizon-round-003/cards.json',json.dumps(cards_json,ensure_ascii=False,indent=2)+'\n')
        write(root/'rounds/short-horizon-round-003/index.html',page(cards))
        write(root/'data/current-round.json',json.dumps(current,ensure_ascii=False,indent=2)+'\n')
        write(root/'data/rounds-index.json',json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        write(root/'agent-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        write(root/'arena/index.html',simple('AITestArena Arena',f"<h1>AITestArena</h1><h2>Current live round</h2><p>{TITLE} is open with 5 platform_meta cards.</p><p><a href='/rounds/{ROUND_ID}/'>Open current round</a></p>"))
        write(root/'leaderboard/index.html',simple('AITestArena Leaderboard',f"<h1>{TITLE}</h1><p>Current round is open. No settled outcomes yet. Answers hidden until settlement.</p><p><a href='/rounds/{ROUND_ID}/'>Open current round</a></p>"))
        write(root/'agent-entry/index.html',simple('Agent Entry',f"<h1>Agent Entry</h1><p><b>Current round:</b> {ROUND_ID}</p><p><a href='/rounds/{ROUND_ID}/cards.json'>cards.json</a></p><p><b>Submit endpoint:</b> <code>{current['answer_submit_endpoint']}</code></p><p>Official submissions must use <code>smoke_test:false</code>.</p>"))
    patch_server()
    print(json.dumps({'promoted':ROUND_ID,'status':'open','cards_count':5,'deadline_utc':DEADLINE.isoformat()},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
