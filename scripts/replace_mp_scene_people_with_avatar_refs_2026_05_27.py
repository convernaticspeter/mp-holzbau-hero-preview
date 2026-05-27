#!/usr/bin/env python3
import os, json, time, urllib.request, mimetypes
from pathlib import Path
from datetime import datetime, timezone

BASE='https://api.kie.ai/api/v1'
CREATE=f'{BASE}/jobs/createTask'
STATUS=f'{BASE}/jobs/recordInfo?taskId={{task_id}}'
UPLOAD='https://kieai.redpandaai.co/api/file-stream-upload'
API_KEY=os.environ.get('KIE_API_KEY')
if not API_KEY:
    raise SystemExit('KIE_API_KEY missing')

ROOT=Path(__file__).resolve().parents[1]
BASE_SCENES=ROOT/'assets/mp-peter-team-scenes-2026-05-27-kie-white-logo-v2/images'
OUT=ROOT/'assets/mp-team-scenes-avatar-replacement-2026-05-27-kie'
IMG=OUT/'images'
IMG.mkdir(parents=True, exist_ok=True)

AVATAR_DIR=Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau/assets/generated-images/mp-holzbau-portraits-5-unique-v2')
AVATARS={
    'Lena': AVATAR_DIR/'01_lena_office_plans_turn.png',
    'Tobias': AVATAR_DIR/'02_tobias_apprentice_tool_belt.png',
    'Harald': AVATAR_DIR/'03_harald_master_crossed_arms.png',
    'Lukas': AVATAR_DIR/'04_lukas_measure_tape_side.png',
    'Daniel': AVATAR_DIR/'05_daniel_tablet_consulting.png',
}

headers_json={'Authorization':f'Bearer {API_KEY}','Content-Type':'application/json','Accept':'application/json','User-Agent':'Mozilla/5.0'}

def req(method,url,payload=None,timeout=90):
    data=json.dumps(payload).encode() if payload is not None else None
    r=urllib.request.Request(url,data=data,headers=headers_json,method=method)
    with urllib.request.urlopen(r,timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def upload_file(path: Path):
    boundary='----HermesBoundary' + str(int(time.time()*1000))
    parts=[]
    def field(name,value):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    def filepart(name,path):
        ctype=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{path.name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode())
        parts.append(path.read_bytes()); parts.append(b'\r\n')
    field('uploadPath','images')
    filepart('file',path)
    parts.append(f'--{boundary}--\r\n'.encode())
    body=b''.join(parts)
    r=urllib.request.Request(UPLOAD,data=body,method='POST',headers={'Authorization':f'Bearer {API_KEY}','Content-Type':f'multipart/form-data; boundary={boundary}','User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(r,timeout=180) as resp:
        res=json.loads(resp.read().decode())
    url=((res.get('data') or {}).get('downloadUrl') or (res.get('data') or {}).get('url') or '')
    if not url:
        raise RuntimeError(f'upload failed: {res}')
    return url, res

def download(url,path):
    r=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(r,timeout=240) as resp:
        path.write_bytes(resp.read())

# Map existing scene labels to the avatar references that should replace visible workers.
SCENES=[
('01_peter_team_site_check_driveway', ['Harald','Daniel','Lukas']),
('02_peter_customer_photo_review', ['Daniel','Lena']),
('03_team_laser_measure_foundation', ['Lukas','Tobias']),
('04_peter_spirit_level_post', ['Harald']),
('05_team_lifting_glulam_beam', ['Harald','Lukas','Tobias']),
('06_workshop_cutting_beam', ['Lukas']),
('07_workshop_plan_table_team', ['Harald','Daniel','Lena']),
('08_peter_roofline_inspection', ['Harald']),
('09_team_drainage_detail', ['Lukas','Daniel']),
('10_team_weather_side_screen', ['Lukas','Tobias']),
('11_peter_house_connection', ['Harald']),
('12_team_customer_handover_no_faces', ['Harald','Daniel','Lena']),
('13_worker_sanding_surface', ['Tobias']),
('14_team_loading_timber_truck', ['Lukas','Tobias']),
('15_peter_foundation_discussion', ['Harald','Daniel']),
('16_team_roof_board_installation', ['Lukas','Tobias']),
('17_peter_carport_depth_demo', ['Daniel']),
('18_team_rain_day_shelter', ['Harald','Lukas']),
('19_winter_check_team', ['Harald','Daniel']),
('20_team_detail_connection', ['Lukas']),
('21_peter_portrait_workshop', ['Harald']),
('22_team_group_finished_carport', ['Harald','Daniel','Lena','Lukas','Tobias']),
('23_worker_drilling_preparation', ['Lukas']),
('24_team_material_sorting', ['Lukas','Tobias']),
('25_peter_tablet_site_photo', ['Daniel']),
('26_team_under_roof_quality_check', ['Harald','Lukas']),
('27_peter_with_young_apprentice', ['Harald','Tobias']),
('28_team_clean_finished_driveway', ['Lukas','Tobias']),
('29_peter_evening_finished_carport', ['Harald']),
('30_team_walkthrough_sequence', ['Harald','Daniel','Lukas']),
]

manifest={'created_at':datetime.now(timezone.utc).isoformat(),'batch':'mp-team-scenes-avatar-replacement-2026-05-27-kie','model':'nano-banana-2','source_scenes':str(BASE_SCENES),'avatar_refs':{k:str(v) for k,v in AVATARS.items()},'avatar_urls':{},'base_scene_urls':{},'items':[]}
def save():
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))

print('Uploading avatar refs...', flush=True)
for name,path in AVATARS.items():
    url,res=upload_file(path)
    manifest['avatar_urls'][name]=url
    print('UPLOADED_AVATAR', name, url, flush=True); save(); time.sleep(.3)

for sid,names in SCENES:
    base_png=BASE_SCENES/f'{sid}.png'
    if not base_png.exists():
        print('MISSING_BASE', sid, base_png, flush=True)
        manifest['items'].append({'id':sid,'state':'missing_base'}); save(); continue
    base_url,_=upload_file(base_png)
    manifest['base_scene_urls'][sid]=base_url
    refs=[base_url]+[manifest['avatar_urls'][n] for n in names]
    people=', '.join(names)
    prompt=f'''Use the first supplied image as the exact base scene/composition reference.
This is a people-and-workwear replacement pass, not a redesign.
Keep the same camera angle, framing, carport/workshop/driveway setting, timber structure, tools, lighting, and documentary realism from the base scene.
Replace the visible worker/person identities and workwear with the supplied M&P avatar references: {people}.
Keep each referenced person's face, age impression, body type, red hoodie/workwear, and existing small white M&P chest logo/textile mark from the avatar reference as consistently as possible.
IMPORTANT LOGO RULE: do not invent a new logo, do not create colored logo patches, do not add fake letters, do not add extra badges. If the logo is small or partly hidden by pose/folds, that is correct. It should read as a subtle white textile print/embroidery on burgundy fabric, not a prominent advertising badge.
All workers must wear burgundy/dark red M&P hoodies or work jackets, dark work trousers, black work shoes. No generic black-only outfits. No random signage. No watermarks. No gibberish text.
Preserve physically plausible carpentry action: correct tools, believable hands, straight posts/beams, no Blechwinkel hero detail, no impossible structure.
True horizontal 16:9 realistic Austrian timber-construction photo.'''
    payload={'model':'nano-banana-2','input':{'prompt':prompt,'image_input':refs,'aspect_ratio':'16:9','resolution':'2K','output_format':'png'}}
    try:
        res=req('POST',CREATE,payload,90)
        tid=(res.get('data') or {}).get('taskId')
        item={'id':sid,'avatars':names,'task_id':tid,'state':'submitted','prompt':prompt,'image_input':refs,'submit_response':res}
        print('SUBMITTED',sid,tid,flush=True)
    except Exception as e:
        item={'id':sid,'avatars':names,'state':'submit_error','error':repr(e),'prompt':prompt,'image_input':refs}
        print('SUBMIT_ERROR',sid,repr(e),flush=True)
    manifest['items'].append(item); save(); time.sleep(.8)

pending={i['task_id']:i for i in manifest['items'] if i.get('task_id')}
start=time.time()
while pending and time.time()-start<4200:
    for tid,item in list(pending.items()):
        try:
            st=req('GET',STATUS.format(task_id=tid),None,45)
            data=st.get('data') or {}; state=(data.get('state') or '').lower()
            item['last_status']=st; item['state']=state
            print('STATUS',item['id'],state,flush=True)
            if state in {'success','failed','fail','error','cancelled','canceled'}:
                if state=='success':
                    rj=data.get('resultJson')
                    if isinstance(rj,str):
                        try: rj=json.loads(rj)
                        except Exception: rj={}
                    urls=(rj or {}).get('resultUrls') or []
                    item['result_urls']=urls
                    if urls:
                        path=IMG/f"{item['id']}.png"
                        download(urls[0],path)
                        item['file']=str(path)
                        try:
                            from PIL import Image
                            im=Image.open(path).convert('RGB')
                            webp=IMG/f"{item['id']}.webp"
                            im.save(webp,'WEBP',quality=88,method=6)
                            item['webp']=str(webp)
                        except Exception as e:
                            item['webp_error']=repr(e)
                        print('DOWNLOADED',path,flush=True)
                pending.pop(tid,None); save()
        except Exception as e:
            item['poll_error']=repr(e)
            print('POLL_ERROR',item['id'],repr(e),flush=True); save()
    if pending:
        time.sleep(22)
for item in pending.values():
    item['state']='timeout'
manifest['finished_at']=datetime.now(timezone.utc).isoformat()
save()

try:
    from PIL import Image, ImageDraw
    files=[Path(i.get('webp') or i.get('file')) for i in manifest['items'] if i.get('webp') or i.get('file')]
    thumbs=[]
    for f in files:
        im=Image.open(f).convert('RGB'); im.thumbnail((360,202))
        tile=Image.new('RGB',(390,248),(246,239,228))
        tile.paste(im,((390-im.width)//2,10))
        ImageDraw.Draw(tile).text((12,218),f.stem,fill=(24,24,24))
        thumbs.append(tile)
    cols=5; rows=(len(thumbs)+cols-1)//cols
    sheet=Image.new('RGB',(cols*390,rows*248),(32,38,30))
    for idx,t in enumerate(thumbs):
        sheet.paste(t,((idx%cols)*390,(idx//cols)*248))
    sheet_path=OUT/'_contact_sheet.jpg'
    sheet.save(sheet_path,quality=92)
    manifest['contact_sheet']=str(sheet_path); save()
    print('CONTACT_SHEET',sheet_path,flush=True)
except Exception as e:
    manifest['contact_sheet_error']=repr(e); save(); print('CONTACT_SHEET_ERROR',repr(e),flush=True)

success=sum(1 for i in manifest['items'] if i.get('state')=='success')
print(f'DONE success={success}/30 out={OUT}',flush=True)
