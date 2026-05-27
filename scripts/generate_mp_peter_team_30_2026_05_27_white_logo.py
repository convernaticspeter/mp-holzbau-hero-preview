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
OUT=ROOT/'assets/mp-peter-team-scenes-2026-05-27-kie-white-logo-v2'
IMG=OUT/'images'
IMG.mkdir(parents=True, exist_ok=True)

REF_CACHE=OUT/'_refs_local'
REFS={
    'logo': REF_CACHE/'logo-white-transparent.png',
    'peter1': REF_CACHE/'peter-preissinger-1.jpeg',
    'peter2': REF_CACHE/'peter-preissinger-2.jpeg',
    'peter3': REF_CACHE/'peter-preissinger-3.jpeg',
    'peter4': REF_CACHE/'peter-preissinger-4.jpeg',
}

headers_json={'Authorization':f'Bearer {API_KEY}','Content-Type':'application/json','Accept':'application/json','User-Agent':'Mozilla/5.0'}

def req(method,url,payload=None,timeout=90):
    data=json.dumps(payload).encode() if payload is not None else None
    r=urllib.request.Request(url,data=data,headers=headers_json,method=method)
    with urllib.request.urlopen(r,timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def read_bytes_retry(path: Path, attempts=8):
    last=None
    for n in range(attempts):
        try:
            return path.read_bytes()
        except OSError as e:
            last=e
            print('READ_RETRY', path, repr(e), flush=True)
            time.sleep(1.5 * (n + 1))
    if last is not None:
        raise last
    raise RuntimeError(f'could not read {path}')

def upload_file(path: Path):
    boundary='----HermesBoundary' + str(int(time.time()*1000))
    parts=[]
    def field(name,value):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    def filepart(name,path):
        ctype=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{path.name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode())
        parts.append(read_bytes_retry(path)); parts.append(b'\r\n')
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

identity='''Use the supplied real Peter Preissinger photos as identity anchors whenever Peter appears: Austrian male Zimmermeister, late 50s/early 60s, short gray hair, gray stubble beard, natural experienced face. Preserve age and character; do not make him younger or turn him into a generic model.'''
brand='''M&P Holzbau documentary image set. Workwear must be burgundy/dark red M&P work jackets or hoodies, dark grey/black work trousers, black safety shoes. Use the supplied WHITE M&P logo with transparent background as the exact logo reference: only one small believable white chest print/embroidery or sleeve print directly on burgundy fabric, no colored/normal logo, no dark-background logo asset, no fake text, no extra logos, no huge centered branding. If the logo is too small to read, keep it as a subtle white textile mark rather than inventing letters.'''
quality='''Realistic Austrian/DACH small-business timber construction photography, Wiener Becken / Lower Austria / Burgenland residential context, natural overcast daylight, no Alps, no stock-photo smile, no AI gloss, no random signage, no watermarks, no gibberish text, no impossible beams, no Blechwinkel hero detail. Structurally plausible timber carport craft: straight posts, rafters, clean joints, roof depth, drainage and house fit. True horizontal 16:9 photo.'''

SCENES=[
('01_peter_team_site_check_driveway','Peter and two team members stand at a residential driveway with a printed plan and measuring wheel, checking carport position and turning radius.'),
('02_peter_customer_photo_review','Peter holds a tablet with driveway photos while a colleague marks measurements on a clipboard beside a timber carport bay; no customer face visible.'),
('03_team_laser_measure_foundation','Two M&P workers use a laser level and tape measure to mark foundation points on paving for a carport.'),
('04_peter_spirit_level_post','Peter checks a tall carport post with a long spirit level, roof line visible above, realistic scale.'),
('05_team_lifting_glulam_beam','Three workers carefully position a glulam beam on prepared posts, safe controlled movement, no crane fantasy.'),
('06_workshop_cutting_beam','A worker in M&P hoodie marks and cuts a glulam beam in the workshop, saw setup safe and realistic.'),
('07_workshop_plan_table_team','Peter and two colleagues review plans on a large workshop table with timber samples and fasteners sorted neatly.'),
('08_peter_roofline_inspection','Peter inspects the finished roof line of a timber carport from a side angle, hand on beam, calm expert expression.'),
('09_team_drainage_detail','Two workers discuss gutter/downpipe routing on a carport roof edge, waterführung visibly part of the craft.'),
('10_team_weather_side_screen','Team installs or checks a timber weather-side screen on one side of a carport, clean vertical battens.'),
('11_peter_house_connection','Peter checks the junction between house façade and carport roof, showing how the structure fits the house.'),
('12_team_customer_handover_no_faces','Peter and team at a finished carport handover, customers only from behind or out of focus, focus on carport and craft.'),
('13_worker_sanding_surface','Close documentary scene: worker sanding or finishing timber surface on a beam, M&P sleeve patch visible, hands plausible.'),
('14_team_loading_timber_truck','Team loads prepared beams onto a small truck/trailer in yard, safe straps and organized material.'),
('15_peter_foundation_discussion','Peter kneels near foundation point with plan and marker, explaining base position to colleague, no customer face.'),
('16_team_roof_board_installation','Two workers install roof boards/underside planking on a carport, realistic ladders/scaffold, no dangerous pose.'),
('17_peter_carport_depth_demo','Peter stands beside a parked car fully under roof and points to the generous door-opening space; car protected, blank plate.'),
('18_team_rain_day_shelter','Team under completed carport during rain, dry sheltered interior visible, not theatrical storm.'),
('19_winter_check_team','Peter and one colleague check a carport in winter conditions, snow outside, structure clean and stable.'),
('20_team_detail_connection','Close scene of worker checking clean timber joint/connection with pencil and folding rule, avoid metal angle-bracket hero.'),
('21_peter_portrait_workshop','Peter portrait in workshop, burgundy M&P jacket, timber and plans behind him, professional but natural.'),
('22_team_group_finished_carport','Peter with three team members in front of a finished timber carport, relaxed not posed like stock, logo patches subtle.'),
('23_worker_drilling_preparation','Worker prepares a precise pre-drill on timber beam at bench, clamp visible, safe realistic tool use.'),
('24_team_material_sorting','Two workers sort labeled timber parts before transport, labels are blank/unreadable, organized craft process.'),
('25_peter_tablet_site_photo','Peter uses tablet on site to compare driveway photo/plan, carport structure behind, one colleague measuring in background.'),
('26_team_under_roof_quality_check','Team checks roof underside, alignment and straightness under a new carport, natural daylight.'),
('27_peter_with_young_apprentice','Peter explains a timber detail to a younger apprentice, respectful training moment, no staged thumbs-up.'),
('28_team_clean_finished_driveway','Workers sweep/clean finished driveway around a new carport, shows handover quality and tidy site.'),
('29_peter_evening_finished_carport','Peter at dusk beside warmly lit completed timber carport, quiet proud expression, not glossy luxury ad.'),
('30_team_walkthrough_sequence','Peter and team walk through a finished carport checking final points: post, roof edge, drainage, clear car space.'),
]

manifest={'created_at':datetime.now(timezone.utc).isoformat(),'batch':'mp-peter-team-scenes-2026-05-27-kie-white-logo-v2','model':'nano-banana-2','refs':{k:str(v) for k,v in REFS.items()},'ref_urls':{},'items':[]}

def save():
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))

print('Uploading refs...', flush=True)
for k,p in REFS.items():
    if not p.exists():
        print('REF_MISSING',k,p,flush=True); continue
    url,res=upload_file(p)
    manifest['ref_urls'][k]=url
    print('UPLOADED',k,url,flush=True)
    save()

peter_urls=[manifest['ref_urls'][k] for k in ['peter1','peter2','peter3','peter4'] if k in manifest['ref_urls']]
logo_url=manifest['ref_urls'].get('logo')

for sid,goal in SCENES:
    includes_peter = 'peter' in sid or sid in {'01_peter_team_site_check_driveway','05_team_lifting_glulam_beam','07_workshop_plan_table_team','12_team_customer_handover_no_faces','22_team_group_finished_carport','27_peter_with_young_apprentice','30_team_walkthrough_sequence'}
    refs=[]
    if includes_peter:
        refs.extend(peter_urls[:4])
    if logo_url:
        refs.append(logo_url)
    prompt=f"{identity if includes_peter else ''}\n\n{brand}\n\n{quality}\n\nScene: {goal}\n\nImportant: create an original documentary photo, not a collage. Correct anatomy and hands. The logo patch must be small and physically attached to workwear, never floating."
    payload={'model':'nano-banana-2','input':{'prompt':prompt,'image_input':refs,'aspect_ratio':'16:9','resolution':'2K','output_format':'png'}}
    try:
        res=req('POST',CREATE,payload,90)
        tid=(res.get('data') or {}).get('taskId')
        item={'id':sid,'task_id':tid,'state':'submitted','prompt':prompt,'image_input':refs,'submit_response':res}
        print('SUBMITTED',sid,tid,flush=True)
    except Exception as e:
        item={'id':sid,'state':'submit_error','error':repr(e),'prompt':prompt}
        print('SUBMIT_ERROR',sid,repr(e),flush=True)
    manifest['items'].append(item); save()
    time.sleep(1.2)

pending={i['task_id']:i for i in manifest['items'] if i.get('task_id')}
start=time.time()
while pending and time.time()-start<3600:
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
                        # convert to webp for site use
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

# Contact sheet
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
    manifest['contact_sheet']=str(sheet_path)
    save()
    print('CONTACT_SHEET',sheet_path,flush=True)
except Exception as e:
    manifest['contact_sheet_error']=repr(e); save(); print('CONTACT_SHEET_ERROR',repr(e),flush=True)

success=sum(1 for i in manifest['items'] if i.get('state')=='success')
print(f'DONE success={success}/30 out={OUT}',flush=True)
