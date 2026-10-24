"""Render a narrated product demo from actual captured UI states. macOS say + ffmpeg + Pillow."""
from pathlib import Path
import json, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'
FRAMES = OUT / 'video-frames'
FRAMES.mkdir(exist_ok=True)
SCENES = json.loads((ROOT / 'docs/demo-scenes.json').read_text())
FONT = Path('/System/Library/Fonts/Supplemental')
def font(size, style='Arial'):
    return ImageFont.truetype(str(FONT / f'{style}.ttf'), size)
PAPER = '#f4f3ed'; INK = '#193a30'; MUTED = '#6f7c6c'; GOLD = '#ce9e65'; LINE = '#dce0d3'
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
    d.rounded_rectangle((74,49,132,107),radius=13,fill=INK)
    d.arc((87,61,119,94),180,360,fill=GOLD,width=3);d.line((85,88,121,88),fill=GOLD,width=3)
    d.text((151,65),'AFTERLIGHT',font=font(29,'Arial Bold'),fill=INK)
    d.text((74,157),s['label'],font=font(19,'Arial Bold'),fill=MUTED)
    titlefont=font(76,'Georgia')
    if max(d.textlength(line,font=titlefont) for line in s['title'].split('\n'))>1040:titlefont=font(66,'Georgia')
    y=wrapped(d,s['title'],70,217,1055,titlefont,INK,94)+22
    if s.get('stat'):
        d.text((74,y+13),s['stat'],font=font(63,'Georgia'),fill=GOLD);y+=100
        d.text((78,y),s['statLabel'],font=font(24),fill=MUTED);y+=73
    else:y+=55
    for b in s['bullets']:
        d.ellipse((79,y+11,86,y+18),fill=GOLD)
        y=wrapped(d,b,105,y,972,font(28),INK,40)+22
    # Captures are genuine UI states from the local application, presented as a responsive viewport.
    screenshot=Image.open(OUT/'screenshots'/s['screen']).convert('RGB')
    screenshot.thumbnail((566,790),Image.Resampling.LANCZOS)
    # Scale up the small native panel screenshot without altering its contents.
    ratio=min(566/screenshot.width,790/screenshot.height)
    screenshot=screenshot.resize((round(screenshot.width*ratio),round(screenshot.height*ratio)),Image.Resampling.LANCZOS)
    x=1248+(566-screenshot.width)//2; sy=150
    d.rounded_rectangle((x-15,sy-15,x+screenshot.width+15,sy+screenshot.height+15),radius=20,fill='#ffffff',outline=LINE,width=2)
    image.paste(screenshot,(x,sy))
    d.text((1250,sy+screenshot.height+22),'CAPTURED WORKING PROTOTYPE',font=font(16,'Arial Bold'),fill=MUTED)
    d.line((74,987,1840,987),fill=LINE,width=2)
    d.text((74,1013),'IEEE ClimateChain  /  AI + blockchain for energy-claim integrity',font=font(19),fill=MUTED)
    d.text((1710,1013),f'{i+1:02d} / {len(SCENES):02d}',font=font(19),fill=MUTED)
    frame=FRAMES/f'scene-{i:02d}.png';image.save(frame)
    txt=FRAMES/f'scene-{i:02d}.txt';txt.write_text(s['narration'])
    audio=FRAMES/f'scene-{i:02d}.aiff'
    subprocess.run(['say','-v','Samantha','-r','170','-f',str(txt),'-o',str(audio)],check=True)
    duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)])) + 0.65
    segment=FRAMES/f'scene-{i:02d}.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(frame),'-i',str(audio),'-vf','scale=1920:1080,format=yuv420p','-af','apad=pad_dur=0.65','-t',str(duration),'-r','24','-c:v','libx264','-preset','fast','-tune','stillimage','-crf','22','-c:a','aac','-b:a','160k',str(segment)],check=True)
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
doc=['# AFTERLIGHT demonstration','',f'Narrated product demo: approximately {round(cursor//60)} minutes {round(cursor%60)} seconds, 1920×1080. The MP4 includes optional English subtitles; the SRT is also provided.','', 'Actual captured UI states are presented with annotations and local synthetic narration. This is an edited demonstration of the working app, not a continuous screen recording.','', 'Run the interactive version with `npm start`, open http://127.0.0.1:4173, and choose **Walk through the demo**.','']
for s in timing:
    seconds=round(s['start']);doc.extend([f"## {seconds//60:02d}:{seconds%60:02d} — {s['title']}",'',s['narration'],''])
(ROOT/'docs/DEMO.md').write_text('\n'.join(doc))
print(f'Final duration: {cursor:.2f}s',flush=True)
