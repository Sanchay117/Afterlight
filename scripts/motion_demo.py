"""AFTERLIGHT motion film: original vector animation, real UI captures, Deepgram and original score."""
from pathlib import Path
from functools import lru_cache
import argparse, json, math, re, subprocess, textwrap, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from score import compose, save_pcm, RATE

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts';WORK=OUT/'video-frames/motion'
W,H,FPS=1920,1080,24
PAPER='#f3effa';INK='#2b1845';PURPLE='#713ce4';LIME='#c7ff74';CORAL='#ff784f';PINK='#ffafd1';YELLOW='#ffdd65';MUTED='#78688b';WHITE='#fffdf8'
ACCENTS=[YELLOW,CORAL,YELLOW,PINK,LIME,LIME,PURPLE,CORAL,PINK,LIME,YELLOW]
BRAND_LOGO=Image.open(OUT/'brand/afterlight-logo-primary.png').convert('RGBA');BRAND_LOGO.thumbnail((242,55),Image.Resampling.LANCZOS)
SCENES=json.loads((ROOT/'docs/demo-scenes.json').read_text())
DATA=json.loads((OUT/'motion-data.json').read_text())
TOPICS=['Does the sun back it up?','72 kWh appeared after sunset.','Below capacity. Outside the envelope.','The same total can tell a different story.','Three splits. One untouched test set.','Every hour earns its place.','One certificate. Twenty-four locked slots.','A new root cannot unlock old hours.','One changed reading changes the root.','Retirement does not release the intervals.','Protect the claim. Show your limits.']

@lru_cache(maxsize=80)
def font(size,bold=False):
    f=ImageFont.truetype(str(ROOT/'public/fonts/BricolageGrotesque.ttf'),max(8,int(size)))
    f.set_variation_by_axes([(760 if bold else 500) if b'Weight' in a['name'] else a['default'] for a in f.get_variation_axes()])
    return f

def clamp(v,a=0,b=1):return min(b,max(a,v))
def ease(v):return 1-(1-clamp(v))**3
def smooth(v):v=clamp(v);return v*v*(3-2*v)
def rgba(c,a=255):return (*tuple(bytes.fromhex(c.lstrip('#'))),int(a))
def wrap_lines(text,width,f):
    d=ImageDraw.Draw(Image.new('RGB',(1,1)));lines=[]
    for para in text.split('\n'):
        line=''
        for word in para.split():
            test=(line+' '+word).strip()
            if line and d.textlength(test,font=f)>width:lines.append(line);line=word
            else:line=test
        lines.append(line)
    return lines
def label(draw,xy,text,size=20,color=INK,bold=False,anchor=None):draw.text(xy,str(text),font=font(size,bold),fill=color,anchor=anchor)
def text_sprite(text,width,size=24,color=INK,bold=False,line_height=None):
    f=font(size,bold);lines=wrap_lines(text,width,f);lh=line_height or round(size*1.27)
    im=Image.new('RGBA',(width+8,lh*len(lines)+10));d=ImageDraw.Draw(im)
    for i,line in enumerate(lines):d.text((0,i*lh),line,font=f,fill=color)
    return im
def paste_motion(base,im,x,y,alpha=1):
    if alpha<=0:return
    if alpha<.999:im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:round(a*alpha)))
    base.paste(im,(round(x),round(y)),im)
def arrow(d,a,b,color=PURPLE,width=4):
    d.line([a,b],fill=color,width=width);angle=math.atan2(b[1]-a[1],b[0]-a[0]);n=12
    d.polygon([b,(b[0]-n*math.cos(angle-.4),b[1]-n*math.sin(angle-.4)),(b[0]-n*math.cos(angle+.4),b[1]-n*math.sin(angle+.4))],fill=color)
def sun(d,cx,cy,r,t,color=YELLOW):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=color)
    for i in range(12):
        a=i*math.tau/12+t*.12
        d.line([(cx+1.22*r*math.cos(a),cy+1.22*r*math.sin(a)),(cx+1.48*r*math.cos(a),cy+1.48*r*math.sin(a))],fill=color,width=max(2,round(r/12)))

def graphic(index,t,width,height,mini=False):
    """Render an explicitly labelled explanation, never altered UI or invented telemetry."""
    im=Image.new('RGB',(width,height),INK);d=ImageDraw.Draw(im)
    sx,sy=width/1000,height/500
    def pt(x,y):return (round(x*sx),round(y*sy))
    def box(coords,fill,outline=None,radius=12,width_=2):
        d.rounded_rectangle(tuple(pt(coords[i],coords[i+1]) for i in (0,2)),radius=max(2,round(radius*min(sx,sy))),fill=fill,outline=outline,width=width_)
    def txt(x,y,text,size=22,color=WHITE,bold=False,anchor=None):
        label(d,pt(x,y),text,max(10,round(size*min(sx,sy))),color,bold,anchor)
    def line(points,color=PURPLE,stroke=3):d.line([pt(*p) for p in points],fill=color,width=max(2,round(stroke*min(sx,sy))),joint='curve')
    reveal=ease(t/3.6)
    if index in [1,2,3,5]:
        key={1:'night',2:'peak',3:'shift',5:'clean'}[index];rows=DATA['profiles'][key]['hours']
        left,right,top,bottom=65,953,75,420
        for value in [0,25,50,75,100]:
            yy=bottom-value/110*(bottom-top);line([(left,yy),(right,yy)],'#5d466f',1)
            if not mini:txt(48,yy,str(value),16,'#b5a2ca',anchor='rm')
        x=lambda i:left+i/23*(right-left);y=lambda v:bottom-v/110*(bottom-top)
        for row in rows:
            if row['status']!='PASS':box((x(row['hour'])-12,top,x(row['hour'])+12,bottom),'#513047',radius=4)
        count=max(2,min(24,math.ceil(reveal*24)))
        line([(x(i),y(r['expected'])) for i,r in enumerate(rows[:count])],'#a684ff',5)
        line([(x(i),y(r['claim'])) for i,r in enumerate(rows[:count])],CORAL,4)
        scan=min(23,int((t*.8)%24));rr=rows[scan];line([(x(scan),top),(x(scan),bottom)],'#fffdf844',1)
        for i,row in enumerate(rows[:count]):
            if row['status']!='PASS' or i==scan:
                xx,yy=pt(x(i),y(row['claim']));r=max(3,round((6+(2*math.sin(t*3) if i==scan else 0))*min(sx,sy)))
                d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=YELLOW if i==scan else CORAL)
        if not mini:
            for i in [0,6,12,18,23]:txt(x(i),445,f'{i:02}:00',18,'#cbbbdc',anchor='mm')
            txt(65,25,'HOURLY ENERGY / kWh',19,LIME,True)
            txt(953,25,DATA['profiles'][key]['status'],20,CORAL if key!='clean' else LIME,True,anchor='ra')
    elif index==0:
        cx,cy=pt(500,250);r=min(width*.19,height*.30)
        sun(d,cx,cy,r,t,YELLOW)
        rows=DATA['profiles']['night']['hours']
        for row in rows:
            a=row['hour']/24*math.tau-math.pi/2+t*.04;reach=r*1.62+row['claim']/100*r*.5
            col=CORAL if row['status']=='REJECT' else LIME
            d.line([(cx+r*1.58*math.cos(a),cy+r*1.58*math.sin(a)),(cx+reach*math.cos(a),cy+reach*math.sin(a))],fill=col,width=max(3,round(width/180)))
        if not mini:
            txt(500,242,'AFTERLIGHT',44,INK,True,anchor='mm');txt(500,293,'SOLAR CLAIMS / VERIFIED EVIDENCE',15,INK,True,anchor='mm')
            txt(500,475,'Every registered hour has a story.',23,WHITE,anchor='mm')
    elif index==4:
        colors=[PINK,YELLOW,LIME];names=['TRAIN','CALIBRATE','TEST'];months=['JAN–JUN','JUL–SEP','OCT–DEC'];counts=[2182,1215,902]
        for i in range(3):
            start=65+i*310;p=ease((t-i*.45)/1.5)
            box((start,80,start+250,350),'#49335f',radius=12)
            if p>0:box((start,350-220*p,start+250,350),colors[i],radius=10)
            txt(start+125,135,names[i],30,INK if p>.9 else WHITE,True,anchor='mm')
            txt(start+125,200,months[i],20,INK,True,anchor='mm')
            txt(start+125,260,f'{round(counts[i]*p):,}',39,INK,True,anchor='mm')
            if i<2:arrow(d,pt(start+263,212),pt(start+297,212),LIME,max(2,round(3*sx)))
        if not mini:txt(500,415,'94.1% daylight coverage · 0.306 kW MAE',29,WHITE,True,anchor='mm');txt(500,464,'PVGIS modeled-power surrogate / chronological holdout',18,'#c8b4dd',anchor='mm')
    elif index in [6,7,9]:
        active=min(24,int(t*9)) if index==6 else 24
        for i in range(24):
            xx=100+(i%8)*102;yy=78+(i//8)*88;locked=i<active
            box((xx,yy,xx+78,yy+62),LIME if locked else '#573b71',radius=7)
            if not mini:txt(xx+39,yy+31,f'{i:02}',24,INK if locked else WHITE,True,anchor='mm')
        if index==7:
            cycle=t%7;xx=100+ease(cycle/1.3)*670
            box((xx,360,xx+190,421),CORAL,radius=4);txt(xx+95,390,'NEW ROOT',20,INK,True,anchor='mm')
            if cycle>1.35:
                txt(500,457,'REVERTED: DuplicateInterval(0)',29,CORAL,True,anchor='mm')
                line([(842,355),(900,423)],CORAL,8);line([(900,355),(842,423)],CORAL,8)
        elif index==9:
            p=ease(t/1.7);box((210,360,790,444),LIME,radius=4)
            txt(500,402,'RETIRED / INTERVALS STAY LOCKED',27,INK,True,anchor='mm')
        elif not mini:txt(500,393,'ONE ASSET + ONE UTC HOUR = ONE SLOT',24,YELLOW,True,anchor='mm');txt(500,454,'24 slots reserved atomically in Solidity',22,WHITE,anchor='mm')
    elif index==8:
        edited=(t%9)>2.7;leaf_x=[140,380,620,860];leaf_y=410
        for i,xx in enumerate(leaf_x):
            col=CORAL if edited and i==1 else LIME
            box((xx-90,350,xx+90,445),col,radius=5)
            if not mini:txt(xx,390,['META','20:00','21:00','…'][i],24,INK,True,anchor='mm')
            parent=260 if i<2 else 740
            line([(xx,350),(parent,265)],CORAL if edited and i==1 else '#a38bbc',4)
        for i,xx in enumerate([260,740]):
            col=CORAL if edited and i==0 else PURPLE;box((xx-105,205,xx+105,270),col,radius=5)
            line([(xx,205),(500,125)],CORAL if edited and i==0 else '#a38bbc',4)
        box((290,50,710,135),CORAL if edited else LIME,radius=6)
        txt(500,91,'ROOT CHANGED' if edited else 'ROOT MATCHES',29,INK,True,anchor='mm')
        if not mini:txt(500,487,'Schematic excerpt / metadata + 24 readings are committed',18,'#d4c3e4',anchor='mm')
    else:
        cells=[('72 kWh','FLAGGED IN THE NIGHT CASE',CORAL),('24','INTERVALS RESERVED',LIME),('16','TESTS PASSED',YELLOW),('NEXT','AUTHENTICATED METERS',PINK)]
        for i,(value,caption,col) in enumerate(cells):
            xx=65+(i%2)*470;yy=55+(i//2)*225;p=ease((t-i*.18)/1.2)
            if p<=0:continue
            box((xx,yy+30*(1-p),xx+405,yy+185+30*(1-p)),col,radius=9)
            txt(xx+202,yy+75,value,48,INK,True,anchor='mm')
            if not mini:txt(xx+202,yy+136,caption,18,INK,True,anchor='mm')
    return im

class Chapter:
    def __init__(self,index,scene,start):
        self.index=index;self.scene=scene;self.start=start;self.lead=1.8 if index==0 else .45;self.tail=3 if index==10 else .75
        self.audio=OUT/'narration'/f'scene-{index:02d}.wav'
        self.speech=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(self.audio)]))
        self.frames=math.ceil((self.lead+self.speech+self.tail)*FPS);self.duration=self.frames/FPS
        self.layers=[];y=215;title=scene['title'];size=59
        while max(ImageDraw.Draw(Image.new('RGB',(1,1))).textlength(line,font=font(size,True)) for line in title.split('\n'))>574:size-=1
        title_im=text_sprite(title,584,size,INK,True,round(size*1.16));self.layers.append((title_im,72,y,.15));y+=title_im.height+18
        self.stat=None;self.stat_y=y
        if scene.get('stat'):
            self.stat=scene['stat'];y+=82
            caption=text_sprite(scene['statLabel'],565,21,MUTED);self.layers.append((caption,76,y,.75));y+=caption.height+24
        else:y+=32
        for i,b in enumerate(scene['bullets']):
            layer=text_sprite('•  '+b,558,23,INK,False,30);self.layers.append((layer,77,y,1.1+i*.55));y+=layer.height+17
        self.mini_y=max(742,min(812,y+22));self.mini_h=956-self.mini_y
        self.screenshot=Image.open(OUT/'screenshots'/scene['screen']).convert('RGB').resize((1118,776),Image.Resampling.LANCZOS)
        self.stat_final=self.stat_image(self.stat) if self.stat else None
        self.mini_static=Image.new('RGB',(584,self.mini_h),INK)
    def stat_image(self,value):
        im=Image.new('RGBA',(590,83));d=ImageDraw.Draw(im);f=font(47,True);end=min(584,round(d.textlength(value,font=f))+37)
        d.rounded_rectangle((1,1,end,76),radius=5,fill=YELLOW,outline=INK,width=2);d.text((15,9),value,font=f,fill=INK);return im
    def render(self,t,total):
        base=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(base)
        base.paste(BRAND_LOGO,(74,52),BRAND_LOGO)
        label(d,(74,145),self.scene['label'],16,MUTED,True)
        label(d,(1835,70),'DEEPGRAM / THALIA',14,MUTED,True,anchor='ra')
        for layer,x,y,when in self.layers:
            p=ease((t-when)/.7);paste_motion(base,layer,x+36*(1-p),y+12*(1-p),p)
        if self.stat:
            p=ease((t-.5)/1.4);value=self.stat
            match=re.match(r'([\d,.]+)(.*)',value)
            if match and p<1:
                number=match[1];decimals=len(number.split('.')[-1]) if '.' in number else 0
                value=f'{float(number.replace(",",""))*p:,.{decimals}f}'+match[2]
            paste_motion(base,self.stat_final if p==1 else self.stat_image(value),74,self.stat_y+18*(1-p),ease((t-.4)/.6))
        # A first-principles explanatory diagram resolves into the actual, unmodified application capture.
        big=Image.new('RGB',(1118,776),INK);bd=ImageDraw.Draw(big)
        label(bd,(43,28),'HOW THE CHECK WORKS / ANIMATED EXPLANATION',15,LIME,True)
        topic=text_sprite(TOPICS[self.index],1020,35,WHITE,True,44);big.paste(topic,(43,80),topic)
        big.paste(graphic(self.index,t,1026,480),(46,218))
        label(bd,(44,736),'DEMONSTRATION DATA · EXPLANATORY DIAGRAM',14,'#c6b2dc')
        p=smooth((t-5.2)/1.05)
        if p>=1:big=self.screenshot
        elif p>0:big=Image.blend(big,self.screenshot,p)
        d.rounded_rectangle((703,134,1854,944),radius=20,fill=INK)
        base.paste(big,(719,150))
        label(d,(720,954),'CAPTURED WORKING PROTOTYPE' if p>=1 else 'FROM CLIMATE EVIDENCE TO A CHECKABLE CLAIM',15,MUTED,True)
        # Persistent motion while the viewer reads the proof: scanning data, locks, and propagation.
        mini=graphic(self.index,t,584,max(90,self.mini_h),True)
        base.paste(mini,(74,self.mini_y))
        label(d,(74,self.mini_y-23),'THE SIGNAL / EXPLAINED',12,MUTED,True)
        d.line((74,989,1840,989),fill='#d0c1df',width=2)
        progress=(self.start+t)/total;d.line((74,989,74+1766*progress,989),fill=PURPLE,width=4)
        label(d,(74,1012),'IEEE CLIMATECHAIN / RENEWABLE ENERGY & ENERGY TRADING',15,MUTED)
        label(d,(1840,1012),f'{self.index+1:02} / 11',16,MUTED,anchor='ra')
        # Matched-color chapter wipes hide the cut without overlapping narration.
        if t<.42:
            x=round(W*ease(t/.42));d.rectangle((x,0,W,H),fill=ACCENTS[self.index])
        if t>self.duration-.28:
            x=round(W*ease((t-(self.duration-.28))/.28));d.rectangle((0,0,x,H),fill=ACCENTS[(self.index+1)%11])
        return base

def make_timeline():
    chapters=[];cursor=0
    for i,s in enumerate(SCENES):
        c=Chapter(i,s,cursor);chapters.append(c);cursor+=c.duration
    return chapters,cursor

def prepare_audio(chapters,total):
    speech=np.zeros(round(total*RATE),dtype=np.float32)
    for c in chapters:
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(c.audio),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar',str(RATE),'-ac','1','-f','f32le','-'])
        audio=np.frombuffer(raw,dtype='<f4');start=round((c.start+c.lead)*RATE);end=min(len(speech),start+len(audio));speech[start:end]=audio[:end-start]
    save_pcm(WORK/'narration.wav',speech)
    score=compose(total,WORK/'score.wav')
    score.update({'mix':'Narration-driven sidechain compression; score falls under speech and rises in pauses','bedGain':.35,'sidechain':{'threshold':.04,'ratio':4,'attackMs':18,'releaseMs':500}})
    (OUT/'music-provenance.json').write_text(json.dumps(score,indent=2)+'\n')
    print('Original score and normalized Deepgram narration prepared.',flush=True)

def write_captions(chapters):
    def stamp(t):
        m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
    entries=[];idx=1
    for c in chapters:
        phrases=textwrap.wrap(c.scene['narration'],width=90);weights=[len(p) for p in phrases];begin=c.start+c.lead
        for phrase,weight in zip(phrases,weights):
            end=begin+c.speech*weight/sum(weights);entries.append(f'{idx}\n{stamp(begin)} --> {stamp(end)}\n{phrase}\n');begin=end;idx+=1
    (OUT/'afterlight-demo.srt').write_text('\n'.join(entries))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--render-only',action='store_true');parser.add_argument('--audio-only',action='store_true');args=parser.parse_args()
    WORK.mkdir(parents=True,exist_ok=True);chapters,total=make_timeline()
    timeline={'duration':total,'fps':FPS,'motion':'Vector explanations, kinetic typography, data traces, count-ups, matched-color wipes and animated proof schematics','scenes':[{'scene':c.index+1,'start':c.start,'duration':c.duration,'speechStart':c.start+c.lead,'speechDuration':c.speech,'title':c.scene['title'].replace('\n',' '),'narration':c.scene['narration']} for c in chapters]}
    if args.preview:
        for c in chapters:
            c.render(3.4,total).save(WORK/f'preview-{c.index:02}-diagram.png');c.render(9,total).save(WORK/f'preview-{c.index:02}-ui.png')
        print('Motion contact frames ready.',flush=True);return
    (OUT/'demo-timing.json').write_text(json.dumps(timeline,indent=2)+'\n');write_captions(chapters)
    if not args.render_only:prepare_audio(chapters,total)
    if args.audio_only:return
    silent=WORK/'motion-silent.mp4'
    encoder=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-threads','4',str(silent)],stdin=subprocess.PIPE)
    try:
        for c in chapters:
            for frame in range(c.frames):encoder.stdin.write(c.render(frame/FPS,total).tobytes())
            print(f'Motion chapter {c.index+1}/11 rendered ({c.start+c.duration:.1f}s of {total:.1f}s).',flush=True)
        encoder.stdin.close();code=encoder.wait()
        if code:raise RuntimeError(f'Video encoder exited with code {code}')
    except BaseException:
        encoder.kill();encoder.wait();raise
    filters=f'[1:a]asplit=2[voice][trigger];[2:a]volume=0.35,afade=t=in:d=1.5,afade=t=out:st={total-3}:d=3[bed];[bed][trigger]sidechaincompress=threshold=0.04:ratio=4:attack=18:release=500[ducked];[voice][ducked]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.94:level=0[mix]'
    result=OUT/'afterlight-motion.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(WORK/'narration.wav'),'-i',str(WORK/'score.wav'),'-i',str(OUT/'afterlight-demo.srt'),'-filter_complex',filters,'-map','0:v:0','-map','[mix]','-map','3:s:0','-c:v','copy','-c:a','aac','-ar','48000','-b:a','192k','-ac','2','-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata','title=AFTERLIGHT — Solar claims with an alibi','-metadata','comment=Deepgram Aura-2 Thalia narration; original Solar Alibi score; programmatic motion graphics','-t',str(total),'-movflags','+faststart',str(result)],check=True)
    import shutil
    shutil.copy2(result,OUT/'afterlight-demo.mp4')
    chapters[1].render(3.4,total).save(OUT/'afterlight-poster.png')
    doc=['# AFTERLIGHT motion demonstration','',f'Duration: {int(total//60)}:{round(total%60):02}. 1920×1080, 24 fps, stereo audio, optional English subtitles.','', 'Original animated data explanations and kinetic typography introduce each chapter, then resolve into actual captured UI states. The animation is an explanatory layer, not a fabricated screen recording. Deepgram Aura-2 Thalia narrates. The original 96 BPM Solar Alibi score is synthesized without third-party music or samples and ducks under speech.','']
    for c in chapters:doc.extend([f'## {int(c.start)//60:02}:{int(c.start)%60:02} — {c.scene["title"].replace(chr(10)," ")}', '',c.scene['narration'],''])
    (ROOT/'docs/DEMO.md').write_text('\n'.join(doc))
    print(f'Completed motion film: {total:.3f}s / {result}',flush=True)

if __name__=='__main__':main()
