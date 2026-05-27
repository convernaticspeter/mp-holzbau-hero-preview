import os, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau')
AVATAR_DIR = CUSTOMER / 'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20'
OUT = ROOT / 'assets' / 'mp-hero-canopy-logo-kie-2026-05-26'
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
CATBOX='https://catbox.moe/user/api.php'
HEADERS={'Authorization':f'Bearer {API_KEY}','Content-Type':'application/json'} if API_KEY else {}
STATUS_HEADERS={'Authorization':f'Bearer {API_KEY}'} if API_KEY else {}
UPLOAD_HEADERS={'Authorization':f'Bearer {API_KEY}'} if API_KEY else {}
MODEL='nano-banana-2'

REFS = [
    ROOT/'assets/mp-hero-happy-finished-oak-2026-05-26-gemini/selected_happy_finished_oak_hero.webp',
    ROOT/'assets/mp-hero-happy-finished-oak-2026-05-26-gemini/04_happy_peter_team_carport_reveal.webp',
    ROOT/'assets/peter-preissinger-portrait.webp',
    ROOT/'assets/mp-workwear-corrections-2026-05-26-kie/01_peter_red_hoodie_plan_carport.webp',
    AVATAR_DIR/'Michael.png',
    AVATAR_DIR/'Markus.png',
    AVATAR_DIR/'Gerhard.png',
    AVATAR_DIR/'Tobias.png',
    ROOT/'assets/logo-white.png',
]

GLOBAL = """
Create a corrected premium photorealistic 16:9 hero image for the M&P Holzbau landing page.

Use the supplied existing hero/team images as composition inspiration only: keep the improved close-together happy group feeling, not random scattered people. Use the supplied Peter and M&P avatar references as identity/workwear anchors. Use the supplied WHITE M&P logo image as the logo reference for clothing: the small chest logo must be clean, white, simple, and plausible. Do not invent messy pseudo text or random symbols.

Main correction from previous version:
- The roof/canopy from the carport to the house entrance MUST be clearly visible and architecturally believable.
- Show a continuous covered path from the large oak carport roof toward the front door / entrance canopy.
- It should read immediately: people can walk dry from the carport to the house entrance.
- Do not hide this connection behind people or crop it away.

People:
- Peter Preissinger is the main older Austrian Zimmermeister: short gray hair, gray stubble beard, calm proud happy expression.
- 2 to 3 team members stand close beside/behind him as a coherent happy group, shoulder-to-shoulder or naturally clustered, like a finished-project handover/team-pride photo.
- Burgundy/dark red M&P hoodies or work jackets, dark work trousers, subtle clean white M&P chest logo from the logo reference.
- No random generic workers, no scattered awkward lineup, no one floating alone.

Carport/location:
- Very special wide oak timber carport, massive visible oak beams and posts, wide enough for two cars plus two motorcycles, but completely empty.
- Hard negative: no cars, no motorcycles, no bicycles, no vans, no vehicles, no license plates anywhere.
- No Blechwinkel, no sheet-metal angle brackets, no shiny metal connector hero detail. Use oak joinery, Nuten/Auflager, timber-to-timber support logic.
- Medium-sized detached Austrian family house, about 200 sqm, early 2000s Vienna Basin / Wiener Becken feel: plaster facade, realistic suburban house, not Alpine chalet, not luxury villa.
- Well-designed front garden with shrubs/grasses/stone path and clean driveway.

Hero layout:
- True horizontal 16:9, warm daylight, premium but believable documentary photo.
- Keep calm darker/less busy space on the left for headline text overlay.
- Put Peter/team mostly center-right/right third, but do not block the visible canopy route to the entrance.
- No watermark, no readable text except subtle clean M&P chest logo.
""".strip()

SCENES = {
    '01_close_group_canopy_clearly_visible': 'Close happy Peter-and-team group on the right third. The carport roof continues behind them as a clear covered walkway all the way toward the visible front door on the left/middle background.',
    '02_handover_group_front_garden_canopy': 'Finished-project handover feeling: Peter and team stand close together near the front garden path, with the oak carport and a continuous entrance canopy clearly visible behind them.',
    '03_more_house_context_clear_covered_path': 'A slightly wider house-context hero: the early-2000s house facade, front door, garden path, and continuous roof/canopy from carport to entrance are unmistakable; Peter and team remain close together on the right.',
    '04_oak_carport_depth_team_not_blocking': 'Emphasize the large empty oak carport depth and the covered walkway to entrance. Peter and team form one compact proud group to the side, not blocking the architecture.'
}

def upload(path: Path) -> str:
    mime='image/png' if path.suffix.lower()=='.png' else 'image/webp' if path.suffix.lower()=='.webp' else 'image/jpeg'
    # Prefer Catbox URLs for KIE image_input because the KIE upload endpoint sometimes hangs on this network.
    with path.open('rb') as fh:
        r=requests.post(CATBOX,data={'reqtype':'fileupload'},files={'fileToUpload':(path.name,fh,mime)},timeout=90)
    if r.ok and r.text.strip().startswith('https://'):
        return r.text.strip()
    # Fallback to KIE's own upload endpoint.
    with path.open('rb') as fh:
        r=requests.post(UPLOAD,headers=UPLOAD_HEADERS,data={'uploadPath':'images'},files={'file':(path.name,fh,mime)},timeout=60)
    r.raise_for_status(); data=r.json()
    if not data.get('success'):
        raise RuntimeError(f'upload failed {path}: {data}; catbox={r.text[:200]}')
    return data['data']['downloadUrl']

def slug(s): return re.sub(r'[^a-z0-9_\-]+','-',s.lower()).strip('-')
def save(m): MANIFEST.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')

def submit(label,prompt,image_input):
    body={'model':MODEL,'input':{'prompt':GLOBAL+'\n\nVariant: '+prompt,'image_input':image_input,'aspect_ratio':'16:9','resolution':'2K','output_format':'png'}}
    r=requests.post(CREATE,headers=HEADERS,json=body,timeout=180)
    try: data=r.json()
    except Exception: raise RuntimeError(f'non-json {r.status_code}: {r.text[:500]}')
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
    W,H=520,340; cols=2; rows=(len(items)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W,rows*H+60),(232,226,215)); d=ImageDraw.Draw(sheet)
    d.text((16,22),f'M&P Hero KIE correction: canopy + clean white logo — {len(items)} variants',fill=(20,20,20))
    for i,(label,path) in enumerate(items):
        im=Image.open(path).convert('RGB'); im.thumbnail((W,270))
        tile=Image.new('RGB',(W,H),'white'); tile.paste(im,((W-im.width)//2,8))
        td=ImageDraw.Draw(tile); td.rectangle([0,280,W,H],fill=(245,239,228)); td.text((10,292),label[:60],fill=(20,20,20))
        sheet.paste(tile,((i%cols)*W,60+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=92); return str(out)

def main():
    if not API_KEY: raise SystemExit('KIE_API_KEY missing')
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'batch':'mp-hero-canopy-logo-kie-2026-05-26','model':MODEL,'state':'init','output_dir':str(OUT),'refs':[str(p) for p in REFS],'global_prompt':GLOBAL,'scenes':{}}
    if MANIFEST.exists():
        try: manifest=json.loads(MANIFEST.read_text()); manifest.setdefault('scenes',{})
        except Exception: pass
    if not manifest.get('ref_urls'):
        urls=[]
        for p in REFS:
            if not p.exists(): raise FileNotFoundError(str(p))
            urls.append(upload(p)); print('uploaded',p.name,flush=True); time.sleep(.4)
        manifest['ref_urls']=urls; save(manifest)
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
        save(manifest); time.sleep(1.2)
    pending={l for l,i in manifest['scenes'].items() if i.get('task_id') and not i.get('file') and i.get('state') not in ('success','failed','fail','error','cancelled')}
    for poll in range(160):
        if not pending: break
        time.sleep(10)
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
                    Image.open(png).convert('RGB').save(webp,quality=90,method=6)
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
