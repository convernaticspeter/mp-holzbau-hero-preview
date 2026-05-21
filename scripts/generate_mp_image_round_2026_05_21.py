import os, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'generated-carports-2026-05-21-image-round-b1'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'

for env_path in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY = os.environ.get('KIE_API_KEY')
CREATE = 'https://api.kie.ai/api/v1/jobs/createTask'
STATUS = 'https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}'
HEADERS = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'} if API_KEY else {}
STATUS_HEADERS = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else {}
MODEL = 'gpt-image-2-text-to-image'

GLOBAL = """
Photorealistic documentary and architectural imagery for M&P Holzbau, an Austrian Zimmermeisterbetrieb building custom timber carports in Vienna, Lower Austria and Burgenland.
The images must feel like believable local craft/trade website photography, not CGI, not a generic stock render, not a luxury architecture magazine fantasy.
Regional DACH/Austrian houses, realistic driveways, timber construction, cream plaster, clay roof tiles or modern dark facades, practical family homes.
IMPORTANT: default to an EMPTY carport bay. No cars, no vans, no bicycles parked in the carport or driveway unless the scene explicitly says otherwise. Keep the parking bay visibly empty and usable.
Physical logic: structurally plausible timber beams, posts vertical and straight, believable roof thickness, gutters/downpipes where needed, correct shadows and perspective, no impossible cantilevers.
No readable text, no logos, no watermarks, no fake signage, no license plates, no people posing at camera unless explicitly described. Natural daylight, realistic lens, slight imperfection, believable weather and materials.
Composition must be website-usable: clean subject, no awkward crops, enough visual calm for landing page sections, horizontal 16:9 unless otherwise specified.
""".strip()

SCENES = {
    # Architecture / hero candidates: empty bays, strong house integration
    '01_hero_attached_dark_timber_empty_bay': 'Wide horizontal hero photo: a custom attached timber carport with dark-stained wood matched to a modern Austrian house facade, fully empty parking bay, clean paved driveway, visible roof depth and front overhang, early morning soft light.',
    '02_hero_rural_warm_timber_empty_bay': 'Wide horizontal hero photo: warm natural timber carport attached to a rural Austrian family house, clay roof tiles nearby, empty bay, gravel and paved driveway, honest carpentry feel, not showroom-perfect.',
    '03_hero_modern_plaster_timber_empty_bay': 'Modern cream plaster house with a simple custom timber carport integrated into the entrance side, empty parking bay, proportional roof line, visible gutter and downpipe, calm overcast daylight.',
    '04_hero_corner_house_carport_empty_bay': 'Three-quarter view of a corner-position carport beside an Austrian family house, empty bay, generous walking space to the front door, roof clearly protects the path, realistic garden edges.',
    '05_hero_double_carport_no_cars': 'A double timber carport for two vehicles, completely empty, broad paved driveway, straight posts, well-proportioned roof and beams, normal suburban Lower Austria house, natural light.',
    '06_hero_closed_weather_side_no_cars': 'Custom timber carport with one closed weather side using vertical timber slats, empty parking bay, practical wind/rain protection readable, Austrian residential driveway, no car.',
    '07_hero_black_roof_timber_no_cars': 'Dark metal roof with timber substructure, empty bay, modern Austrian detached house, clean drainage line and downpipe visible, subdued premium craft look.',
    '08_hero_long_roof_to_entrance_no_cars': 'Long protective roof line from carport toward house entrance, empty parking area, dry covered walking route visible, Austrian family home, realistic paving and garden.',
    '09_hero_snow_empty_clean_bay': 'Winter hero photo: timber carport attached to Austrian home, carport bay completely snow-free and empty, 15-20 cm snow outside only, driveway visibly cleared from foreground to bay, no car.',
    '10_hero_rain_empty_dry_bay': 'Rain hero photo: timber carport at Austrian house, rain outside, glossy wet paving beyond roof edge, under-roof bay fully dry and empty, gutter/downpipe logic believable, no car.',

    # Detail / craft proof
    '11_detail_beam_joinery': 'Close architectural detail photo of timber carport beam and post connection, clean carpentry joinery, metal fasteners discreet and plausible, natural wood grain, shallow depth of field, no people.',
    '12_detail_gutter_downpipe_water_path': 'Close detail of carport roof edge with real gutter, downpipe and controlled drainage into paving channel, wet outside surface, dry sheltered zone visible, physically believable water path.',
    '13_detail_foundation_post_base': 'Close documentary photo of timber carport post base anchored into concrete footing with clean metal bracket, realistic driveway paving around it, craft quality proof, no text.',
    '14_detail_roof_overhang_shadow': 'Architectural close-up of a timber carport roof overhang casting a dry shadow line on paving, visible roof depth and timber beams, realistic Austrian residential facade.',
    '15_detail_slatted_weather_wall': 'Detail photo of vertical timber slat weather wall on a carport, craftsmanship, straight spacing, warm wood texture, garden and house softly in background.',
    '16_detail_roof_structure_underneath': 'View from under an empty timber carport looking up at roof structure, straight beams, clean underside, warm timber, dry sheltered paving below, no car.',
    '17_detail_measurement_on_driveway': 'Documentary detail: tape measure and chalk marks on a paved driveway where a carport will be planned, timber sample board and pencil nearby, no visible logos, realistic consultation scene.',
    '18_detail_material_samples': 'Close photo of timber samples, roof color samples, pencil and folded plan on an outdoor table at an Austrian house, practical planning mood, no readable text.',

    # Planning / before-after / onsite proof
    '19_planning_site_check_driveway': 'Documentary photo: Zimmermeister-style site inspection at an Austrian driveway, one craftsman in dark workwear seen from side/back holding clipboard and measuring tape, no logo text, no posing, empty driveway.',
    '20_planning_house_connection_discussion': 'Two tradesmen from behind discussing the house connection and roof line beside a partially marked driveway, natural workwear, no smiling to camera, carport not built yet, realistic local appointment.',
    '21_construction_posts_beams_install': 'Documentary construction photo: timber carport posts and main beams being installed at a family house, two workers in dark workwear, safe tidy Baustelle, no readable logos, no car, realistic tools.',
    '22_construction_roof_frame': 'Part-built timber carport roof frame at an Austrian home, empty driveway, scaffolding/ladder plausible, straight beams, no fantasy construction errors.',
    '23_finished_driveway_empty': 'Finished carport with empty driveway bay and clean landscaping, looks like it belonged to the house from the first day, proportional to facade, no car.',
    '24_team_from_back_at_site': 'Small M&P-style carpentry team from behind at a completed empty carport, dark navy/charcoal workwear without readable logos, checking details, not posing, credible Meisterbetrieb feel.',

    # Section-specific proof scenes
    '25_quality_foundation_context': 'Wider scene showing carport posts aligned with driveway and house entrance, empty bay, foundation/post placement feels deliberately planned for door clearance and movement.',
    '26_quality_door_clearance_empty': 'Empty carport bay beside house entrance showing generous door-opening and walking space, no car, composition makes the practical clearance benefit understandable.',
    '27_quality_water_after_rain': 'After rain: timber carport with empty dry sheltered bay, wet uncovered paving outside, visible gutter/downpipe, no puddles inside the sheltered area, soft realistic wet/dry transition.',
    '28_quality_weather_side_wind': 'Windy overcast day: carport with vertical timber weather side, shrubs bent slightly in wind, sheltered empty bay remains calm and dry, Austrian house context.',
    '29_quality_winter_access': 'Winter practical scene: empty carport bay with dry paving under roof, snow outside and cleared access path from foreground to house entrance, no car, no snow piles under roof.',
    '30_quality_solar_wallbox_empty': 'Modern timber carport prepared for solar/wallbox use, discreet wallbox on house wall, empty bay, roof geometry plausible, no cables spaghetti, no fake branding.',

    # More editorial / page atmosphere, still grounded
    '31_atmosphere_morning_woodgrain': 'Editorial close-medium shot of morning light across timber beams and empty paved bay, Austrian house facade softly visible, premium but practical, no car.',
    '32_atmosphere_evening_warm_lights': 'Evening exterior of a warm timber carport with subtle house lights on, empty bay, calm residential mood, not cinematic fantasy, no car.',
    '33_atmosphere_autumn_driveway': 'Autumn Austrian driveway with custom timber carport, leaves outside, empty bay clean and usable, house and garden context, realistic colors.',
    '34_atmosphere_modern_dark_facade': 'Modern dark facade house with matching dark-stained timber carport, empty bay, crisp but realistic local craft aesthetic, no car, no showroom CGI.',
    '35_atmosphere_traditional_house': 'Traditional Austrian house with timber carport carefully integrated without looking like a cheap kit, empty bay, warm daylight, natural garden, no car.',
    '36_atmosphere_detail_to_house': 'Architectural detail showing how timber carport roof line meets existing house facade, gutter, wall connection and clean transition, empty space below, no car.',
}

def slug(name: str) -> str:
    return re.sub(r'[^a-z0-9_\-]+', '-', name.lower()).strip('-')

def save(manifest):
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

def create_task(label, prompt):
    body = {
        'model': MODEL,
        'input': {
            'prompt': GLOBAL + '\n\nScene: ' + prompt,
            'aspect_ratio': '16:9',
            'resolution': '1K',
            'output_format': 'png'
        }
    }
    r = requests.post(CREATE, headers=HEADERS, json=body, timeout=120)
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f'{label} non-json response {r.status_code}: {r.text[:500]}')
    if data.get('code') != 200:
        raise RuntimeError(f'{label} submit failed: {data}')
    return data['data']['taskId'], body

def result_urls(sd):
    raw = sd.get('resultJson') or ''
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    return parsed.get('resultUrls') or parsed.get('result_urls') or []

def contact_sheet(scenes):
    items=[]
    for label, info in scenes.items():
        f=info.get('file')
        if f and Path(f).exists():
            items.append((label, Path(f)))
    if not items:
        return None
    W,H=360,275
    thumbs=[]
    for label,path in items:
        im=Image.open(path).convert('RGB')
        im.thumbnail((W,210))
        tile=Image.new('RGB',(W,H),'white')
        tile.paste(im,((W-im.width)//2,8))
        d=ImageDraw.Draw(tile)
        d.rectangle([0,218,W,H], fill=(245,239,228))
        d.text((8,226),label[:46],fill=(20,20,20))
        thumbs.append(tile)
    cols=4
    rows=(len(thumbs)+cols-1)//cols
    sheet=Image.new('RGB',(cols*W,rows*H+54),(232,226,215))
    d=ImageDraw.Draw(sheet)
    d.text((16,18),f'M&P Holzbau image round b1 — {len(items)} / {len(SCENES)} images — text-only no-car bias',fill=(20,20,20))
    for i,t in enumerate(thumbs):
        sheet.paste(t,((i%cols)*W,54+(i//cols)*H))
    out=OUT/'_contact_sheet.jpg'
    sheet.save(out,quality=90)
    return str(out)

def main():
    manifest = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'batch': 'mp-image-round-b1-2026-05-21',
        'model': MODEL,
        'state': 'init',
        'output_dir': str(OUT),
        'global_prompt': GLOBAL,
        'scenes': {}
    }
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text())
            manifest.setdefault('scenes', {})
        except Exception:
            pass
    if not API_KEY:
        manifest['state']='blocked'; manifest['error']='KIE_API_KEY missing'; save(manifest); raise SystemExit('KIE_API_KEY missing')

    # submit missing scenes only, so the script is resumable
    for label, prompt in SCENES.items():
        info = manifest['scenes'].get(label, {})
        if info.get('task_id') or info.get('file'):
            continue
        try:
            task_id, body = create_task(label, prompt)
            manifest['scenes'][label] = {'state':'submitted','task_id':task_id,'prompt':prompt,'request_body':body,'file_name':slug(label)+'.png'}
            print('submitted', label, task_id, flush=True)
        except Exception as e:
            manifest['scenes'][label] = {'state':'submit_failed','prompt':prompt,'error':str(e),'file_name':slug(label)+'.png'}
            print('submit_failed', label, str(e), flush=True)
        save(manifest)
        time.sleep(1.2)

    pending = {label for label, info in manifest['scenes'].items() if info.get('task_id') and info.get('state') not in ('success','failed','error','cancelled') and not info.get('file')}
    for poll in range(180):
        if not pending:
            break
        time.sleep(10)
        for label in list(pending):
            info=manifest['scenes'][label]
            try:
                sr=requests.get(STATUS.format(task_id=info['task_id']), headers=STATUS_HEADERS, timeout=120)
                data=sr.json()
                sd=data.get('data', {})
                state=sd.get('state') or 'unknown'
                info['state']=state
                info['status_snapshot']={'failCode':sd.get('failCode'),'failMsg':sd.get('failMsg')}
                urls=result_urls(sd)
                if state == 'success' and urls:
                    out=OUT/info['file_name']
                    img=requests.get(urls[0], timeout=180)
                    img.raise_for_status()
                    out.write_bytes(img.content)
                    info.update({'result_url':urls[0], 'file':str(out), 'finished_at':datetime.now(timezone.utc).isoformat()})
                    pending.remove(label)
                    print('done', label, out.name, flush=True)
                elif state in ('failed','error','cancelled'):
                    info['finished_at']=datetime.now(timezone.utc).isoformat()
                    pending.remove(label)
                    print('failed', label, info.get('status_snapshot'), flush=True)
            except Exception as e:
                info['last_poll_error']=str(e)
                print('poll_error', label, str(e), flush=True)
            save(manifest)
        done=sum(1 for i in manifest['scenes'].values() if i.get('file'))
        failed=sum(1 for i in manifest['scenes'].values() if i.get('state') in ('failed','error','cancelled','submit_failed'))
        print('poll', poll+1, 'done', done, 'failed', failed, 'pending', len(pending), flush=True)
        if done and done % 8 == 0:
            manifest['contact_sheet']=contact_sheet(manifest['scenes'])
            save(manifest)

    manifest['contact_sheet']=contact_sheet(manifest['scenes'])
    manifest['finished_at']=datetime.now(timezone.utc).isoformat()
    still_pending=[p for p in pending]
    if still_pending:
        manifest['state']='timeout_polling'; manifest['pending']=sorted(still_pending)
    else:
        manifest['state']='finished'
    save(manifest)
    print('contact_sheet', manifest.get('contact_sheet'), flush=True)
    print('done', manifest['state'], flush=True)

if __name__ == '__main__':
    main()
