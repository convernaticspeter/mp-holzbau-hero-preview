import os, json, base64, time
from pathlib import Path
from datetime import datetime, timezone
import subprocess, requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'mp-hero-peter-team-oak-2026-05-26-gemini'
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
]
MODEL = 'gemini-3.1-flash-image-preview'

def api_key():
    for p in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip().startswith('GEMINI_API_KEY='):
                    return line.split('=',1)[1].strip().strip('"').strip("'")
    out = subprocess.run(['bash','-lc','source ~/.hermes/.env 2>/dev/null; echo -n $GEMINI_API_KEY'],capture_output=True,text=True).stdout.strip()
    return out

def mime(path):
    s=path.suffix.lower()
    if s=='.png': return 'image/png'
    if s=='.webp': return 'image/webp'
    return 'image/jpeg'

def imgpart(path):
    return {'inline_data': {'mime_type': mime(path), 'data': base64.b64encode(path.read_bytes()).decode('ascii')}}

BASE = '''Generate a new premium photorealistic 16:9 hero image for the M&P Holzbau landing page.

Use the supplied references as identity/workwear anchors:
- Peter Preissinger: older Austrian Zimmermeister, short gray hair, gray stubble beard, calm proud face, authentic craftsman presence.
- Team: 2 to 3 M&P assembly workers from the supplied avatar/team references.
- Clothing: original-looking M&P workwear: burgundy/dark red hoodies or work jackets, dark work trousers, subtle small white M&P logo patch on left chest only. No random generic people.

Required scene:
- Peter and team stand proudly and naturally in front of a very special wide oak timber carport.
- Carport made from massive visible oak beams/posts, premium carpentry, clean roof edge, timber-to-timber connections, Nuten and Auflager.
- Absolutely no Blechwinkel, no sheet-metal angle brackets, no shiny metal connector hero detail.
- Carport is wide enough for two cars and two motorcycles underneath, but it is completely empty.
- Hard negative: no cars, no motorcycles, no bicycles, no vans, no vehicles, no license plates anywhere in the image.
- In front of a medium-sized detached Austrian family house, about 200 sqm, built in early 2000s, Vienna Basin / Wiener Becken character: plaster facade, simple roof, suburban Austrian, not alpine chalet, not luxury villa.
- Well-designed front garden: grasses, shrubs, stone/gravel path, clean driveway.
- A canopy/roof connection continues from the carport toward the house entrance, making the covered path to the front door clear.

Hero layout:
- True wide horizontal landing-page hero.
- Leave clean, calmer, slightly darker space on the left for headline text overlay.
- Put Peter and team mostly center-right/right third.
- Warm daylight, documentary-real, premium but believable, not CGI, not showroom, no watermark, no readable text except subtle M&P chest logo.
'''

SCENES = {
  '01_hero_peter_team_right_empty_oak': 'Peter in the right third with two team members slightly behind, the empty oak carport and shaded driveway create clean text space on the left.',
  '02_hero_team_under_roof_big_span': 'Peter and three team members stand just outside the open empty bay; the huge oak roof span clearly reads as two-car-plus-motorcycle size; no vehicles visible.',
  '03_hero_front_garden_canopy_house': 'Broader front garden and house view, with the carport canopy visibly leading toward the entrance; Peter and team on right, calm proud mood.',
  '04_hero_low_angle_oak_craft_peter': 'Slightly lower angle emphasizing massive oak posts, Nuten/Auflager and craftsmanship; Peter foreground right, team behind, early-2000s house background.'
}

def save_contact(files):
    if not files: return None
    W,H=520,340; cols=2; rows=(len(files)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W,rows*H+60),(232,226,215)); d=ImageDraw.Draw(sheet)
    d.text((16,22),f'M&P Hero Peter + Team / Eiche — {len(files)} Varianten',fill=(20,20,20))
    for i,(label,path) in enumerate(files):
        im=Image.open(path).convert('RGB'); im.thumbnail((W,270))
        tile=Image.new('RGB',(W,H),'white'); tile.paste(im,((W-im.width)//2,8))
        td=ImageDraw.Draw(tile); td.rectangle([0,280,W,H],fill=(245,239,228)); td.text((10,292),label[:60],fill=(20,20,20))
        sheet.paste(tile,((i%cols)*W,60+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'; sheet.save(out,quality=92); return str(out)

def main():
    key=api_key()
    if not key: raise SystemExit('GEMINI_API_KEY missing')
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'model':MODEL,'output_dir':str(OUT),'refs':[str(p) for p in REFS],'scenes':{}}
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}'
    files=[]
    for label,scene in SCENES.items():
        prompt=BASE+'\nVariant-specific framing: '+scene
        parts=[{'text':prompt}]+[imgpart(p) for p in REFS if p.exists()]
        body={'contents':[{'parts':parts}], 'generationConfig': {'responseModalities':['TEXT','IMAGE']}}
        rec={'prompt':prompt,'state':'submitted','started_at':datetime.now(timezone.utc).isoformat()}
        try:
            r=requests.post(url,json=body,timeout=300)
            rec['http_status']=r.status_code
            data=r.json()
            rec['promptFeedback']=data.get('promptFeedback')
            imgdata=None
            texts=[]
            for cand in data.get('candidates',[]):
                for part in cand.get('content',{}).get('parts',[]):
                    if 'text' in part: texts.append(part['text'])
                    obj=part.get('inlineData') or part.get('inline_data')
                    if obj and obj.get('data'): imgdata=base64.b64decode(obj['data'])
            rec['text']='\n'.join(texts)[:1000]
            if not imgdata:
                rec['state']='no_image'; rec['response_preview']=json.dumps(data)[:2000]
                print('no_image',label,rec.get('promptFeedback'),flush=True)
            else:
                png=OUT/(label+'.png'); png.write_bytes(imgdata)
                webp=OUT/(label+'.webp')
                Image.open(png).convert('RGB').save(webp,quality=90,method=6)
                rec.update({'state':'success','file':str(webp),'source_png':str(png),'finished_at':datetime.now(timezone.utc).isoformat()})
                files.append((label,webp)); print('done',label,flush=True)
        except Exception as e:
            rec['state']='error'; rec['error']=str(e); print('error',label,e,flush=True)
        manifest['scenes'][label]=rec
        MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        time.sleep(1)
    manifest['contact_sheet']=save_contact(files)
    manifest['finished_at']=datetime.now(timezone.utc).isoformat()
    manifest['state']='finished'
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('contact_sheet',manifest['contact_sheet'],flush=True)

if __name__=='__main__': main()
