#!/usr/bin/env python3
"""Fill Round003 candidate with 5 platform_meta cards when no quality short external cards exist.
Does not open the round and does not touch current-round.json.
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROUND_ID='short-horizon-round-003'
TITLE='Short Horizon Round 003'
OUT_DIRS=[Path('/var/www/aitestarena/rounds/short-horizon-round-003'),Path('/root/firstmeet_github_upload/site/aitestarena/rounds/short-horizon-round-003')]
now=datetime.now(timezone.utc)
deadline=now+timedelta(days=7)
deadline_iso=deadline.isoformat()

raw_cards=[
('short-003-meta-01-three-valid-agent-submissions','Will at least 3 unique AI agents submit valid Round 003 forecasts before the deadline?','YES if at least 3 unique non-smoke agent_ids have accepted valid Round 003 forecast submissions before the deadline.','NO if fewer than 3 unique non-smoke agent_ids have accepted valid Round 003 forecast submissions before the deadline.','Measures whether the round attracted enough real agent participation to be useful.'),
('short-003-meta-02-one-external-agent-submission','Will at least 1 non-owner external AI agent submit a valid Round 003 forecast before the deadline?','YES if at least one accepted non-smoke Round 003 forecast is submitted by an agent not controlled by the site owner/operator before the deadline.','NO if no non-owner external AI agent submits an accepted non-smoke Round 003 forecast before the deadline.','Separates real third-party interest from owner-operated/demo-agent activity.'),
('short-003-meta-03-two-model-providers','Will Round 003 receive valid forecasts from at least 2 different model providers before the deadline?','YES if accepted non-smoke submissions include at least 2 distinct model/provider labels before the deadline.','NO if submissions come from fewer than 2 distinct model/provider labels before the deadline.','Tests whether the benchmark attracts more than one model family.'),
('short-003-meta-04-public-discussion','Will Round 003 receive at least 1 public external mention or discussion before the deadline?','YES if at least one public non-owner post, comment, article, issue, or social mention links to or clearly discusses Round 003 before the deadline.','NO if no public non-owner external mention/discussion is found before the deadline.','Measures whether the round creates visible outside attention.'),
('short-003-meta-05-clean-submission-flow','Will Round 003 finish the submission window with zero accepted-agent card-count or card-id mismatches?','YES if every accepted non-smoke Round 003 submission uses exactly the official candidate-approved card_ids and expected card count.','NO if at least one accepted non-smoke submission has a card-count mismatch, missing official card_id, or extra non-official card_id.','Tests whether the public instructions and cabinet flow are clear enough for agents to submit correctly.')
]

cards=[]
for i,(cid,title,yes,no,why) in enumerate(raw_cards,1):
    cards.append({
        'position':i,
        'track':'platform_meta',
        'card_id_suggestion':cid,
        'title':title,
        'source':'aitestarena_public_status',
        'source_url':'https://aitestarena.com/leaderboard/',
        'deadline_utc':deadline_iso,
        'yes_rule':yes,
        'no_rule':no,
        'public_verification':'Verify through the public Round 003 final status/leaderboard or settlement report.',
        'why_interesting':why,
        'quality_notes':['platform_meta card','smoke tests excluded','candidate pending owner/DeepSeek review']
    })

pack={
 'schema':'aitestarena.round_candidate_pack.v1',
 'audit_id':'candidate-pack-meta5-'+now.strftime('%Y%m%d-%H%M%S'),
 'status':'WARN',
 'summary':'Short candidate filled with 5 platform_meta cards because no quality external_market cards were available inside the 7-10 day horizon.',
 'generated_at':now.isoformat(),
 'round_candidate':{
   'round_id_suggestion':ROUND_ID,
   'round_title':TITLE,
   'status':'candidate_pending_review',
   'recommended_deadline_utc':deadline_iso,
   'cards_count':5,
   'mix':{'external_market':0,'platform_meta':5},
   'cards':cards
 },
 'quality_check':{
   'short_horizon_days':7,
   'no_machine_fragments':True,
   'tracks_clearly_labeled':True,
   'external_cards_found':0,
   'external_cards_note':'No quality human-readable external market cards found within the short horizon. Do not extend horizon just to force external cards.',
   'total_cards_target':5
 },
 'safe_to_promote_to_open':False,
 'requires_human_approval':True,
 'next_actions':['DeepSeek audits candidate_cards.json.','Owner approves/rejects or replaces one meta card with a manually found short external card.','Only after approval, promote to current/open.']
}

def esc(x): return str(x).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def render(pack):
    rows=''.join([f"<article class='card'><div><b>{c['position']}. {c['track']}</b></div><h2>{esc(c['title'])}</h2><p><b>Deadline:</b> {esc(c['deadline_utc'])}</p><p><b>YES:</b> {esc(c['yes_rule'])}</p><p><b>NO:</b> {esc(c['no_rule'])}</p><p>{esc(c['why_interesting'])}</p></article>" for c in cards])
    return "<!doctype html><meta charset='utf-8'><title>Round003 candidate</title><style>body{background:#050914;color:#eef4ff;font-family:Arial;line-height:1.55}main{max-width:1000px;margin:auto;padding:30px}.card{background:#0b1220;border:1px solid #20304a;border-radius:18px;padding:18px;margin:16px 0}</style><main><h1>Round003 candidate cards</h1><p>candidate_pending_review · 5 platform_meta · safe_to_promote_to_open=false</p>"+rows+"</main>"

for d in OUT_DIRS:
    d.mkdir(parents=True,exist_ok=True)
    (d/'candidate_cards.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (d/'candidate_cards.html').write_text(render(pack),encoding='utf-8')
print(json.dumps({'status':pack['status'],'cards_count':5,'mix':pack['round_candidate']['mix'],'candidate_json':[str(d/'candidate_cards.json') for d in OUT_DIRS]},ensure_ascii=False,indent=2))
