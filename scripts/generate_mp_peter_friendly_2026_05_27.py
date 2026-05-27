import base64
import json
import pathlib
import textwrap
import time
from datetime import datetime, timezone

import requests

ROOT = pathlib.Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_REPOS/mp-holzbau-hero-preview')
OUT = ROOT / 'assets' / 'mp-peter-friendly-2026-05-27-gemini'
OUT.mkdir(parents=True, exist_ok=True)

refs = [
    ROOT / 'assets' / 'peter-preissinger-portrait.webp',
    ROOT / 'assets' / 'peter-action-2026-05-26' / '13_peter_tall_carport_roofline.webp',
    ROOT / 'assets' / 'peter-action-2026-05-26' / '12_peter_tall_carport_level.webp',
]

prompts = [
    ('01_peter_friendly_explaining_carport', '''
Create a photorealistic business-use website image of the SAME person from the references: Peter Preissinger, Austrian carpenter master in his late 50s to early 60s, short grey hair, salt-and-pepper beard, warm approachable expression.

This is for a landing-page section about thoughtful planning by a Zimmermeister. He must look natural, competent and friendly — NOT stern, blank, uncanny or overly posed.

Scene:
Peter stands next to a high-quality finished wooden carport at a real detached house. He is explaining one detail of the timber structure with one open hand while the other hand lightly touches or indicates a post or beam. Slight natural smile, relaxed face, open body language, believable eye direction toward the structure or slightly toward camera. No paper plans in hand. Focus on Peter and the timber craftsmanship.

Composition:
Wide 16:9 image. Peter roughly on the right third. Enough visible carport structure around him. Clean residential background. Natural overcast daylight. Authentic documentary photography. Realistic skin texture. Realistic hands. Exactly one body, two arms, two hands. Keep the red or burgundy M&P workwear look. Preserve exact identity from the references.
'''),
    ('02_peter_friendly_quality_check', '''
Create a photorealistic business-use website image of the SAME person from the references: Peter Preissinger, Austrian carpenter master in his late 50s to early 60s, short grey hair, salt-and-pepper beard, warm approachable expression.

This is a correction/regeneration for a website section. He must look natural, human, friendly and trustworthy — not stiff, grim or uncanny.

Scene:
Peter is doing a quality check at a finished wooden carport, one hand at a timber post, the other in a relaxed explanatory gesture. He is slightly smiling as if speaking to a homeowner. Show the timber construction clearly. No harsh posing, no exaggerated grin, no blueprint sheet.

Composition:
Wide 16:9 medium shot. Peter prominent but not oversized. More craftsmanship than empty pavement. Elegant timber beams visible. Clean house background. Natural colors. Realistic proportions. Realistic hands. Flattering angle. Avoid making him look unfriendly.
''')
]

MODEL = 'gemini-2.5-flash-image'


def main() -> None:
    import os

    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not key:
        for env_path in [pathlib.Path('/Users/theo/.hermes/.env'), pathlib.Path('/Users/theo/.env')]:
            if env_path.exists():
                for line in env_path.read_text(encoding='utf-8').splitlines():
                    if line.strip().startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
            if key:
                break
    if not key:
        raise SystemExit('GEMINI_API_KEY missing')

    url = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODEL + ':generateContent?key=' + key
    manifest = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'model': MODEL,
        'outputs': [],
    }

    for name, prompt in prompts:
        parts = [{'text': textwrap.dedent(prompt).strip()}]
        for ref in refs:
            parts.append({
                'inline_data': {
                    'mime_type': 'image/webp',
                    'data': base64.b64encode(ref.read_bytes()).decode('ascii'),
                }
            })

        body = {
            'contents': [{'parts': parts}],
            'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']},
        }
        r = requests.post(url, json=body, timeout=300)
        info = {'name': name, 'http_status': r.status_code}
        r.raise_for_status()
        resp = r.json()
        img_bytes = None
        texts = []
        for cand in resp.get('candidates', []):
            for part in cand.get('content', {}).get('parts', []):
                if 'text' in part:
                    texts.append(part['text'])
                img_obj = part.get('inlineData') or part.get('inline_data')
                if img_obj and img_obj.get('data'):
                    img_bytes = base64.b64decode(img_obj['data'])
                    break
            if img_bytes:
                break

        if not img_bytes:
            info['error'] = resp.get('promptFeedback', {})
            info['text'] = '\n'.join(texts)[:500]
            manifest['outputs'].append(info)
            continue

        out_path = OUT / f'{name}.png'
        out_path.write_bytes(img_bytes)
        info['file'] = str(out_path)
        info['text'] = '\n'.join(texts)[:500]
        manifest['outputs'].append(info)
        time.sleep(1)

    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
