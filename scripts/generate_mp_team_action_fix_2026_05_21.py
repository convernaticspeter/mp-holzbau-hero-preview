import os, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau')
OUT = ROOT / 'assets' / 'mp-team-action-fix-2026-05-21-kie'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'

for env_path in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k,v=line.split('=',1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY=os.environ.get('KIE_API_KEY')
CREATE='https://api.kie.ai/api/v1/jobs/createTask'
STATUS='https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}'
UPLOAD='https://kieai.redpandaai.co/api/file-stream-upload'
HEADERS={'Authorization':f'Bearer {API_KEY}','Content-Type':'application/json'} if API_KEY else {}
STATUS_HEADERS={'Authorization':f'Bearer {API_KEY}'} if API_KEY else {}
UPLOAD_HEADERS={'Authorization':f'Bearer {API_KEY}'} if API_KEY else {}

REFS = [
    CUSTOMER/'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20/Michael.png',
    CUSTOMER/'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20/Markus.png',
    CUSTOMER/'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20/Gerhard.png',
    CUSTOMER/'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20/Tobias.png',
    CUSTOMER/'assets/logo/logo.png',
]

GLOBAL = """
Photorealistic documentary images for M&P Holzbau, an Austrian Zimmermeisterbetrieb. Use the supplied worker/team references as identity and workwear anchors: red/burgundy work hoodies or work jackets, dark work trousers, small white M&P logo on the left chest only. Looks like real Austrian carpenters, not stock photo, not CGI.
CRITICAL ACTION LOGIC: show only real, useful carpentry or carport installation work. No fake working poses. No nonsensical tapping, pointing, or pretending. No fake metal angle/Winkel hero shot. No random bracket fantasy. No terrace/deck construction. No patio. No pergola. No impossible post bases or leaning beams. Tools must match the visible task exactly. Horizontal 16:9, natural lens, landing-page usable, no readable text, no watermark, no third-party brands.
""".strip()

SCENES = {
    '01_team_montage_balken_einheben': """
Two M&P carpenters at a nearly finished timber carport on an Austrian driveway, performing a believable montage task: carefully positioning and aligning a solid timber beam/rafter under the carport roof line. One worker supports/guides the beam, the second checks alignment with a spirit level or holds it in place. Timber posts, roof underside, paved driveway and house facade visible. The action must read as real installation work, not posing. No metal Winkel/bracket close-up as the subject.
""".strip(),
    '02_werkstatt_kappsaege_holz_zuschnitt': """
One M&P carpenter in a real timber workshop using a professional chop saw / Kappsäge to cut a carport timber beam to length. The timber beam is clamped or properly supported on a workbench/saw station, hands safely placed, saw action physically plausible, wood dust and offcuts subtle. This is a useful workshop preparation task for a carport. No fake pose, no random handheld drill, no metal angle/Winkel, no terrace boards.
""".strip(),
    '03_team_vor_ort_zollstock_anzeichnen': """
Two M&P carpenters on a carport construction site doing a believable on-site handcraft task: one marks a timber post/beam with a pencil while the other holds a folding rule/Zollstock and checks the measurement. A real timber carport structure, vertical posts, rafters and paved driveway are visible. They are focused on the timber, not smiling at camera. No fake bracket work, no drilling into a meaningless Winkel, no terrace deck.
""".strip(),
}

def upload(path: Path) -> str:
    mime = 'image/png' if path.suffix.lower()=='.png' else 'image/webp' if path.suffix.lower()=='.webp' else 'image/jpeg'
    with path.open('rb') as fh:
        r=requests.post(UPLOAD,headers=UPLOAD_HEADERS,data={'uploadPath':'images'},files={'file':(path.name,fh,mime)},timeout=180)
    r.raise_for_status(); data=r.json()
    if not data.get('success'):
        raise RuntimeError(f'upload failed {path}: {data}')
    return data['data']['downloadUrl']

def slug(s): return re.sub(r'[^a-z0-9_\-]+','-',s.lower()).strip('-')
def save(m): MANIFEST.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')

def submit(label,prompt,image_input):
    body={'model':'nano-banana-2','input':{'prompt':GLOBAL+'\n\nScene: '+prompt,'image_input':image_input,'aspect_ratio':'16:9','resolution':'2K','output_format':'png'}}
    r=requests.post(CREATE,headers=HEADERS,json=body,timeout=180); r.raise_for_status(); data=r.json()
    if data.get('code')!=200:
        raise RuntimeError(f'{label} submit failed: {data}')
    return data['data']['taskId'], body

def urls_from(sd):
    raw=sd.get('resultJson') or ''
    if not raw: return []
    try: parsed=json.loads(raw)
    except Exception: return []
    return parsed.get('resultUrls') or parsed.get('result_urls') or []

def make_contact(scenes):
    items=[]
    for label,info in scenes.items():
        f=info.get('file')
        if f and Path(f).exists(): items.append((label,Path(f)))
    if not items: return None
    W,H=430,300
    tiles=[]
    for label,path in items:
        im=Image.open(path).convert('RGB'); im.thumbnail((W,235))
        tile=Image.new('RGB',(W,H),(255,255,255)); tile.paste(im,((W-im.width)//2,8))
        d=ImageDraw.Draw(tile); d.rectangle([0,242,W,H],fill=(245,239,228)); d.text((10,252),label[:55],fill=(20,20,20))
        tiles.append(tile)
    cols=3; rows=(len(tiles)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W,rows*H+58),(232,226,215)); d=ImageDraw.Draw(sheet)
    d.text((16,20),'M&P team/action fix: real tasks, no fake Winkel',fill=(20,20,20))
    for i,t in enumerate(tiles): sheet.paste(t,((i%cols)*W,58+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=92); return str(out)

def main():
    if not API_KEY: raise SystemExit('KIE_API_KEY missing')
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'batch':'mp-team-action-fix-2026-05-21','model':'nano-banana-2','state':'init','output_dir':str(OUT),'refs':[str(p) for p in REFS],'scenes':{}}
    if MANIFEST.exists():
        try: manifest=json.loads(MANIFEST.read_text()); manifest.setdefault('scenes',{})
        except Exception: pass
    if not manifest.get('ref_urls'):
        manifest['ref_urls']=[upload(p) for p in REFS if p.exists()]
        save(manifest)
    for label,prompt in SCENES.items():
        info=manifest['scenes'].get(label,{})
        if info.get('task_id') or info.get('file'): continue
        try:
            task_id,body=submit(label,prompt,manifest['ref_urls'])
            manifest['scenes'][label]={'state':'submitted','task_id':task_id,'prompt':prompt,'request_body':body,'file_name':slug(label)+'.png'}
            print('submitted',label,task_id,flush=True)
        except Exception as e:
            manifest['scenes'][label]={'state':'submit_failed','prompt':prompt,'error':str(e),'file_name':slug(label)+'.png'}
            print('submit_failed',label,e,flush=True)
        save(manifest); time.sleep(1)
    pending={l for l,i in manifest['scenes'].items() if i.get('task_id') and not i.get('file') and i.get('state') not in ('success','failed','fail','error','cancelled')}
    for poll in range(90):
        if not pending: break
        time.sleep(12)
        for label in list(pending):
            info=manifest['scenes'][label]
            try:
                data=requests.get(STATUS.format(task_id=info['task_id']),headers=STATUS_HEADERS,timeout=180).json()
                sd=data.get('data',{}); state=sd.get('state') or 'unknown'; info['state']=state
                info['status_snapshot']={'failCode':sd.get('failCode'),'failMsg':sd.get('failMsg')}
                urls=urls_from(sd)
                if state=='success' and urls:
                    raw=requests.get(urls[0],timeout=240); raw.raise_for_status()
                    png=OUT/info['file_name']; png.write_bytes(raw.content)
                    webp=png.with_suffix('.webp')
                    Image.open(png).convert('RGB').save(webp,quality=88,method=6)
                    info.update({'result_url':urls[0],'file':str(webp),'source_png':str(png),'finished_at':datetime.now(timezone.utc).isoformat()})
                    pending.remove(label); print('done',label,webp.name,flush=True)
                elif state in ('failed','fail','error','cancelled'):
                    info['finished_at']=datetime.now(timezone.utc).isoformat(); pending.remove(label); print('failed',label,info.get('status_snapshot'),flush=True)
            except Exception as e:
                info['last_poll_error']=str(e); print('poll_error',label,e,flush=True)
            save(manifest)
        print('poll',poll+1,'done',sum(1 for i in manifest['scenes'].values() if i.get('file')),'pending',len(pending),flush=True)
    manifest['contact_sheet']=make_contact(manifest['scenes']); manifest['finished_at']=datetime.now(timezone.utc).isoformat(); manifest['state']='finished' if not pending else 'timeout_polling'; manifest['pending']=sorted(pending)
    save(manifest)
    print('contact_sheet',manifest.get('contact_sheet'),flush=True); print('done',manifest['state'],flush=True)

if __name__=='__main__': main()
