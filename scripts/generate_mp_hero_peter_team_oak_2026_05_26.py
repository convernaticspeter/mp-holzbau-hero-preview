import os, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau')
AVATAR_DIR = CUSTOMER / 'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20'
LOGO = CUSTOMER / 'assets/logo/logo.png'
OUT = ROOT / 'assets' / 'mp-hero-peter-team-oak-2026-05-26-kie'
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
MODEL='nano-banana-2'

REFS = [
    ROOT/'assets/peter-preissinger-portrait.webp',
    ROOT/'assets/mp-workwear-corrections-2026-05-26-kie/01_peter_red_hoodie_plan_carport.webp',
    ROOT/'assets/mp-avatar-scenes-2026-05-26-kie/10_montage_abschlusskontrolle_team.webp',
    AVATAR_DIR/'Michael.png',
    AVATAR_DIR/'Markus.png',
    AVATAR_DIR/'Gerhard.png',
    AVATAR_DIR/'Tobias.png',
    LOGO,
]

GLOBAL = """
Create a premium photorealistic hero image for the M&P Holzbau landing page.

Identity and people:
- Use the supplied Peter Preissinger reference as the main person: older Austrian carpenter / master builder, short gray hair, gray stubble beard, calm proud expression.
- Use the supplied M&P worker/avatar references for the team. Do not invent random workers. Keep faces and age range close to the references.
- Peter and 2 to 3 team members wear original-looking M&P work clothing: burgundy/dark red hoodie or work jacket, dark work trousers, subtle small white M&P logo on left chest only.
- Proud but natural team pose: confident, friendly, real craftspeople, not stock-photo models, not exaggerated smiling.

Carport and location:
- A very special wide oak timber carport made from visible massive oak beams and posts.
- Wide enough for two cars and two motorcycles underneath, but the carport is completely empty.
- NO cars, NO motorcycles, NO bicycles, NO vehicles, NO license plates visible anywhere.
- No Blechwinkel, no metal angle brackets, no shiny steel connector hero details. Use beautiful carpentry logic: oak joinery, clean supports, Nuten/Auflager, timber-to-timber connections, solid roof edge.
- In front of a medium-sized detached Austrian family house, about 200 sqm, built in the early 2000s, Vienna Basin / Wiener Becken character: plaster facade, simple gabled/hipped roof, not alpine chalet, not luxury villa.
- Well-designed front garden with low planting, gravel/stone path, shrubs, clean driveway.
- A roof/canopy connection continues from the carport toward the house entrance, so the covered way to the entrance is visually clear.

Hero composition:
- True horizontal 16:9 landing-page hero, natural wide-angle documentary photo.
- Leave some clean darker/less busy space on the left side for overlaid headline text; put Peter and the team mostly in the center-right or right third.
- Warm daylight, premium but believable, real Austrian residential setting, not CGI, not showroom, not fantasy architecture.
- No readable text except a subtle M&P chest logo; no watermark; no fake signs.
""".strip()

SCENES = {
    '01_hero_peter_team_right_wide_oak': 'Peter stands proud in the right third with two team members slightly behind him, all in burgundy M&P workwear, in front of a very wide empty oak carport. The left side shows clean oak structure and shaded driveway for text overlay. The early-2000s Austrian house and covered walkway to entrance are visible behind.',
    '02_hero_team_under_roof_empty_bay': 'Peter and three team members stand just outside the open empty bay of the oversized oak carport. The roof span clearly suggests space for two cars plus two motorcycles, but absolutely no vehicles are present. Beautiful oak beams, no metal brackets, front garden and entrance canopy visible.',
    '03_hero_low_angle_oak_craft': 'A slightly lower camera angle emphasizing massive oak posts, Nuten and timber supports, with Peter foreground right and the M&P team casually grouped behind. Medium Vienna Basin family house from early 2000s in background, landscaped garden, covered path to entrance.',
    '04_hero_house_front_canopy_clear': 'A broader residential view: the special empty oak double carport connects visually to a canopy leading to the house entrance. Peter and team are proud but natural on the right, carport and front garden dominate the frame, no cars or motorcycles anywhere.'
}

def upload(path: Path) -> str:
    mime='image/png' if path.suffix.lower()=='.png' else 'image/webp' if path.suffix.lower()=='.webp' else 'image/jpeg'
    with path.open('rb') as fh:
        r=requests.post(UPLOAD,headers=UPLOAD_HEADERS,data={'uploadPath':'images'},files={'file':(path.name,fh,mime)},timeout=180)
    r.raise_for_status(); data=r.json()
    if not data.get('success'):
        raise RuntimeError(f'upload failed {path}: {data}')
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
    d.text((16,22),f'M&P hero Peter + team oak carport — {len(items)} variants',fill=(20,20,20))
    for i,(label,path) in enumerate(items):
        im=Image.open(path).convert('RGB'); im.thumbnail((W,270))
        tile=Image.new('RGB',(W,H),'white'); tile.paste(im,((W-im.width)//2,8))
        td=ImageDraw.Draw(tile); td.rectangle([0,280,W,H],fill=(245,239,228)); td.text((10,292),label[:60],fill=(20,20,20))
        sheet.paste(tile,((i%cols)*W,60+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=92); return str(out)

def main():
    if not API_KEY: raise SystemExit('KIE_API_KEY missing')
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'batch':'mp-hero-peter-team-oak-2026-05-26','model':MODEL,'state':'init','output_dir':str(OUT),'refs':[str(p) for p in REFS],'global_prompt':GLOBAL,'scenes':{}}
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
    for poll in range(120):
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
