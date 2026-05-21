import os, json, time, importlib.util
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'generated-carports-2026-05-21-realism-b2-kie'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'
SRC = ROOT / 'scripts' / 'generate_mp_image_round_b2_realism_gemini.py'
spec = importlib.util.spec_from_file_location('gemini_b2', SRC)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SCENES = mod.SCENES
GLOBAL = mod.GLOBAL + "\n\nExtra rendering rule: use imperfect real construction photography, ordinary Austrian tradesmen, practical jobsite clutter, and physically boring-but-correct carpentry. Avoid polished CGI, showroom lighting, fantasy architecture, and stock-photo posing."

for env_path in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
API_KEY=os.environ.get('KIE_API_KEY')
CREATE='https://api.kie.ai/api/v1/jobs/createTask'
STATUS='https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}'
HEADERS={'Authorization': f'Bearer {API_KEY}', 'Content-Type':'application/json'} if API_KEY else {}
STATUS_HEADERS={'Authorization': f'Bearer {API_KEY}'} if API_KEY else {}
MODEL='nano-banana-2'

def save(m): MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')

def create_task(label,prompt):
    body={'model':MODEL,'input':{'prompt': GLOBAL+'\n\nScene: '+prompt, 'aspect_ratio':'16:9', 'resolution':'1K', 'output_format':'png'}}
    r=requests.post(CREATE, headers=HEADERS, json=body, timeout=120)
    try: data=r.json()
    except Exception: raise RuntimeError(f'non-json {r.status_code}: {r.text[:500]}')
    if data.get('code') != 200:
        raise RuntimeError(f'{label} submit failed: {data}')
    return data['data']['taskId'], body

def result_urls(sd):
    raw=sd.get('resultJson') or ''
    if not raw: return []
    try: parsed=json.loads(raw)
    except Exception: return []
    return parsed.get('resultUrls') or parsed.get('result_urls') or []

def contact_sheet(scenes):
    items=[]
    for label,info in scenes.items():
        f=info.get('file')
        if f and Path(f).exists(): items.append((label,Path(f)))
    if not items: return None
    W,H=360,270; cols=4; rows=(len(items)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W, rows*H+54),(232,226,215)); d=ImageDraw.Draw(sheet)
    d.text((16,18),f'M&P realism/workwear B2 KIE — {len(items)} images',fill=(20,20,20))
    for i,(label,path) in enumerate(items):
        im=Image.open(path).convert('RGB'); im.thumbnail((W,205))
        tile=Image.new('RGB',(W,H),'white'); tile.paste(im,((W-im.width)//2,8))
        td=ImageDraw.Draw(tile); td.rectangle([0,215,W,H],fill=(245,239,228)); td.text((8,224),label[:45],fill=(20,20,20))
        sheet.paste(tile,((i%cols)*W,54+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=90); return str(out)

def main():
    if not API_KEY: raise SystemExit('KIE_API_KEY missing')
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'model':MODEL,'state':'running','global_prompt':GLOBAL,'scenes':{}}
    if MANIFEST.exists():
        try: manifest=json.loads(MANIFEST.read_text()); manifest.setdefault('scenes',{})
        except Exception: pass
    for label,prompt in SCENES.items():
        info=manifest['scenes'].get(label,{})
        if info.get('task_id') or info.get('file'): continue
        try:
            tid,body=create_task(label,prompt)
            manifest['scenes'][label]={'state':'submitted','task_id':tid,'prompt':prompt,'request_body':body,'file_name':label+'.png'}
            print('submitted',label,tid,flush=True)
        except Exception as e:
            manifest['scenes'][label]={'state':'submit_failed','error':str(e),'prompt':prompt,'file_name':label+'.png'}
            print('submit_failed',label,str(e),flush=True)
        save(manifest); time.sleep(1.2)
    pending={l for l,i in manifest['scenes'].items() if i.get('task_id') and i.get('state') not in ('success','failed','error','cancelled') and not i.get('file')}
    for poll in range(180):
        if not pending: break
        time.sleep(10)
        for label in list(pending):
            info=manifest['scenes'][label]
            try:
                sr=requests.get(STATUS.format(task_id=info['task_id']),headers=STATUS_HEADERS,timeout=120)
                sd=sr.json().get('data',{})
                state=sd.get('state') or 'unknown'; info['state']=state; info['status_snapshot']={'failCode':sd.get('failCode'),'failMsg':sd.get('failMsg')}
                urls=result_urls(sd)
                if state=='success' and urls:
                    out=OUT/info['file_name']; img=requests.get(urls[0],timeout=180); img.raise_for_status(); out.write_bytes(img.content)
                    info.update({'result_url':urls[0],'file':str(out),'finished_at':datetime.now(timezone.utc).isoformat()}); pending.remove(label)
                    print('done',label,flush=True)
                elif state in ('failed','error','cancelled'):
                    info['finished_at']=datetime.now(timezone.utc).isoformat(); pending.remove(label); print('failed',label,info.get('status_snapshot'),flush=True)
            except Exception as e:
                info['last_poll_error']=str(e); print('poll_error',label,str(e),flush=True)
            save(manifest)
        done=sum(1 for i in manifest['scenes'].values() if i.get('file'))
        failed=sum(1 for i in manifest['scenes'].values() if i.get('state') in ('failed','error','cancelled','submit_failed'))
        print('poll',poll+1,'done',done,'failed',failed,'pending',len(pending),flush=True)
    manifest['contact_sheet']=contact_sheet(manifest['scenes']); manifest['finished_at']=datetime.now(timezone.utc).isoformat(); manifest['state']='finished' if not pending else 'timeout_polling'; manifest['pending']=sorted(pending)
    save(manifest); print('contact_sheet',manifest.get('contact_sheet'),flush=True); print('done',manifest['state'],flush=True)
if __name__=='__main__': main()
