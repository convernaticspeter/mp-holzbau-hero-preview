import os, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'mp-carport-corrections-2026-05-21-kie'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'

for env_path in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY = os.environ.get('KIE_API_KEY')
CREATE = 'https://api.kie.ai/api/v1/jobs/createTask'
STATUS = 'https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}'
HEADERS = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'} if API_KEY else {}
STATUS_HEADERS = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else {}
MODEL = 'gpt-image-2-text-to-image'

GLOBAL = """
Photorealistic documentary architectural images for M&P Holzbau, an Austrian Zimmermeisterbetrieb building custom timber carports in Vienna, Lower Austria and Burgenland.
CRITICAL: every image must clearly be about a timber CARPORT or carport construction, never a terrace, patio deck, pergola, balcony, terrace substructure or generic timber platform.
Use realistic Austrian / DACH detached houses, paved driveways, gutters, downpipes, straight timber posts and beams, plausible roof loads and connections. Craft-quality, practical, believable local trade photography, not CGI, not luxury-render fantasy.
No readable text, no logos, no watermarks, no license plates. Workers may wear dark navy/charcoal/burgundy workwear without readable logos. Natural lens and light. Horizontal 16:9, website usable, no awkward crops.
""".strip()

SCENES = {
    '01_verbindungen_statt_kosmetik_carport_detail': 'Close documentary detail at a finished timber carport: a solid timber beam meeting a vertical post under the carport roof, visible metal bracket/bolt connection and roof underside, paved driveway below, part of the house in the background. Absolutely no terrace deck or patio floor construction.',
    '02_material_wunsch_carport_holz_detail': 'Close-medium photo of different timber finish samples and roof color samples held beside an actual timber carport post on a paved driveway, with the carport roof and house entrance softly visible behind. Shows custom material choice for the desired carport, not Siberian larch specifically.',
    '03_team_planung_am_carport': 'Documentary scene: two M&P-style carpenters in burgundy/dark workwear standing at an actual timber carport on an Austrian driveway, looking at plans and pointing toward roof line and post positions. They are not posing. The image must clearly show the carport structure, not a terrace.',
    '04_montage_stuetzenpunkt_carport': 'Construction detail: worker kneeling at the post base of a timber carport, fastening a metal bracket into concrete/paving at the driveway, vertical carport post and roof beams visible above. No terrace boards, no deck, no pergola.',
    '05_referenz_carport_hausanschluss_eingang': 'Finished custom timber carport with a covered roof extension from the parking bay toward the front door, showing a dry protected path to the house entrance. Austrian family house, paved driveway, no text, believable gutter and downpipe.',
    '06_referenz_carport_wasserfuehrung': 'Finished timber carport after rain: wet uncovered driveway outside, dry sheltered paving under roof, visible gutter and downpipe leading water away from house facade. No terrace, no generic patio.',
    '07_referenz_carport_wunschcarport': 'Modern custom timber carport built exactly to fit a normal Austrian house and driveway, practical proportions, clear opening space, optional side storage/weather wall, calm daylight. It should look like a real desired carport, not a catalogue model.',
    '08_standort_check_punkte_basisbild': 'Wide clean photo of timber carport attached beside an Austrian house, with roof continuing toward front door entrance. Clear visible elements for future labels: roof gutter/downpipe on one side, house connection line, walking space to entrance, post base/foundation area, closed weather side. No labels or text in the image.'
}

def slug(name: str) -> str:
    return re.sub(r'[^a-z0-9_\-]+', '-', name.lower()).strip('-')

def save(m):
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')

def create_task(label, prompt):
    body = {'model': MODEL, 'input': {'prompt': GLOBAL + '\n\nScene: ' + prompt, 'aspect_ratio': '16:9', 'resolution': '1K', 'output_format': 'png'}}
    r = requests.post(CREATE, headers=HEADERS, json=body, timeout=120)
    data = r.json()
    if data.get('code') != 200:
        raise RuntimeError(f'{label} submit failed: {data}')
    return data['data']['taskId'], body

def result_urls(sd):
    raw = sd.get('resultJson') or ''
    if not raw: return []
    try: parsed = json.loads(raw)
    except Exception: return []
    return parsed.get('resultUrls') or parsed.get('result_urls') or []

def contact_sheet(scenes):
    items=[]
    for label, info in scenes.items():
        f=info.get('file')
        if f and Path(f).exists(): items.append((label, Path(f)))
    if not items: return None
    W,H=360,275
    thumbs=[]
    for label,path in items:
        im=Image.open(path).convert('RGB'); im.thumbnail((W,210))
        tile=Image.new('RGB',(W,H),'white'); tile.paste(im,((W-im.width)//2,8))
        d=ImageDraw.Draw(tile); d.rectangle([0,218,W,H], fill=(245,239,228)); d.text((8,226),label[:46],fill=(20,20,20))
        thumbs.append(tile)
    cols=4; rows=(len(thumbs)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W,rows*H+54),(232,226,215)); d=ImageDraw.Draw(sheet)
    d.text((16,18),f'M&P carport correction KIE — {len(items)} / {len(SCENES)} images',fill=(20,20,20))
    for i,t in enumerate(thumbs): sheet.paste(t,((i%cols)*W,54+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=90); return str(out)

def main():
    if not API_KEY: raise SystemExit('KIE_API_KEY missing')
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'batch':'mp-carport-corrections-2026-05-21','model':MODEL,'state':'init','output_dir':str(OUT),'global_prompt':GLOBAL,'scenes':{}}
    if MANIFEST.exists():
        try: manifest=json.loads(MANIFEST.read_text()); manifest.setdefault('scenes',{})
        except Exception: pass
    for label,prompt in SCENES.items():
        info=manifest['scenes'].get(label,{})
        if info.get('task_id') or info.get('file'): continue
        try:
            task_id,body=create_task(label,prompt)
            manifest['scenes'][label]={'state':'submitted','task_id':task_id,'prompt':prompt,'request_body':body,'file_name':slug(label)+'.png'}
            print('submitted',label,task_id,flush=True)
        except Exception as e:
            manifest['scenes'][label]={'state':'submit_failed','prompt':prompt,'error':str(e),'file_name':slug(label)+'.png'}
            print('submit_failed',label,e,flush=True)
        save(manifest); time.sleep(1.2)
    pending={l for l,i in manifest['scenes'].items() if i.get('task_id') and i.get('state') not in ('success','failed','error','cancelled') and not i.get('file')}
    for poll in range(90):
        if not pending: break
        time.sleep(10)
        for label in list(pending):
            info=manifest['scenes'][label]
            try:
                data=requests.get(STATUS.format(task_id=info['task_id']),headers=STATUS_HEADERS,timeout=120).json()
                sd=data.get('data',{}); state=sd.get('state') or 'unknown'; info['state']=state
                info['status_snapshot']={'failCode':sd.get('failCode'),'failMsg':sd.get('failMsg')}
                urls=result_urls(sd)
                if state=='success' and urls:
                    raw=requests.get(urls[0],timeout=180); raw.raise_for_status()
                    png=OUT/info['file_name']; png.write_bytes(raw.content)
                    webp=png.with_suffix('.webp')
                    Image.open(png).convert('RGB').save(webp,quality=88,method=6)
                    info.update({'result_url':urls[0],'file':str(webp),'source_png':str(png),'finished_at':datetime.now(timezone.utc).isoformat()})
                    pending.remove(label); print('done',label,webp.name,flush=True)
                elif state in ('failed','error','cancelled'):
                    info['finished_at']=datetime.now(timezone.utc).isoformat(); pending.remove(label); print('failed',label,info.get('status_snapshot'),flush=True)
            except Exception as e:
                info['last_poll_error']=str(e); print('poll_error',label,e,flush=True)
            save(manifest)
        print('poll',poll+1,'done',sum(1 for i in manifest['scenes'].values() if i.get('file')),'pending',len(pending),flush=True)
    manifest['contact_sheet']=contact_sheet(manifest['scenes']); manifest['finished_at']=datetime.now(timezone.utc).isoformat(); manifest['state']='finished' if not pending else 'timeout_polling'; manifest['pending']=sorted(pending)
    save(manifest)
    print('contact_sheet',manifest.get('contact_sheet'),flush=True); print('done',manifest['state'],flush=True)

if __name__ == '__main__': main()
