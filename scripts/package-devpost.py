"""Prepare the Devpost card, gallery and a self-contained upload below 35 MB.

Requires Pillow for the code-drawn brand card. No existing raster image is edited.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/devpost'
OUT.mkdir(parents=True, exist_ok=True)
INK, VIOLET, CORAL = '#2b1845', '#713ce4', '#ff784f'
LIME, GOLD, PAPER, WHITE = '#c7ff74', '#ffdd65', '#f3effa', '#fffdf8'


def font(size, weight=700):
    result = ImageFont.truetype(str(ROOT / 'public/fonts/BricolageGrotesque.ttf'), size)
    result.set_variation_by_axes([
        weight if b'Weight' in axis['name'] else axis['default']
        for axis in result.get_variation_axes()
    ])
    return result


def receipt(draw, x, y, scale=1, paper=VIOLET):
    def box(values):
        a, b, c, d = values
        return (x+a*scale, y+b*scale, x+c*scale, y+d*scale)
    def points(values):
        return [(x+a*scale, y+b*scale) for a, b in values]
    draw.pieslice(box((35,20,93,78)), 180, 360, fill=CORAL)
    for line in [[(64,8),(64,15)],[(26,19),(32,25)],[(102,19),(96,25)]]:
        draw.line(points(line), fill=INK if paper == VIOLET else LIME, width=max(1, round(5*scale)))
    draw.polygon(points([(28,55),(100,55),(100,114),(88,106),(76,114),(64,106),(52,114),(40,106),(28,114)]), fill=paper)
    for line in [[(42,71),(64,71)],[(42,85),(53,85)],[(73,84),(81,92),(94,73)]]:
        draw.line(points(line), fill=WHITE if paper == VIOLET else VIOLET, width=max(1, round(6*scale)), joint='curve')


# New code-native artwork using the project's existing Sun Receipt geometry.
card = Image.new('RGB', (1200,800), PAPER)
d = ImageDraw.Draw(card)
d.rounded_rectangle((24,24,1176,776), radius=28, fill=WHITE, outline=INK, width=3)
receipt(d, 50, 38, .86)
d.text((159,66), 'afterlight', font=font(70,760), fill=INK)
dot_x = d.textbbox((159,66), 'afterlight', font=font(70,760))[2] + 12
d.ellipse((dot_x-5,118,dot_x+5,128), fill=CORAL)
d.rounded_rectangle((881,71,1127,120), radius=24, fill=LIME, outline=INK, width=2)
d.text((1004,95), 'THE SUN RECEIPT', font=font(18), fill=INK, anchor='mm')
d.line((70,178,1130,178), fill=INK, width=2)
d.text((75,220), 'WEATHER  ×  AI  ×  BLOCKCHAIN', font=font(18), fill=VIOLET)
d.text((70,281), 'The sun', font=font(96,780), fill=INK)
d.rectangle((76,462,640,480), fill='#ffc2d7')
d.text((70,383), 'has receipts.', font=font(96,780), fill=VIOLET)
d.text((76,521), 'Solar claims with an alibi.', font=font(29,550), fill=INK)
d.rounded_rectangle((76,587,382,630), radius=8, fill=LIME, outline=INK, width=2)
d.text((217,607), 'OPEN TO CHALLENGE', font=font(16), fill=INK, anchor='mm')
d.line([(344,613),(357,600),(347,600)], fill=INK, width=2)
d.line([(357,600),(357,610)], fill=INK, width=2)
d.rounded_rectangle((736,222,1128,632), radius=24, fill=INK)
d.ellipse((784,251,1080,547), fill=VIOLET)
receipt(d, 803, 270, 2.03, LIME)
d.text((933,548), '72 kWh after sunset?', font=font(24), fill=WHITE, anchor='mm')
d.rounded_rectangle((817,577,1048,614), radius=7, fill=CORAL)
d.text((932,595), 'NO SOLAR ALIBI', font=font(18,800), fill=INK, anchor='mm')
d.rectangle((25,681,1174,749), fill=GOLD)
d.text((75,706), 'SCREEN THE CLAIM.  ANCHOR THE EVIDENCE.', font=font(23,750), fill=INK)
d.text((76,754), 'IEEE CLIMATECHAIN  /  RENEWABLE ENERGY & ENERGY TRADING', font=font(12), fill=INK)
thumbnail = OUT / 'afterlight-devpost-thumbnail.png'
card.save(thumbnail, optimize=True)

gallery = OUT / 'gallery'
gallery.mkdir(exist_ok=True)
gallery_sources = [
    ('01-live-overview.png', 'artifacts/afterlight-live-preview.png'),
    ('02-phantom-night.png', 'artifacts/screenshots/02-phantom-night.png'),
    ('03-inflated-peak.png', 'artifacts/screenshots/03-inflated-peak.png'),
    ('04-certificate.png', 'artifacts/screenshots/07-certificate.png'),
    ('05-duplicate-blocked.png', 'artifacts/screenshots/08-duplicate-blocked.png'),
    ('06-tamper-detected.png', 'artifacts/screenshots/09-tamper-detected.png'),
    ('07-model-and-source.png', 'artifacts/screenshots/12-model.png'),
]
for name, source in gallery_sources:
    shutil.copy2(ROOT/source, gallery/name)

fields = {
    'projectName': 'Afterlight',
    'elevatorPitch': 'The sun has receipts. AI checks solar claims against weather; smart contracts block duplicate asset-hours. Portable evidence makes each claim open to inspection.',
    'about': (ROOT/'docs/DEVPOST-ABOUT.md').read_text(),
    'builtWith': ['JavaScript','Node.js','Solidity','Ethereum','ethers.js','Ganache','solc','HTML','CSS','SVG','Python','PVGIS','Machine Learning','Ridge Regression','Conformal Prediction','Merkle Trees','Deepgram','Render','GitHub Actions'],
    'tryItOut': ['https://afterlight-3ch7.onrender.com/','https://github.com/Sanchay117/Afterlight'],
    'video': 'https://youtu.be/JrWJmzfMmjQ',
    'thumbnail': str(thumbnail.relative_to(ROOT)),
    'gallery': [str((gallery/name).relative_to(ROOT)) for name, _ in gallery_sources],
    'additionalInfoFile': 'artifacts/Afterlight-IEEE-Submission.zip',
    'submissionStatus': 'Prepared for the owner to submit; no Devpost submission receipt.',
}
assert len(fields['projectName']) <= 60 and len(fields['elevatorPitch']) <= 200
assert len(fields['builtWith']) <= 25
for image_file in [thumbnail, *gallery.glob('*.png')]:
    assert image_file.stat().st_size < 5_000_000, image_file
    with Image.open(image_file) as image:
        image.verify()
(OUT/'fields.json').write_text(json.dumps(fields, indent=2, ensure_ascii=False)+'\n')

paths = {ROOT/name for name in ['README.md','LICENSE','package.json','package-lock.json','server.mjs','render.yaml','.gitignore']}
for directory in ['lib','contracts','public','data','test','scripts','docs','.github']:
    paths.update(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.update(p for p in OUT.rglob('*') if p.is_file() and p.name != 'package-verification.json')
for name in ['afterlight-demo.mp4','afterlight-demo.srt','verification.json','clean-evidence.json','narration-provenance.json','music-provenance.json','audio-verification.json','motion-verification.json','demo-timing.json']:
    paths.add(ROOT/'artifacts'/name)
for name in ['afterlight-logo-primary.svg','afterlight-logo-primary.png','afterlight-icon-primary.svg','brand-spec.json']:
    paths.add(ROOT/'artifacts/brand'/name)
paths.add(ROOT/'artifacts/thumbnail/afterlight-youtube.jpg')
paths = sorted(paths)
for p in paths:
    assert p.is_file() and not p.is_symlink(), p
    assert not any(part in {'.git','.data','.sessions','.tooling','node_modules'} or part.startswith('.env') for part in p.relative_to(ROOT).parts), p

source_commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
guide = f'''# AFTERLIGHT — IEEE ClimateChain submission

Live app: https://afterlight-3ch7.onrender.com/
Video: https://youtu.be/JrWJmzfMmjQ
Public source: https://github.com/Sanchay117/Afterlight
Track: Renewable Energy & Energy Trading — renewable certificate tracking.

## Try the demonstration
Open the live app and choose "Try to break it". Each visitor gets a separate temporary chain. Sessions expire after 20 idle minutes or service restart. If the free service is waking, allow about a minute.

## Run the source
Use Node.js 22 or newer in this folder:

    npm ci
    npm run build
    npm test
    npm start

Open http://127.0.0.1:4173. This local mode persists its chain in .data. No runtime API key or external wallet is required. See docs/DEPLOY.md for hosted mode.

## Included evidence and media
- artifacts/verification.json records the tested live origin and complete certificate workflow.
- artifacts/clean-evidence.json contains the exportable evidence packet.
- artifacts/afterlight-demo.mp4 is the 4:34 narrated film with original graphics and music.
- artifacts/devpost/ contains the 3:2 card, gallery and exact form fields.
- docs/DEVPOST-ABOUT.md is the seven-section project story.
- data/ contains the public PVGIS snapshot, model and provenance.
- contracts/ contains the Solidity source and matching compiled artifact.

PVGIS output is modeled; attack cases are controlled demonstrations. These are local-EVM demo certificates, not accredited renewable certificates. No avoided CO2 or real-meter fraud accuracy is claimed. The hosted blockchain has a temporary session lifetime.

The archive excludes API keys, installed dependencies, local ledger state and Git history. Source base commit: {source_commit}; this packet also includes the prepared submission text/assets. MANIFEST.sha256 records the exact included files.

The owner still completes the final Devpost submission. This packet is not a submission receipt.
'''
payload = {f'Afterlight/{p.relative_to(ROOT).as_posix()}': p.read_bytes() for p in paths}
payload['Afterlight/START-HERE.md'] = guide.encode()
manifest = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name.removeprefix("Afterlight/")}\n' for name,data in sorted(payload.items()))
archive = ROOT/'artifacts/Afterlight-IEEE-Submission.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
    for name, data in sorted(payload.items()):
        zipped.writestr(name,data)
    zipped.writestr('Afterlight/MANIFEST.sha256',manifest)
assert archive.stat().st_size < 35_000_000, 'Devpost upload exceeds 35 MB'
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    assert len(zipped.namelist()) == len(set(zipped.namelist()))
    for name,data in payload.items():
        assert hashlib.sha256(zipped.read(name)).digest() == hashlib.sha256(data).digest()

verification = {
    'archive': str(archive.relative_to(ROOT)),
    'bytes': archive.stat().st_size,
    'limitBytes': 35_000_000,
    'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'entries': len(payload)+1,
    'crcAndManifestVerified': True,
    'pitchCharacters': len(fields['elevatorPitch']),
    'tagCount': len(fields['builtWith']),
    'thumbnailDimensions': [1200,800],
    'thumbnailBytes': thumbnail.stat().st_size,
    'galleryImages': len(gallery_sources),
    'excluded': ['API keys','node_modules','local chain state','Git history'],
    'submissionStatus': fields['submissionStatus'],
}
(OUT/'package-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(verification,indent=2))
