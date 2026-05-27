import json
import os
import pathlib
import time
from datetime import datetime, timezone

import requests
from PIL import Image, ImageOps, ImageDraw

ROOT = pathlib.Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_REPOS/mp-holzbau-hero-preview')
REFDIR = pathlib.Path('/Users/theo/Library/Group Containers/UBF8T346G9.OneDriveSyncClientSuite/OneDrive - Convernatics.noindex/OneDrive - Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau/assets/real-images/humans/peter-preissinger')
OUT = ROOT / 'assets' / 'mp-peter-likeness-retry-2026-05-27-kie'
OUT.mkdir(parents=True, exist_ok=True)

REAL_REFS = [
    REFDIR / 'peter-preissinger-4.jpeg',
    REFDIR / 'peter-preissinger-1.jpeg',
    REFDIR / 'peter-preissinger-3.jpeg',
]

SCENES = [
    {
        'name': 'peter_real_likeness_hero_close_carport',
        'aspect_ratio': '16:9',
        'prompt': '''
Create a photorealistic website hero image for M&P Holzbau.

IDENTITY IS THE MAIN TASK: Use the supplied real photos as the exact identity anchor for Peter Preissinger. He must clearly look like the same real Austrian carpenter in the references: late 50s/early 60s, grey tousled hair, salt-and-pepper beard, broad natural face, slightly heavy eyelids, gentle tired-friendly eyes, normal real skin texture, not beautified, not younger, not generic model, not a different man.

Scene: Peter stands prominently in the foreground beside a finished oak/timber carport at a detached Austrian house. He wears believable burgundy/dark-red M&P-style workwear over normal work trousers. He is relaxed and approachable, slight real smile, not a stock-photo grin. One hand casually rests near a timber post or beam; the carport roof and craftsmanship remain clearly visible behind him.

Composition: 16:9 horizontal. Peter should be large enough that his face is readable and recognizably the reference person. Text-safe negative space on the left. Warm overcast natural daylight. Documentary craft photography, realistic lens, no CGI gloss.

Hard negatives: no team group, no fake young man, no black-only workwear, no readable gibberish logo, no extra fingers, no duplicated body, no cars in the carport bay, no metal bracket focus.
'''
    },
    {
        'name': 'peter_real_likeness_quality_portrait_generated',
        'aspect_ratio': '1:1',
        'prompt': '''
Create a square photorealistic landing-page profile image of Peter Preissinger at a timber carport workshop/jobsite.

IDENTITY IS THE MAIN TASK: copy the person identity from the supplied real photos exactly enough that someone who knows him recognizes him immediately. Preserve grey tousled hair, salt-and-pepper beard, broad natural face, slightly heavy eyelids, calm friendly expression, age impression, and real skin texture. Do not make him younger, slimmer, more polished, or like a generic stock craftsman.

Scene: chest-up portrait, Peter in burgundy/dark-red M&P-style workwear, standing in front of warm timber beams / stacked wood / carport construction. Friendly but understated Austrian craftsman expression. Natural daylight, realistic photo, no studio look.

Hard negatives: no black jacket, no generic model face, no exaggerated smile, no fake/gibberish large logo, no over-smoothed AI skin.
'''
    }
]


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


def upload_catbox(path: pathlib.Path) -> str:
    with path.open('rb') as f:
        r = requests.post(
            'https://catbox.moe/user/api.php',
            data={'reqtype': 'fileupload'},
            files={'fileToUpload': (path.name, f, 'image/jpeg')},
            timeout=120,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith('http'):
        raise RuntimeError(f'catbox upload failed for {path}: {url}')
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


def direct_real_portrait():
    # Use the actual Peter photo Peter-4 for the profile slot; this avoids identity drift entirely.
    src = ImageOps.exif_transpose(Image.open(REFDIR / 'peter-preissinger-4.jpeg')).convert('RGB')
    # crop square around face/upper body, leaving wood background
    w, h = src.size
    side = min(w, h)
    left = max(0, (w - side)//2)
    top = max(0, int(h * 0.05))
    if top + side > h:
        top = h - side
    crop = src.crop((left, top, left + side, top + side))
    crop = crop.resize((1200, 1200), Image.Resampling.LANCZOS)
    # subtle warm/contrast touch only; keep actual photo identity
    out = OUT / 'selected_peter_portrait_REAL_photo_crop.webp'
    crop.save(out, quality=92)
    return str(out)


def contact_sheet(files):
    thumbs=[]
    for label, p in files:
        im=Image.open(p).convert('RGB')
        im.thumbnail((420,300))
        thumbs.append((label, im))
    cols=2; tw, th = 460, 360
    out=Image.new('RGB',(cols*tw, ((len(thumbs)+1)//2)*th), 'white')
    d=ImageDraw.Draw(out)
    for i,(label,im) in enumerate(thumbs):
        x=(i%cols)*tw+20; y=(i//cols)*th+35
        d.text((x,y-25),label,fill=(0,0,0))
        out.paste(im,(x,y))
    sheet=OUT/'_contact_sheet.jpg'
    out.save(sheet, quality=92)
    return str(sheet)


def main():
    key = api_key()
    real_crop = direct_real_portrait()
    ref_urls = [upload_catbox(p) for p in REAL_REFS]
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'refs': [str(p) for p in REAL_REFS], 'ref_urls': ref_urls, 'outputs': [{'name': 'selected_peter_portrait_REAL_photo_crop', 'file': real_crop, 'method': 'direct crop of real photo'}]}
    files=[('REAL profile crop', pathlib.Path(real_crop))]
    for scene in SCENES:
        try:
            task_id = submit(scene, ref_urls, key)
            manifest['outputs'].append({'name': scene['name'], 'task_id': task_id, 'state': 'submitted'})
            state, url, raw = poll(task_id, key)
            item = manifest['outputs'][-1]
            item.update({'state': state, 'result_url': url, 'raw_state': raw})
            if url:
                img = requests.get(url, timeout=180).content
                out = OUT / f"{scene['name']}.png"
                out.write_bytes(img)
                item['file'] = str(out)
                files.append((scene['name'], out))
        except Exception as e:
            manifest['outputs'].append({'name': scene['name'], 'error': repr(e)})
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    sheet = contact_sheet(files)
    manifest['contact_sheet'] = sheet
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'out': str(OUT), 'contact_sheet': sheet, 'outputs': manifest['outputs']}, indent=2))

if __name__ == '__main__':
    main()
