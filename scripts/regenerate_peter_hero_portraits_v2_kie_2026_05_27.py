import json
import os
import pathlib
import time
from datetime import datetime, timezone

import requests
from PIL import Image, ImageDraw

ROOT = pathlib.Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_REPOS/mp-holzbau-hero-preview')
REFDIR = pathlib.Path('/Users/theo/Library/Group Containers/UBF8T346G9.OneDriveSyncClientSuite/OneDrive - Convernatics.noindex/OneDrive - Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau/assets/real-images/humans/peter-preissinger')
OUT = ROOT / 'assets' / 'mp-peter-hero-portraits-v2-2026-05-27-kie'
OUT.mkdir(parents=True, exist_ok=True)

CURRENT_HERO = ROOT / 'assets/mp-peter-likeness-retry-2026-05-27-kie/peter_real_likeness_hero_close_carport.png'
REAL_REFS = [
    REFDIR / 'peter-preissinger-4.jpeg',
    REFDIR / 'peter-preissinger-1.jpeg',
    REFDIR / 'peter-preissinger-3.jpeg',
]
WORKWEAR_REFS = [
    ROOT / 'assets/mp-workwear-corrections-2026-05-26-kie/02_peter_red_hoodie_post_level.webp',
    ROOT / 'assets/mp-workwear-corrections-2026-05-26-kie/03_peter_red_hoodie_roofline.webp',
]
LOGO = ROOT / 'assets/logo-white.png'

BASE_IDENTITY = '''
Peter Preissinger identity: use the supplied real photos as strict identity anchors. Austrian Zimmermeister, late 50s to early 60s, grey tousled hair, salt-and-pepper beard/stubble, broad natural face, slightly heavy eyelids, calm friendly eyes, real age impression. Keep realistic skin texture with pores, subtle wrinkles, beard texture, small natural imperfections. Do NOT smooth the skin, do NOT make him younger, slimmer, glossy, waxy or like a generic stock model.
'''

HERO_PROMPT = f'''
This is a targeted correction pass for the supplied existing website hero image. Preserve the same broad composition, same finished timber/oak carport, same Austrian family-house context, same hero framing with calm text-safe space on the left, and Peter standing at the right side.

{BASE_IDENTITY}

Critical corrections:
1. Change the ground under and around the carport from gravel/schotter/dirt to a clean finished paved surface: neat grey concrete paving stones or large-format driveway pavers, believable joints, fully installed, suitable for a finished carport at a home. No loose gravel, no muddy dirt, no unfinished construction ground.
2. Correct the workwear: Peter must wear authentic M&P Holzbau work clothing — rich burgundy / dark red work jacket or work hoodie, dark work trousers, practical carpenter workwear, subtle small white M&P chest logo only. Use the supplied workwear references and logo as style anchors. Avoid black-only clothing, purple/mauve jacket, generic fashion jacket, fake big text, misspelled logos, or random brand marks.
3. Skin and face realism: keep natural skin texture, pores, wrinkles, beard texture, normal outdoor-light face detail. No plastic smoothing, no beauty retouching, no AI wax skin.

Keep the timber carport physically plausible: premium oak/timber look, clean roof edge, visible Nuten/Auflager style timber details, no visible Blechwinkel/sheet-metal bracket hero focus, no vehicles in the bay. Professional documentary landing-page photography, realistic lens and daylight.
'''

PORTRAIT_PROMPTS = [
    ('01_professional_photographer_workshop_portrait', f'''
Generate a NEW attractive professional portrait photograph of Peter Preissinger for a premium M&P Holzbau landing page. Do not reuse the existing photo crop; create a fresh portrait that looks shot by a professional photographer.

{BASE_IDENTITY}

Scene: chest-up / upper-body portrait in a warm timber workshop or beside beautiful oak beams. Peter wears authentic burgundy/dark-red M&P workwear with dark work trousers or jacket details and one subtle small white M&P chest logo. Expression: approachable, confident, friendly but not cheesy. Lighting: professional photographer look, soft natural key light, gentle background separation, realistic depth of field, premium editorial craft-business portrait. Skin must stay real: pores, wrinkles, beard texture, no over-smoothing.

Hard negatives: no old photo crop, no studio passport photo, no black jacket, no fake giant logo, no gibberish text, no plastic skin, no younger generic model, no exaggerated grin.
'''),
    ('02_professional_photographer_carport_portrait', f'''
Generate a NEW attractive professional portrait photograph of Peter Preissinger for a premium M&P Holzbau landing page. It should feel commissioned by a professional photographer, not a casual snapshot and not an AI avatar.

{BASE_IDENTITY}

Scene: Peter stands beside a finished paved timber carport, with warm oak beams softly blurred behind him. Chest-up portrait, face clearly in focus. Authentic burgundy/dark-red M&P work jacket/hoodie, dark practical workwear, subtle small white M&P chest logo only. Expression: calm, competent, slight warm smile, trustworthy Zimmermeister. Use professional natural-light portrait photography, 85mm lens feel, tasteful contrast, realistic skin texture with pores and wrinkles.

Hard negatives: no reused existing photo, no overly smooth skin, no black-only workwear, no fake text, no stock-model face, no construction dirt, no gravel foreground.
'''),
    ('03_professional_photographer_authority_portrait', f'''
Generate a NEW attractive square business portrait of Peter Preissinger for a landing-page contact card.

{BASE_IDENTITY}

Scene: clean professional environmental portrait at a timber carport jobsite after completion. Finished paved driveway under the carport, timber beams in background, Peter centered chest-up. Clothing: authentic M&P burgundy/dark-red workwear, subtle small white M&P logo, dark work trousers/jacket accents. Expression: confident, experienced, friendly, personally approachable. Professional photographer quality: soft daylight, realistic color grading, natural face detail, believable eyes, beard texture, no beauty filter.

Hard negatives: no passport-photo crop, no reused real image, no fake plastic face, no younger man, no generic craftsman, no large unreadable logo.
'''),
    ('04_professional_photographer_warm_portrait', f'''
Create a NEW attractive professional portrait photo of Peter Preissinger for the section "Ihr persönlicher Ansprechpartner" / landing-page advisor card.

{BASE_IDENTITY}

Scene: relaxed professional portrait in front of stacked timber / oak beams and a clean workshop-carport background. Upper body, shoulders visible, face sharp and naturally lit. Clothing: M&P burgundy/dark-red work jacket or hoodie, dark practical accents, subtle small white M&P logo on chest. Expression: warm, honest, slightly smiling, not staged. Professional photographer result: premium editorial look, natural skin texture, pores and wrinkles preserved, no AI smoothing, no glamour retouch.

Hard negatives: no existing photo crop, no black jacket, no fake text, no waxy smooth skin, no generic stock photo, no distorted hands.
'''),
]

SCENES = [{'name': 'hero_v2_paved_workwear_skin', 'aspect_ratio': '16:9', 'prompt': HERO_PROMPT, 'refs': [CURRENT_HERO] + WORKWEAR_REFS + [LOGO] + REAL_REFS}]
SCENES += [{'name': name, 'aspect_ratio': '1:1', 'prompt': prompt, 'refs': REAL_REFS + WORKWEAR_REFS + [LOGO]} for name, prompt in PORTRAIT_PROMPTS]


def api_key() -> str:
    key = os.environ.get('KIE_API_KEY', '').strip()
    if key:
        return key
    for env in [pathlib.Path('/Users/theo/.hermes/.env'), pathlib.Path('/Users/theo/.env')]:
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith('KIE_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('KIE_API_KEY missing')


def mime(path: pathlib.Path) -> str:
    s = path.suffix.lower()
    if s == '.png': return 'image/png'
    if s == '.webp': return 'image/webp'
    return 'image/jpeg'


def upload_catbox(path: pathlib.Path, cache: dict) -> str:
    k = str(path)
    if k in cache:
        return cache[k]
    with path.open('rb') as f:
        r = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': (path.name, f, mime(path))}, timeout=120)
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith('http'):
        raise RuntimeError(f'catbox upload failed for {path}: {url}')
    cache[k] = url
    return url


def submit(scene, ref_urls, key):
    body = {
        'model': 'nano-banana-2',
        'input': {
            'prompt': scene['prompt'].strip(),
            'image_input': ref_urls,
            'aspect_ratio': scene['aspect_ratio'],
            'resolution': '2K',
            'output_format': 'png',
        }
    }
    r = requests.post('https://api.kie.ai/api/v1/jobs/createTask', headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, json=body, timeout=120)
    r.raise_for_status()
    data = r.json()
    if data.get('code') not in (200, '200'):
        raise RuntimeError(data)
    return data['data']['taskId']


def poll(task_id, key):
    while True:
        r = requests.get('https://api.kie.ai/api/v1/jobs/recordInfo', headers={'Authorization': f'Bearer {key}'}, params={'taskId': task_id}, timeout=120)
        r.raise_for_status()
        data = r.json()['data']
        state = data.get('state')
        if state == 'success':
            result = json.loads(data.get('resultJson') or '{}')
            return state, result.get('resultUrls', [None])[0], data
        if state in ('failed', 'fail'):
            return state, None, data
        time.sleep(20)


def make_contact(files):
    thumbs = []
    for label, path in files:
        im = Image.open(path).convert('RGB')
        im.thumbnail((430, 300))
        thumbs.append((label, im))
    cols = 2
    tw, th = 470, 360
    sheet = Image.new('RGB', (cols * tw, ((len(thumbs) + cols - 1) // cols) * th), 'white')
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(thumbs):
        x = (i % cols) * tw + 20
        y = (i // cols) * th + 38
        d.text((x, y - 25), label, fill=(0, 0, 0))
        sheet.paste(im, (x, y))
    out = OUT / '_contact_sheet.jpg'
    sheet.save(out, quality=92)
    return out


def main():
    key = api_key()
    upload_cache = {}
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'model': 'nano-banana-2', 'outputs': []}
    files = []
    for scene in SCENES:
        print('uploading refs', scene['name'], flush=True)
        ref_urls = [upload_catbox(p, upload_cache) for p in scene['refs']]
        item = {'name': scene['name'], 'refs': [str(p) for p in scene['refs']], 'ref_urls': ref_urls, 'prompt': scene['prompt']}
        try:
            task_id = submit(scene, ref_urls, key)
            item['task_id'] = task_id
            item['state'] = 'submitted'
            manifest['outputs'].append(item)
            (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            print('submitted', scene['name'], task_id, flush=True)
            state, url, raw = poll(task_id, key)
            item.update({'state': state, 'result_url': url, 'raw_state': raw})
            if url:
                data = requests.get(url, timeout=180).content
                out = OUT / f"{scene['name']}.png"
                out.write_bytes(data)
                item['file'] = str(out)
                files.append((scene['name'], out))
        except Exception as e:
            item['error'] = repr(e)
            if item not in manifest['outputs']:
                manifest['outputs'].append(item)
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    sheet = make_contact(files)
    manifest['contact_sheet'] = str(sheet)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'out': str(OUT), 'contact_sheet': str(sheet), 'files': [str(p) for _, p in files]}, indent=2))

if __name__ == '__main__':
    main()
