"""Render a narrated product demo from actual captured UI states. Deepgram Aura-2 narration + ffmpeg + Pillow."""
from pathlib import Path
import json, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'
FRAMES = OUT / 'video-frames'
FRAMES.mkdir(exist_ok=True)
SCENES = json.loads((ROOT / 'docs/demo-scenes.json').read_text())
FONT = ROOT / 'public/fonts/BricolageGrotesque.ttf'
def font(size, style='Arial'):
    f=ImageFont.truetype(str(FONT),size)
    axes=f.get_variation_axes()
    f.set_variation_by_axes([750 if b'Weight' in a['name'] and ('Bold' in style or style=='Georgia') else 500 if b'Weight' in a['name'] else a['default'] for a in axes])
    return f
PAPER = '#f3effa'; INK = '#2b1845'; MUTED = '#736681'; GOLD = '#713ce4'; LINE = '#cbbfdc'
def wrapped(draw, text, x, y, max_width, f, fill, line_height):
    for paragraph in text.split('\n'):
        words, line = paragraph.split(), ''
        for word in words:
            candidate = (line+' '+word).strip()
            if draw.textlength(candidate,font=f)>max_width and line:
                draw.text((x,y),line,font=f,fill=fill); y+=line_height; line=word
            else: line=candidate
        draw.text((x,y),line,font=f,fill=fill); y+=line_height
    return y

timing=[]; cursor=0
for i,s in enumerate(SCENES):
    image=Image.new('RGB',(1920,1080),PAPER);d=ImageDraw.Draw(image)
    d.rounded_rectangle((74,49,132,107),radius=13,fill=GOLD)
    d.arc((87,61,119,94),180,360,fill='#ffdd65',width=3);d.line((85,88,121,88),fill='#ffdd65',width=3)
    d.text((151,65),'AFTERLIGHT',font=font(29,'Arial Bold'),fill=INK)
    wrapped(d,s['label'],74,157,580,font(17,'Arial Bold'),MUTED,22)
    titlefont=font(63,'Georgia')
    if max(d.textlength(line,font=titlefont) for line in s['title'].split('\n'))>590:titlefont=font(51,'Georgia')
    y=wrapped(d,s['title'],70,221,590,titlefont,INK,76)+22
    if s.get('stat'):
        statfont=font(52,'Georgia')
        end=min(658,106+d.textlength(s['stat'],font=statfont))
        d.rounded_rectangle((74,y+6,end,y+84),radius=5,fill='#ffdd65',outline=INK,width=2)
        d.text((89,y+15),s['stat'],font=statfont,fill=INK);y+=104
        y=wrapped(d,s['statLabel'],78,y,560,font(22),MUTED,29)+43
    else:y+=55
    for b in s['bullets']:
        d.ellipse((79,y+11,86,y+18),fill=GOLD)
        y=wrapped(d,b,105,y,540,font(25),INK,34)+22
    # Captures are genuine UI states from the local application, presented as a responsive viewport.
    screenshot=Image.open(OUT/'screenshots'/s['screen']).convert('RGB')
    screenshot.thumbnail((1120,778),Image.Resampling.LANCZOS)
    # Scale up the small native panel screenshot without altering its contents.
    ratio=min(1120/screenshot.width,778/screenshot.height)
    screenshot=screenshot.resize((round(screenshot.width*ratio),round(screenshot.height*ratio)),Image.Resampling.LANCZOS)
    x=718+(1120-screenshot.width)//2; sy=150
    d.rounded_rectangle((x-15,sy-15,x+screenshot.width+15,sy+screenshot.height+15),radius=20,fill='#fffdf8',outline=INK,width=2)
    image.paste(screenshot,(x,sy))
    d.text((720,sy+screenshot.height+22),'CAPTURED WORKING PROTOTYPE / SOLAR FORENSICS DESK',font=font(16,'Arial Bold'),fill=MUTED)
    d.line((74,987,1840,987),fill=LINE,width=2)
    d.text((74,1013),'IEEE ClimateChain  /  AI + blockchain for energy-claim integrity',font=font(19),fill=MUTED)
    d.text((1710,1013),f'{i+1:02d} / {len(SCENES):02d}',font=font(19),fill=MUTED)
    frame=FRAMES/f'scene-{i:02d}.png';image.save(frame)
    txt=FRAMES/f'scene-{i:02d}.txt';txt.write_text(s['narration'])
    audio=OUT/'narration'/f'scene-{i:02d}.wav'
    if not audio.exists(): raise RuntimeError('Missing Deepgram audio. Run npm run demo:narrate with DEEPGRAM_API_KEY first.')
    duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)])) + 0.65
    segment=FRAMES/f'scene-{i:02d}.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(frame),'-i',str(audio),'-vf','scale=1920:1080,format=yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.65','-t',str(duration),'-r','24','-c:v','libx264','-preset','fast','-tune','stillimage','-crf','22','-c:a','aac','-ar','48000','-b:a','160k',str(segment)],check=True)
    timing.append({'scene':i+1,'start':cursor,'duration':duration,'title':s['title'].replace('\n',' '),'narration':s['narration']})
    cursor+=duration
    print(f'Scene {i+1}/{len(SCENES)}: {duration:.1f}s',flush=True)

listing=FRAMES/'concat.txt';listing.write_text(''.join(f"file '{(FRAMES/f'scene-{i:02d}.mp4').as_posix()}'\n" for i in range(len(SCENES))))
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(OUT/'afterlight-demo.mp4')],check=True)
(OUT/'demo-timing.json').write_text(json.dumps({'duration':cursor,'scenes':timing},indent=2)+'\n')
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
captions=[];idx=1
for s in timing:
    phrases=textwrap.wrap(s['narration'],width=95)
    available=s['duration']-.65
    weights=[len(p) for p in phrases];total=sum(weights);start=s['start']
    for phrase,weight in zip(phrases,weights):
        end=start+available*weight/total
        captions.append(f'{idx}\n{stamp(start)} --> {stamp(end)}\n{phrase}\n');idx+=1;start=end
(OUT/'afterlight-demo.srt').write_text('\n'.join(captions))
captioned=FRAMES/'captioned.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(OUT/'afterlight-demo.mp4'),'-i',str(OUT/'afterlight-demo.srt'),'-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart',str(captioned)],check=True)
captioned.replace(OUT/'afterlight-demo.mp4')
Image.open(FRAMES/'scene-01.png').save(OUT/'afterlight-poster.png')
doc=['# AFTERLIGHT demonstration','',f'Narrated product demo: approximately {round(cursor//60)} minutes {round(cursor%60)} seconds, 1920×1080. The MP4 includes optional English subtitles; the SRT is also provided.','', 'Actual captured UI states are presented with annotations and Deepgram Aura-2 Thalia narration. This is an edited demonstration of the working app, not a continuous screen recording.','', 'Run the interactive version with `npm start`, open http://127.0.0.1:4173, and choose **Try to break it**.','']
for s in timing:
    seconds=round(s['start']);doc.extend([f"## {seconds//60:02d}:{seconds%60:02d} — {s['title']}",'',s['narration'],''])
(ROOT/'docs/DEMO.md').write_text('\n'.join(doc))
print(f'Final duration: {cursor:.2f}s',flush=True)
