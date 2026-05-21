import os, json, time, base64, mimetypes
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'generated-carports-2026-05-21-realism-b2'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'
LOGO = ROOT / 'assets' / 'logo.png'
MODEL = 'gemini-3.1-flash-image-preview'

for env_path in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
API_KEY=os.environ.get('GEMINI_API_KEY')

SCENES = {
    '01_real_baustelle_posts_beams': 'Realistic documentary worksite photo: two carpenters installing straight timber posts and a main beam for a simple attached carport beside a normal Austrian family house. Dark charcoal/navy work trousers and jackets, muted burgundy/dark-grey small chest patch inspired by the supplied logo, no readable text. The workers are actively aligning a beam with a level and clamps; no smiling, no posing. The carport is only partly built, so the construction logic is clear.',
    '02_real_baustelle_roof_frame': 'Realistic documentary worksite photo: partially built timber carport roof frame, rafters and beams visible, ladder and sawhorses in plausible positions, one carpenter fastening a rafter while another holds it. Normal Austrian driveway, no car, tidy Baustelle. Dark M&P-style workwear: charcoal/navy with subtle burgundy/grey branding patch, no readable logo text.',
    '03_real_measurement_driveway': 'Realistic planning appointment photo: carpenter kneeling at an existing driveway, tape measure stretched between house wall and future post position, chalk marks on paving, clipboard nearby. Normal Austrian home, no finished carport yet. Workwear dark charcoal/navy with small muted burgundy/grey patch, not a stock-photo smile.',
    '04_real_house_connection_check': 'Realistic close-medium photo: carpenter checking the wall connection line and roof height for an attached timber carport, holding a level against a cream plaster house facade. Show hands, level, wall, timber sample; face not central. Dark practical M&P-style workwear, subtle non-readable patch.',
    '05_real_post_base_detail_worker_hands': 'Close documentary detail: worker hands setting a metal post base bracket into concrete/paving for a timber carport post. Gloves, drill, anchor bolts, dust, realistic tools. Physically correct bracket, no fantasy metal, no text.',
    '06_real_beam_joinery_hands': 'Close documentary detail: carpenter hands fitting a timber beam/post connection with visible screw holes and metal connector plate, believable joinery, natural wood grain, dark work sleeve visible with subtle burgundy/grey patch, no readable text.',
    '07_real_gutter_installation': 'Realistic worksite photo: carpenter installing a gutter/downpipe along the front roof edge of a timber carport, roof slope believable, water path logical. Normal Austrian house and driveway, no rain, no car. Dark M&P-style workwear, no readable text.',
    '08_real_finished_inspection_empty_bay': 'Realistic finished-project inspection photo: two carpenters from side/back checking a completed timber carport with empty bay, one holds clipboard, one touches a post/beam detail. Normal Austrian home, no car, no posed team portrait. Dark charcoal/navy workwear, subtle burgundy/grey patch.',
    '09_real_worker_toolbelt_detail': 'Close waist-up documentary photo: carpenter in dark charcoal/navy workwear with tool belt, folding rule, pencil, cordless drill, standing next to timber carport beam. Subtle muted burgundy/grey chest patch inspired by logo, not readable, no face focus.',
    '10_real_material_consultation': 'Realistic consultation scene outside a house: timber samples, roof sheet sample, pencil, small plan with no readable text, hands of carpenter and homeowner comparing materials on a simple outdoor table. Practical, not luxury showroom.',
    '11_real_under_roof_structure': 'Realistic view from under a newly built empty timber carport, showing straight beams, rafters, correct roof underside, clean dry paving below. No cars, no people, no weird geometry, normal Austrian house context.',
    '12_real_side_weather_wall_install': 'Worksite photo: carpenter fixing vertical timber slats as a weather side wall on a carport. Slats straight with realistic spacing, clamps and screws visible, dark M&P-style workwear, no readable text, no car.',
    '13_real_rain_dry_zone_no_worker': 'After-rain documentary photo of a completed timber carport: wet driveway outside roof footprint, dry sheltered empty bay under roof, soft irregular wet-dry transition, gutter/downpipe visible and logical. No car, no people, no dramatic CGI.',
    '14_real_snow_cleared_access_no_worker': 'Winter documentary photo: completed timber carport with empty bay, under-roof paving dry and snow-free, driveway cleared from foreground into bay, snow only outside, realistic plowed edges. No car, no people, no snow under roof.',
    '15_real_windy_weather_side_no_worker': 'Overcast windy day: completed timber carport with vertical slatted weather side, empty bay sheltered, shrubs slightly bent, no flying fantasy debris, structure stable and straight. Normal Austrian residential setting.',
    '16_real_finished_house_integration': 'Realistic finished timber carport attached to a cream plaster Austrian home, empty bay, roof line and posts proportional, clear walking route to entrance, no car. Photograph should look like a real completed job, not an architect rendering.',
    '17_real_dark_facade_integration': 'Realistic completed carport beside a modern dark facade house, dark-stained timber matching the house, empty bay, correct shadows and roof depth, no car, no CGI sheen.',
    '18_real_traditional_house_integration': 'Realistic completed warm timber carport beside a traditional Austrian house with clay roof tiles, empty bay, practical driveway, not a catalogue render, no car.',
    '19_real_entry_roof_connection': 'Realistic photo showing protective roof line from carport toward entrance, empty bay and dry walkway visible, Austrian house context, no impossible supports, no car.',
    '20_real_double_carport_grounded': 'Realistic double timber carport, empty two-car bay, simple robust posts and beams, proportional roof, visible drainage, normal suburban Austrian home, no car and no grand luxury villa.',
    '21_real_quality_walkaround_worker': 'Documentary photo: carpenter walking around a completed carport checking post alignment with a level. Side/back view, dark M&P-style workwear, muted burgundy/grey small patch, no readable text, empty bay.',
    '22_real_roof_edge_detail': 'Close realistic detail of timber carport roof edge, eaves, gutter, downpipe, screws and wood grain. Show correct slope and drainage; no random water streams, no text.',
    '23_real_team_small_backview': 'Small team of two carpenters from behind at a real worksite, carrying a timber beam together. Dark charcoal/navy practical workwear with subtle burgundy/grey patch inspired by M&P logo, no readable text, no posing, no stock smiles.',
    '24_real_finished_evening_grounded': 'Grounded evening photo of a completed timber carport at a normal Austrian home, warm house light, empty bay, no car, realistic shadows, no cinematic fantasy, no CGI perfection.'
}

GLOBAL = """
Generate a photorealistic horizontal 16:9 image for M&P Holzbau, an Austrian Zimmermeisterbetrieb.
Use the supplied logo ONLY as a color/style reference for subtle workwear branding: dark/charcoal/navy clothes, muted burgundy and dark grey accent patch. Do NOT render readable logo text or fake lettering.
Strict realism filter: this must look like a real phone/camera documentary photo from a carpentry job, not a 3D render, not a stock image, not an AI fantasy.
Physical construction logic is mandatory: vertical posts, straight beams, plausible spans, proper metal brackets, realistic tools, believable roof slope, gutters/downpipes only where they make sense.
No impossible roof geometry, no floating beams, no decorative nonsense, no fake water behavior, no over-perfect luxury villa, no people smiling at camera, no high-vis construction helmets unless the exact task needs them.
Default: no cars, no vans, no bicycles. The carport bay should be empty unless explicitly stated otherwise.
""".strip()

def b64(path):
    return base64.b64encode(path.read_bytes()).decode('ascii')

def save(m):
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')

def generate(label, prompt):
    parts=[{'text': GLOBAL + '\n\nScene: ' + prompt}]
    if LOGO.exists():
        parts.append({'inline_data': {'mime_type': 'image/png', 'data': b64(LOGO)}})
    body={
        'contents':[{'parts':parts}],
        'generationConfig': {'responseModalities':['TEXT','IMAGE']}
    }
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}'
    r=requests.post(url, json=body, timeout=300)
    try:
        data=r.json()
    except Exception:
        raise RuntimeError(f'non-json {r.status_code}: {r.text[:500]}')
    if r.status_code >= 400:
        raise RuntimeError(f'http {r.status_code}: {data}')
    image_bytes=None
    text=[]
    for c in data.get('candidates', []):
        for p in c.get('content', {}).get('parts', []):
            if 'text' in p:
                text.append(p['text'])
            img=p.get('inlineData') or p.get('inline_data')
            if img and img.get('data'):
                image_bytes=base64.b64decode(img['data'])
                break
        if image_bytes:
            break
    if not image_bytes:
        raise RuntimeError('no image returned: ' + json.dumps(data.get('promptFeedback') or data, ensure_ascii=False)[:1000])
    return image_bytes, data, '\n'.join(text)

def contact_sheet(scenes):
    items=[]
    for label, info in scenes.items():
        f=info.get('file')
        if f and Path(f).exists():
            items.append((label, Path(f)))
    if not items:
        return None
    W,H=360,270
    cols=4
    rows=(len(items)+cols-1)//cols
    sheet=Image.new('RGB', (cols*W, rows*H+54), (232,226,215))
    d=ImageDraw.Draw(sheet)
    d.text((16,18), f'M&P Holzbau realism/workwear B2 — {len(items)} images', fill=(20,20,20))
    for i,(label,path) in enumerate(items):
        im=Image.open(path).convert('RGB')
        im.thumbnail((W,205))
        tile=Image.new('RGB',(W,H),'white')
        tile.paste(im,((W-im.width)//2,8))
        td=ImageDraw.Draw(tile)
        td.rectangle([0,215,W,H], fill=(245,239,228))
        td.text((8,224),label[:45],fill=(20,20,20))
        sheet.paste(tile,((i%cols)*W,54+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'
    sheet.save(out, quality=90)
    return str(out)

def main():
    if not API_KEY:
        raise SystemExit('GEMINI_API_KEY missing')
    manifest={'created_at': datetime.now(timezone.utc).isoformat(), 'model': MODEL, 'state':'running', 'global_prompt': GLOBAL, 'logo_reference': str(LOGO), 'scenes': {}}
    if MANIFEST.exists():
        try:
            manifest=json.loads(MANIFEST.read_text())
            manifest.setdefault('scenes', {})
        except Exception:
            pass
    for label,prompt in SCENES.items():
        if manifest['scenes'].get(label, {}).get('file'):
            continue
        info={'prompt':prompt, 'state':'running', 'started_at': datetime.now(timezone.utc).isoformat()}
        manifest['scenes'][label]=info
        save(manifest)
        try:
            img, raw, text = generate(label,prompt)
            out=OUT/(label+'.png')
            out.write_bytes(img)
            info.update({'state':'success','file':str(out),'text':text,'finished_at':datetime.now(timezone.utc).isoformat()})
            print('done', label, flush=True)
        except Exception as e:
            info.update({'state':'failed','error':str(e),'finished_at':datetime.now(timezone.utc).isoformat()})
            print('failed', label, str(e), flush=True)
        save(manifest)
        time.sleep(1.5)
    manifest['contact_sheet']=contact_sheet(manifest['scenes'])
    manifest['finished_at']=datetime.now(timezone.utc).isoformat()
    manifest['state']='finished'
    save(manifest)
    print('contact_sheet', manifest.get('contact_sheet'), flush=True)
    print('done finished', flush=True)

if __name__ == '__main__':
    main()
