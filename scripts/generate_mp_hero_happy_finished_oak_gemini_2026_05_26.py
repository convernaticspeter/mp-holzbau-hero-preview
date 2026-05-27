import os, json, base64, time, subprocess
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'mp-hero-happy-finished-oak-2026-05-26-gemini'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'
CUSTOMER = Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau')
AVATAR_DIR = CUSTOMER / 'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20'
REFS = [
    ROOT/'assets/peter-preissinger-portrait.webp',
    ROOT/'assets/mp-workwear-corrections-2026-05-26-kie/01_peter_red_hoodie_plan_carport.webp',
    ROOT/'assets/mp-avatar-scenes-2026-05-26-kie/10_montage_abschlusskontrolle_team.webp',
    AVATAR_DIR/'Michael.png',
    AVATAR_DIR/'Markus.png',
    AVATAR_DIR/'Gerhard.png',
    AVATAR_DIR/'Tobias.png',
]
MODEL = 'gemini-3.1-flash-image-preview'

def api_key():
    for p in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip().startswith('GEMINI_API_KEY='):
                    return line.split('=',1)[1].strip().strip('"').strip("'")
    return subprocess.run(['bash','-lc','source ~/.hermes/.env 2>/dev/null; echo -n $GEMINI_API_KEY'],capture_output=True,text=True).stdout.strip()

def mime(path):
    if path.suffix.lower()=='.png': return 'image/png'
    if path.suffix.lower()=='.webp': return 'image/webp'
    return 'image/jpeg'

def imgpart(path):
    return {'inline_data': {'mime_type': mime(path), 'data': base64.b64encode(path.read_bytes()).decode('ascii')}}

BASE = '''Generate a premium photorealistic 16:9 hero image for M&P Holzbau.

Core emotion and composition:
- This must feel like ONE coherent happy completion moment, not random people standing around.
- Show 4 to 5 people grouped together closely as a real team/family moment after finishing the project.
- They are all visibly happy and proud because the new oak carport with covered walkway to the house entrance is finally finished.
- Use connected body language: close shoulder-to-shoulder grouping, slight inward lean, relaxed arms around shoulders or hands resting naturally, one person gesturing proudly toward the finished carport, warm genuine smiles.
- Avoid scattered/random spacing. Avoid people spread across the scene. Avoid stiff catalogue posing. Avoid lonely individuals at different depths.
- Peter Preissinger is the central/lead person: older Austrian Zimmermeister, short gray hair, gray stubble beard, calm proud happy expression.
- Team members match the supplied M&P avatar/team references. Do not invent random workers.
- All workers wear original-looking M&P workwear: burgundy/dark red hoodie or work jacket, dark work trousers, subtle small white M&P logo patch on left chest.

Scene:
- A very special FINISHED oak timber carport made from massive visible oak beams and posts.
- Wide enough for two cars and two motorcycles underneath, but completely empty: no cars, no motorcycles, no bicycles, no vans, no vehicles, no license plates anywhere.
- The completion should be clear: clean paved driveway, tidy site, no construction mess, final inspection/handover feeling.
- No Blechwinkel, no sheet-metal angle brackets, no shiny metal connector hero details. Use beautiful timber joinery: Nuten, Auflager, timber-to-timber supports, solid roof edge.
- The carport includes/continues into a covered walkway/canopy to the front entrance of the house.
- Medium-sized detached Austrian family house around 200 sqm, early 2000s, Vienna Basin / Wiener Becken: plaster facade, simple roof, realistic suburban Austrian house, not alpine chalet, not luxury villa.
- Nicely designed front garden with shrubs, grasses, gravel/stone path, clean driveway.

Hero usability:
- Wide horizontal landing-page hero, natural documentary lens, warm daylight, premium but real.
- Keep a calmer darker area on the left for headline overlay if possible; group can be center-right/right third.
- No watermark, no fake signs, no readable text except tiny M&P chest logo.
'''

SCENES = {
  '01_happy_group_close_front_right': 'Group Peter plus four M&P team members close together on the right third, all smiling naturally, one worker lightly points back to the finished oak carport and covered entrance walkway. Strong coherent team moment.',
  '02_happy_handover_finished_carport': 'Peter stands central with four happy team members in a compact semicircle, as if at the handover after finishing the carport. Finished clean empty bay, front garden and house entrance canopy visible.',
  '03_happy_team_under_edge': 'Five people stand together under the front edge of the finished oak carport, close and celebratory but natural, proud smiles, Peter central, huge empty bay and covered walkway to entrance clear behind them.',
  '04_happy_peter_team_carport_reveal': 'Peter and team are grouped as one unit in foreground right, all happy and proud, looking partly at camera and partly at the finished Eichencarport like a reveal photo. No random spacing, no vehicles.'
}

def contact(files):
    if not files: return None
    W,H=520,340; cols=2; rows=(len(files)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W,rows*H+60),(232,226,215)); d=ImageDraw.Draw(sheet)
    d.text((16,22),f'M&P happy finished Eichencarport hero — {len(files)} Varianten',fill=(20,20,20))
    for i,(label,path) in enumerate(files):
        im=Image.open(path).convert('RGB'); im.thumbnail((W,270))
        tile=Image.new('RGB',(W,H),'white'); tile.paste(im,((W-im.width)//2,8))
        td=ImageDraw.Draw(tile); td.rectangle([0,280,W,H],fill=(245,239,228)); td.text((10,292),label[:60],fill=(20,20,20))
        sheet.paste(tile,((i%cols)*W,60+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=92); return str(out)

def main():
    key=api_key()
    if not key: raise SystemExit('GEMINI_API_KEY missing')
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}'
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'model':MODEL,'output_dir':str(OUT),'refs':[str(p) for p in REFS],'scenes':{}}
    files=[]
    for label, scene in SCENES.items():
        prompt=BASE+'\nVariant-specific framing: '+scene
        parts=[{'text':prompt}]+[imgpart(p) for p in REFS if p.exists()]
        body={'contents':[{'parts':parts}], 'generationConfig': {'responseModalities':['TEXT','IMAGE']}}
        rec={'prompt':prompt,'state':'submitted','started_at':datetime.now(timezone.utc).isoformat()}
        try:
            r=requests.post(url,json=body,timeout=300); rec['http_status']=str(r.status_code); data=r.json(); rec['promptFeedback']=data.get('promptFeedback')
            imgdata=None; texts=[]
            for cand in data.get('candidates',[]):
                for part in cand.get('content',{}).get('parts',[]):
                    if 'text' in part: texts.append(part['text'])
                    obj=part.get('inlineData') or part.get('inline_data')
                    if obj and obj.get('data'): imgdata=base64.b64decode(obj['data'])
            rec['text']='\n'.join(texts)[:1000]
            if imgdata:
                png=OUT/(label+'.png'); png.write_bytes(imgdata)
                webp=OUT/(label+'.webp'); Image.open(png).convert('RGB').save(webp,quality=91,method=6)
                rec.update({'state':'success','file':str(webp),'source_png':str(png),'finished_at':datetime.now(timezone.utc).isoformat()})
                files.append((label,webp)); print('done',label,flush=True)
            else:
                rec['state']='no_image'; rec['response_preview']=json.dumps(data)[:2000]; print('no_image',label,rec.get('promptFeedback'),flush=True)
        except Exception as e:
            rec['state']='error'; rec['error']=str(e); print('error',label,e,flush=True)
        manifest['scenes'][label]=rec; MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        time.sleep(1)
    manifest['contact_sheet']=contact(files); manifest['finished_at']=datetime.now(timezone.utc).isoformat(); manifest['state']='finished'
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('contact_sheet',manifest['contact_sheet'],flush=True)

if __name__=='__main__': main()
