#!/usr/bin/env python3
import os, json, time, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

API_KEY=os.environ.get('KIE_API_KEY')
if not API_KEY: raise SystemExit('KIE_API_KEY missing')
BASE='https://api.kie.ai/api/v1'
CREATE=f'{BASE}/jobs/createTask'
STATUS=f'{BASE}/jobs/recordInfo?taskId={{task_id}}'
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/mp-team-scenes-avatar-replacement-2026-05-27-kie'
IMG=OUT/'images'
manifest=json.loads((OUT/'manifest.json').read_text())
headers={'Authorization':f'Bearer {API_KEY}','Content-Type':'application/json','Accept':'application/json','User-Agent':'Mozilla/5.0'}

def req(method,url,payload=None,timeout=90):
    data=json.dumps(payload).encode() if payload is not None else None
    r=urllib.request.Request(url,data=data,headers=headers,method=method)
    with urllib.request.urlopen(r,timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def download(url,path):
    r=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(r,timeout=240) as resp:
        path.write_bytes(resp.read())

sid='20_team_detail_connection'
base=manifest['base_scene_urls'][sid]
avatar=manifest['avatar_urls']['Lukas']
prompt='''Use the first supplied image as the exact base scene/composition reference. Minimal correction/replacement pass only.
Replace the visible worker with the supplied Lukas avatar reference. Keep the avatar face, age impression, burgundy red M&P hoodie/workwear, and the small white M&P textile chest mark as in the avatar reference.
Do not invent or redraw a prominent logo. If the logo is small, folded, partially hidden, or only a subtle white mark, that is correct. No colored logo patch, no fake letters, no badges, no extra branding.
Keep the base image scene: close timber joint/detail work, realistic carpentry hands and tools, same camera angle and timber structure. No redesign. No Blechwinkel hero detail. True horizontal 16:9 realistic Austrian timber-construction documentary photo.'''
payload={'model':'nano-banana-2','input':{'prompt':prompt,'image_input':[base,avatar],'aspect_ratio':'16:9','resolution':'2K','output_format':'png'}}
res=req('POST',CREATE,payload,90)
tid=(res.get('data') or {}).get('taskId')
print('SUBMITTED',tid,flush=True)
item=None
for it in manifest['items']:
    if it.get('id')==sid:
        item=it; break
if item is None:
    item={'id':sid}; manifest['items'].append(item)
item.update({'id':sid,'avatars':['Lukas'],'task_id':tid,'state':'submitted_retry','prompt':prompt,'image_input':[base,avatar],'submit_response_retry':res})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
start=time.time()
while time.time()-start<1200:
    st=req('GET',STATUS.format(task_id=tid),None,45)
    data=st.get('data') or {}; state=(data.get('state') or '').lower()
    print('STATUS',state,flush=True)
    item['last_status']=st; item['state']=state
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    if state in {'success','failed','fail','error','cancelled','canceled'}:
        if state=='success':
            rj=data.get('resultJson')
            if isinstance(rj,str): rj=json.loads(rj)
            urls=(rj or {}).get('resultUrls') or []
            item['result_urls']=urls
            if urls:
                png=IMG/f'{sid}.png'; download(urls[0],png); item['file']=str(png)
                im=Image.open(png).convert('RGB')
                webp=IMG/f'{sid}.webp'; im.save(webp,'WEBP',quality=88,method=6); item['webp']=str(webp)
                print('DOWNLOADED',png,flush=True)
        break
    time.sleep(20)
# rebuild contact sheet from manifest items with files
files=[Path(i.get('webp') or i.get('file')) for i in manifest['items'] if i.get('webp') or i.get('file')]
files=[f for f in files if f.exists()]
thumbs=[]
for f in sorted(files, key=lambda p:p.name):
    im=Image.open(f).convert('RGB'); im.thumbnail((360,202))
    tile=Image.new('RGB',(390,248),(246,239,228))
    tile.paste(im,((390-im.width)//2,10))
    ImageDraw.Draw(tile).text((12,218),f.stem,fill=(24,24,24))
    thumbs.append(tile)
cols=5; rows=(len(thumbs)+cols-1)//cols
sheet=Image.new('RGB',(cols*390,rows*248),(32,38,30))
for idx,t in enumerate(thumbs): sheet.paste(t,((idx%cols)*390,(idx//cols)*248))
sheet_path=OUT/'_contact_sheet.jpg'; sheet.save(sheet_path,quality=92)
manifest['contact_sheet']=str(sheet_path)
manifest['retry_20_finished_at']=time.time()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print('CONTACT_SHEET',sheet_path)
