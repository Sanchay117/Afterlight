"""AFTERLIGHT's original Sun Receipt identity: portable outlined SVG and transparent PNG."""
from pathlib import Path
import sys, json, math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tooling/python'))
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

OUT=ROOT/'artifacts/brand';WEB=ROOT/'public/brand';OUT.mkdir(parents=True,exist_ok=True);WEB.mkdir(parents=True,exist_ok=True)
INK='#2b1845';PURPLE='#713ce4';CORAL='#ff784f';YELLOW='#ffdd65';LIME='#c7ff74';PAPER='#f3effa';WHITE='#fffdf8'
BODY='M28 55H100V114L88 106L76 114L64 106L52 114L40 106L28 114Z'
SUN='M35 49A29 29 0 0 1 93 49Z'
RAYS='M64 8V15M26 19L32 25M102 19L96 25'
CUTS='M42 71H64M42 85H53M73 84L81 92L94 73'
variants={'primary':(PURPLE,CORAL,INK,INK),'reversed':(LIME,CORAL,LIME,WHITE),'mono':(INK,INK,INK,INK),'white':(WHITE,WHITE,WHITE,WHITE)}

def mark_svg(variant='primary',prefix='mark'):
    body,sun,rays,_=variants[variant]
    return f'''<defs><mask id="{prefix}"><rect width="128" height="128" fill="black"/><path d="{BODY}" fill="white"/><path d="{CUTS}" fill="none" stroke="black" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></mask></defs><path d="{SUN}" fill="{sun}"/><path d="{RAYS}" stroke="{rays}" stroke-width="5" stroke-linecap="round"/><path d="{BODY}" fill="{body}" mask="url(#{prefix})"/>'''

def mark_png(size,variant='primary',tile=False):
    scale=size/128;im=Image.new('RGBA',(size,size));d=ImageDraw.Draw(im)
    def pts(values):return [(round(x*scale),round(y*scale)) for x,y in values]
    body,sun,rays,_=variants[variant]
    if tile:
        d.rounded_rectangle((0,0,size-1,size-1),radius=round(size*.21),fill=PURPLE)
        body,sun,rays=WHITE,YELLOW,YELLOW
    d.pieslice((35*scale,20*scale,93*scale,78*scale),180,360,fill=sun)
    for a,b in [((64,8),(64,15)),((26,19),(32,25)),((102,19),(96,25))]:
        d.line(pts([a,b]),fill=rays,width=max(1,round(5*scale)))
        for x,y in pts([a,b]):r=2.5*scale;d.ellipse((x-r,y-r,x+r,y+r),fill=rays)
    poly=pts([(28,55),(100,55),(100,114),(88,106),(76,114),(64,106),(52,114),(40,106),(28,114)])
    paper=Image.new('RGBA',(size,size));pd=ImageDraw.Draw(paper);pd.polygon(poly,fill=body)
    for path in [[(42,71),(64,71)],[(42,85),(53,85)],[(73,84),(81,92),(94,73)]]:
        pd.line(pts(path),fill=(0,0,0,0),width=max(1,round(6*scale)),joint='curve')
        for x,y in pts([path[0],path[-1]]):r=3*scale;pd.ellipse((x-r,y-r,x+r,y+r),fill=(0,0,0,0))
    if tile:
        # Knockouts reveal the same violet substrate in the app tile.
        base=Image.new('RGBA',(size,size),PURPLE);base.alpha_composite(paper);paper=base
        # Preserve the sun and rays above the paper's horizon.
        paper.alpha_composite(im.crop((0,0,size,round(55*scale))),(0,0));return paper
    im.alpha_composite(paper);return im

source=TTFont(ROOT/'public/fonts/BricolageGrotesque.ttf')
static=instantiateVariableFont(source,{'opsz':72,'wdth':100,'wght':760},inplace=False)
static_path=ROOT/'.tooling/logo-font.ttf';static.save(static_path)
glyphs=static.getGlyphSet();cmap=static.getBestCmap();units=static['head'].unitsPerEm
scale=104/units;advance=0;word=[];positions=[]
for letter in 'afterlight':
    name=cmap[ord(letter)];pen=SVGPathPen(glyphs);glyphs[name].draw(pen)
    word.append((advance,pen.getCommands()));positions.append(advance)
    advance+=static['hmtx'][name][0]-17
word_width=advance*scale;view_width=math.ceil(132+word_width+27);view_height=128

for variant in variants:
    color=variants[variant][3]
    paths=''.join(f'<path d="{d}" transform="translate({132+x*scale:.4f} 91) scale({scale:.6f} {-scale:.6f})"/>' for x,d in word)
    dot=CORAL if variant in ['primary','reversed'] else color
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{view_width}" height="128" viewBox="0 0 {view_width} 128" role="img" aria-label="AFTERLIGHT Sun Receipt logo"><title>AFTERLIGHT — Sun Receipt</title>{mark_svg(variant)}<g fill="{color}">{paths}</g><circle cx="{132+word_width+9:.3f}" cy="84" r="7" fill="{dot}"/></svg>'
    (OUT/f'afterlight-logo-{variant}.svg').write_text(svg+'\n')
    (OUT/f'afterlight-icon-{variant}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="AFTERLIGHT Sun Receipt">{mark_svg(variant)}</svg>\n')
    mult=5;im=Image.new('RGBA',(view_width*mult,128*mult));im.alpha_composite(mark_png(128*mult,variant),(0,0));d=ImageDraw.Draw(im)
    pf=ImageFont.truetype(str(static_path),104*mult)
    for letter,x in zip('afterlight',positions):d.text(((132+x*scale)*mult,91*mult),letter,font=pf,fill=color,anchor='ls')
    cx=(132+word_width+9)*mult;cy=84*mult;r=7*mult;d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=dot)
    im.save(OUT/f'afterlight-logo-{variant}.png')
    mark_png(1024,variant).save(OUT/f'afterlight-icon-{variant}.png')

mark_png(1024,tile=True).save(OUT/'afterlight-app-icon.png')
(WEB/'logo.svg').write_bytes((OUT/'afterlight-logo-primary.svg').read_bytes())
(WEB/'icon.svg').write_bytes((OUT/'afterlight-icon-primary.svg').read_bytes())
(ROOT/'public/favicon.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="26" fill="{PURPLE}"/>{mark_svg("white","favicon").replace(WHITE,YELLOW)}</svg>\n')

# Editorial presentation of the identity; underlying logo exports remain transparent.
board=Image.new('RGB',(1920,1080),PAPER);bd=ImageDraw.Draw(board)
def bf(size,weight=600):
    f=ImageFont.truetype(str(ROOT/'public/fonts/BricolageGrotesque.ttf'),size);f.set_variation_by_axes([weight if b'Weight' in a['name'] else a['default'] for a in f.get_variation_axes()]);return f
bd.text((82,67),'AFTERLIGHT / THE SUN RECEIPT',font=bf(24,700),fill=INK)
bd.text((82,103),'Solar energy. Verifiable evidence.',font=bf(23,500),fill='#736681')
logo=Image.open(OUT/'afterlight-logo-primary.png');logo.thumbnail((1470,315),Image.Resampling.LANCZOS);board.paste(logo,((1920-logo.width)//2,220),logo)
bd.line((80,619,1840,619),fill='#cbbfdc',width=2)
for x,color,variant,title in [(80,WHITE,'primary','PRIMARY'),(690,INK,'reversed','ON DARK'),(1300,YELLOW,'mono','ONE COLOUR')]:
    bd.rounded_rectangle((x,672,x+540,960),radius=15,fill=color)
    icon=mark_png(215,variant);board.paste(icon,(x+162,693),icon)
    bd.text((x+270,922),title,font=bf(17,650),fill=WHITE if variant=='reversed' else INK,anchor='mm')
bd.text((82,1012),'A sunset above a torn receipt. A check cut into the paper. One coherent mark.',font=bf(22,500),fill=INK)
board.save(OUT/'afterlight-brand-board.png')
(OUT/'brand-spec.json').write_text(json.dumps({'name':'Sun Receipt','concept':'A sunset above a torn receipt; negative-space check and ledger lines','palette':{'violet':PURPLE,'coral':CORAL,'ink':INK,'lime':LIME,'yellow':YELLOW},'wordmark':'Bricolage Grotesque, custom spacing and outlined glyphs','svgFontDependency':False,'logoViewBox':[0,0,view_width,128]},indent=2)+'\n')
print(f'Brand kit exported to {OUT}; horizontal SVG {view_width} × 128, all glyphs outlined.')
