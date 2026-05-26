import os, json, time, re
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = Path('/Users/theo/Library/CloudStorage/OneDrive-Convernatics/_AGENT_SHARE_HUB/_CUSTOMER_SYSTEMS/M&P Holzbau')
AVATAR_DIR = CUSTOMER / 'assets/generated-images/mp-holzbau-avatar-bases-v2-hoodies-2026-04-20'
LOGO = CUSTOMER / 'assets/logo/logo.png'
OUT = ROOT / 'assets' / 'mp-avatar-scenes-2026-05-26-kie'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / 'manifest.json'

for env_path in [Path('/Users/theo/.hermes/.env'), Path('/Users/theo/.env')]:
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API_KEY = os.environ.get('KIE_API_KEY')
CREATE = 'https://api.kie.ai/api/v1/jobs/createTask'
STATUS = 'https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}'
UPLOAD = 'https://kieai.redpandaai.co/api/file-stream-upload'
HEADERS = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'} if API_KEY else {}
STATUS_HEADERS = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else {}
UPLOAD_HEADERS = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else {}
MODEL = 'nano-banana-2'

GLOBAL = """
Photorealistic documentary scene for M&P Holzbau, an Austrian carpentry / Zimmermeisterbetrieb.
Use ONLY the supplied M&P avatar reference images as the workers in the scene. Preserve their faces, hair, age, build, and red/burgundy M&P hoodies/work jackets with dark work trousers. Do not invent random workers, do not add extra people, do not change the crew into generic models. Small M&P logo on chest is okay, no large fake text.

Scene style: real Austrian construction photography, natural lens, 16:9 horizontal, useful landing-page image, practical jobsite/workshop detail, quiet professional mood. Workers are focused on the task, not smiling at camera.

Physical logic is critical: only real carpentry or carport installation work. No fake working poses, no meaningless pointing, no fantasy brackets, no Blechwinkel hero shots, no terrace/deck/pergola confusion, no impossible post bases, no leaning beams, no AI showroom look, no generic stock photo, no CGI, no watermark, no readable third-party branding.
""".strip()

SCENES = [
    ('01_montage_balken_ausrichten_level', ['Michael','Markus'], 'Two supplied M&P avatars at a timber carport montage site align a long main beam under the roof edge. One avatar holds a spirit level against the beam, the other steadies the timber. Real posts, rafters, paved driveway, house facade.'),
    ('02_montage_sparren_einheben', ['Gerhard','Tobias'], 'Two supplied M&P avatars carefully lift and position a roof rafter into a timber carport frame. One stands on a stable work platform, one guides from below. Hands and tool positions must be physically plausible.'),
    ('03_montage_zollstock_anzeichnen', ['Markus','Tobias'], 'Two supplied M&P avatars mark a timber post on site: one holds a folding rule / Zollstock, the other marks a clean pencil line on the wood. Real carport posts and driveway visible.'),
    ('04_montage_pfosten_lot_pruefen', ['Michael','Gerhard'], 'Two supplied M&P avatars check a vertical timber post for plumb using a long spirit level before fastening. Foundation/paved driveway visible, no metal angle close-up.'),
    ('05_montage_dachueberstand_kontrolle', ['Michael'], 'One supplied older M&P avatar in burgundy work jacket inspects the roof overhang and gutter line of a new timber carport, holding a folded plan in one hand and pointing at the exact roof edge.'),
    ('06_montage_unterdach_verschrauben', ['Markus','Gerhard'], 'Two supplied M&P avatars fasten underside timber boards/rafters on a carport roof using a cordless driver in a plausible position. Visible screw alignment, no random drilling into metal.'),
    ('07_montage_wetterseite_schalung', ['Tobias','Michael'], 'Two supplied M&P avatars install vertical timber slats on the weather side of a carport. One holds a board, the other checks spacing with a small spacer block. Austrian residential driveway.'),
    ('08_montage_dachrinne_anpassen', ['Gerhard','Markus'], 'Two supplied M&P avatars fit a gutter/downpipe line to a timber carport roof edge. One measures slope, one holds the gutter. Realistic water drainage logic, no impossible floating pipe.'),
    ('09_montage_werkzeug_detail_balkenverbindung', ['Tobias'], 'Close documentary scene with one supplied M&P avatar working on a real timber beam connection with clamps, pencil marks, and cordless driver. The connection is wood-to-wood, not a fake metal bracket hero.'),
    ('10_montage_abschlusskontrolle_team', ['Michael','Markus','Gerhard'], 'Three supplied M&P avatars do a final walkaround at a nearly finished timber carport, checking alignment, post bases, roof edge, and driveway clearance. Professional focused body language.'),
    ('11_werkstatt_kappsaege_zuschnitt', ['Markus'], 'One supplied M&P avatar in the workshop cuts a carport timber beam on a professional chop saw / Kappsäge. Beam is clamped or properly supported, hands safe, real sawdust/offcuts.'),
    ('12_werkstatt_hobelbank_anzeichnen', ['Tobias'], 'One supplied M&P avatar at a timber workbench marks a beam with pencil and square. Workshop background with stacked timber, clamps, sawdust. Practical preparation for carport montage.'),
    ('13_werkstatt_team_material_sortieren', ['Gerhard','Michael'], 'Two supplied M&P avatars in a timber workshop sort and label prepared beams for a carport montage. Stacked wood, measuring tape, clear practical organization, no readable labels.'),
    ('14_werkstatt_bohrung_vorbereiten', ['Markus','Tobias'], 'Two supplied M&P avatars prepare precise pre-drilled holes in a timber beam on a workshop bench. One holds the beam/clamp, one uses a drill press or guided cordless drill safely.'),
    ('15_werkstatt_oberflaeche_schleifen', ['Gerhard'], 'One supplied M&P avatar sands or finishes the edge of a visible timber beam in the workshop. Close enough to show craftsmanship, but still a real documentary scene.'),
    ('16_werkstatt_materialcheck_plan', ['Michael','Gerhard'], 'Two supplied M&P avatars compare a printed plan with prepared timber parts in the workshop before loading for montage. Plans visible but no readable text.'),
    ('17_abladen_lkw_balken', ['Markus','Tobias'], 'Two supplied M&P avatars unload long timber beams from a flatbed or trailer at an Austrian residential carport montage site. They carry the timber together with correct posture, driveway and house visible.'),
    ('18_abladen_stapler_palette', ['Gerhard','Markus'], 'Two supplied M&P avatars receive a pallet of timber materials near the driveway; one guides the load, one checks the delivery list/plan. Forklift or pallet jack is plausible and safe, no third-party branding.'),
    ('19_abladen_material_aufboecken', ['Michael','Tobias'], 'Two supplied M&P avatars place unloaded timber beams onto trestles / Böcke beside the future carport area. Practical staging before montage, straps and spacers visible.'),
    ('20_abladen_team_transport_zur_baustelle', ['Michael','Markus','Gerhard'], 'Three supplied M&P avatars carry and stage smaller timber parts from a trailer toward the carport construction area. Real driveway, residential setting, focused movement, no invented extra crew.'),
]

def avatar_path(name: str) -> Path:
    return AVATAR_DIR / f'{name}.png'

def upload(path: Path) -> str:
    mime = 'image/png' if path.suffix.lower() == '.png' else 'image/webp' if path.suffix.lower() == '.webp' else 'image/jpeg'
    with path.open('rb') as fh:
        r = requests.post(UPLOAD, headers=UPLOAD_HEADERS, data={'uploadPath': 'images'}, files={'file': (path.name, fh, mime)}, timeout=180)
    r.raise_for_status()
    data = r.json()
    if not data.get('success'):
        raise RuntimeError(f'upload failed {path}: {data}')
    return data['data']['downloadUrl']

def slug(s):
    return re.sub(r'[^a-z0-9_\-]+', '-', s.lower()).strip('-')

def save(m):
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')

def submit(label, prompt, refs):
    full_prompt = GLOBAL + '\n\nScene: ' + prompt + '\n\nIdentity rule for this scene: the visible workers must match the supplied avatar reference images attached to this task. Use the same faces and M&P red/burgundy workwear; do not invent different people.'
    body = {
        'model': MODEL,
        'input': {
            'prompt': full_prompt,
            'image_input': refs,
            'aspect_ratio': '16:9',
            'resolution': '1K',
            'output_format': 'png',
        },
    }
    r = requests.post(CREATE, headers=HEADERS, json=body, timeout=180)
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f'non-json {r.status_code}: {r.text[:500]}')
    if data.get('code') != 200:
        raise RuntimeError(f'{label} submit failed: {data}')
    return data['data']['taskId'], body

def urls_from(sd):
    raw = sd.get('resultJson') or ''
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    return parsed.get('resultUrls') or parsed.get('result_urls') or []

def make_contact(scenes):
    items = []
    for label, info in scenes.items():
        f = info.get('file')
        if f and Path(f).exists():
            items.append((label, Path(f)))
    if not items:
        return None
    W, H = 390, 290
    cols = 4
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * W, rows * H + 62), (232, 226, 215))
    d = ImageDraw.Draw(sheet)
    d.text((16, 22), f'M&P avatar scenes — montage / werkstatt / abladen — {len(items)} images', fill=(20, 20, 20))
    for i, (label, path) in enumerate(items):
        im = Image.open(path).convert('RGB')
        im.thumbnail((W, 220))
        tile = Image.new('RGB', (W, H), 'white')
        tile.paste(im, ((W - im.width) // 2, 8))
        td = ImageDraw.Draw(tile)
        td.rectangle([0, 228, W, H], fill=(245, 239, 228))
        td.text((8, 238), label[:50], fill=(20, 20, 20))
        sheet.paste(tile, ((i % cols) * W, 62 + (i // cols) * H))
    out = OUT / '_contact_sheet.jpg'
    sheet.save(out, quality=92)
    return str(out)

def main():
    if not API_KEY:
        raise SystemExit('KIE_API_KEY missing')
    manifest = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'batch': 'mp-avatar-scenes-2026-05-26-kie',
        'model': MODEL,
        'state': 'init',
        'output_dir': str(OUT),
        'global_prompt': GLOBAL,
        'scenes': {},
        'avatar_dir': str(AVATAR_DIR),
    }
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
            manifest.setdefault('scenes', {})
        except Exception:
            pass

    manifest.setdefault('uploaded_refs', {})
    needed = {LOGO}
    for _, names, _ in SCENES:
        needed.update(avatar_path(n) for n in names)
    for p in sorted(needed, key=lambda x: x.name):
        if not p.exists():
            raise FileNotFoundError(str(p))
        key = str(p)
        if key not in manifest['uploaded_refs']:
            manifest['uploaded_refs'][key] = upload(p)
            print('uploaded', p.name, flush=True)
            save(manifest)
            time.sleep(0.4)

    for label, names, prompt in SCENES:
        info = manifest['scenes'].get(label, {})
        if info.get('task_id') or info.get('file'):
            continue
        refs = [manifest['uploaded_refs'][str(avatar_path(n))] for n in names] + [manifest['uploaded_refs'][str(LOGO)]]
        try:
            task_id, body = submit(label, prompt, refs)
            manifest['scenes'][label] = {
                'state': 'submitted',
                'task_id': task_id,
                'avatar_names': names,
                'prompt': prompt,
                'request_body': body,
                'file_name': slug(label) + '.png',
            }
            print('submitted', label, task_id, flush=True)
        except Exception as e:
            manifest['scenes'][label] = {
                'state': 'submit_failed',
                'avatar_names': names,
                'prompt': prompt,
                'error': str(e),
                'file_name': slug(label) + '.png',
            }
            print('submit_failed', label, e, flush=True)
        save(manifest)
        time.sleep(1.2)

    pending = {label for label, info in manifest['scenes'].items() if info.get('task_id') and not info.get('file') and info.get('state') not in ('success', 'failed', 'fail', 'error', 'cancelled')}
    for poll in range(180):
        if not pending:
            break
        time.sleep(10)
        for label in list(pending):
            info = manifest['scenes'][label]
            try:
                data = requests.get(STATUS.format(task_id=info['task_id']), headers=STATUS_HEADERS, timeout=180).json()
                sd = data.get('data', {})
                state = sd.get('state') or 'unknown'
                info['state'] = state
                info['status_snapshot'] = {'failCode': sd.get('failCode'), 'failMsg': sd.get('failMsg')}
                urls = urls_from(sd)
                if state == 'success' and urls:
                    raw = requests.get(urls[0], timeout=240)
                    raw.raise_for_status()
                    png = OUT / info['file_name']
                    png.write_bytes(raw.content)
                    webp = png.with_suffix('.webp')
                    Image.open(png).convert('RGB').save(webp, quality=88, method=6)
                    info.update({'result_url': urls[0], 'file': str(webp), 'source_png': str(png), 'finished_at': datetime.now(timezone.utc).isoformat()})
                    pending.remove(label)
                    print('done', label, webp.name, flush=True)
                elif state in ('failed', 'fail', 'error', 'cancelled'):
                    info['finished_at'] = datetime.now(timezone.utc).isoformat()
                    pending.remove(label)
                    print('failed', label, info.get('status_snapshot'), flush=True)
            except Exception as e:
                info['last_poll_error'] = str(e)
                print('poll_error', label, e, flush=True)
            save(manifest)
        done = sum(1 for i in manifest['scenes'].values() if i.get('file'))
        failed = sum(1 for i in manifest['scenes'].values() if i.get('state') in ('failed', 'fail', 'error', 'cancelled', 'submit_failed'))
        print('poll', poll + 1, 'done', done, 'failed', failed, 'pending', len(pending), flush=True)

    manifest['contact_sheet'] = make_contact(manifest['scenes'])
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    manifest['state'] = 'finished' if not pending else 'timeout_polling'
    manifest['pending'] = sorted(pending)
    save(manifest)
    print('contact_sheet', manifest.get('contact_sheet'), flush=True)
    print('done', manifest['state'], flush=True)

if __name__ == '__main__':
    main()
