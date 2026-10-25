"""Original 96 BPM ambient-electronic score. No recordings, samples or external music."""
import json, math, wave
from pathlib import Path
import numpy as np

RATE=48000
def hz(midi):return 440*2**((midi-69)/12)
def save_pcm(path,audio):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1 if audio.ndim==1 else audio.shape[1]);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())

def compose(duration,path):
    n=round(duration*RATE);mix=np.zeros((n,2),dtype=np.float32)
    rng=np.random.default_rng(20261025);beat=60/96;bar=4*beat;chord_seconds=4*bar
    # Dm9 / Bbmaj7 / Fmaj9 / Cadd9. Voicings and melody are authored for this demo.
    chords=[[50,57,60,64,69],[46,53,57,62,65],[41,53,57,60,64],[48,55,60,62,67]]
    def add(start,signal,pan=.5,gain=1):
        begin=round(start*RATE)
        if begin>=n:return
        end=min(n,begin+len(signal));sig=signal[:end-begin]*gain
        mix[begin:end,0]+=sig*math.cos(pan*math.pi/2)
        mix[begin:end,1]+=sig*math.sin(pan*math.pi/2)
    for k,start in enumerate(np.arange(0,duration,chord_seconds)):
        notes=chords[k%4];length=min(chord_seconds+3,duration-start);t=np.arange(round(length*RATE))/RATE
        env=np.minimum(t/1.8,1)*np.minimum((length-t)/2.5,1)
        for j,note in enumerate(notes):
            f=hz(note);phase=float(rng.uniform(0,2*np.pi))
            pad=(np.sin(2*np.pi*f*t+phase)+.23*np.sin(2*np.pi*f*2*t)+.08*np.sin(2*np.pi*f*3*t))
            pad+=.28*np.sin(2*np.pi*f*1.0025*t+phase)
            pad*=env*(.8+.2*np.sin(2*np.pi*.08*t+j))
            add(start,pad,.16+j*.16,.025)
    # Soft, syncopated plucked pattern with alternating pan and restrained accents.
    order=[0,2,4,1,3,2,4,3]
    for i,start in enumerate(np.arange(0,duration,beat/2)):
        if i%32 in [25,27,29,31]:continue
        chord=chords[int(start//chord_seconds)%4];note=chord[order[i%8]%len(chord)]+12
        t=np.arange(round(.9*RATE))/RATE;f=hz(note)
        env=(1-np.exp(-t/.006))*np.exp(-t/.21)
        pluck=(np.sin(2*np.pi*f*t)+.18*np.sin(2*np.pi*2*f*t)+.05*np.sin(2*np.pi*3*f*t))*env
        gain=.028*(.68+.32*(i%4==0));pan=.28 if i%2==0 else .72
        add(start,pluck,pan,gain);add(start+beat*.75,pluck,1-pan,gain*.23);add(start+beat*1.5,pluck,pan,gain*.1)
    for i,start in enumerate(np.arange(0,duration,beat)):
        if i%4 in [0,2]:
            t=np.arange(round(.25*RATE))/RATE
            phase=2*np.pi*(46*t+30*.035*(1-np.exp(-t/.035)))
            add(start,np.sin(phase)*np.exp(-t/.08),.5,.032)
        t=np.arange(round(.045*RATE))/RATE;noise=rng.normal(0,1,len(t)).astype(np.float32)
        noise=np.concatenate(([0],np.diff(noise)))*np.exp(-t/.012)
        add(start+beat/2,noise,.42 if i%2 else .58,.0024)
    # Quiet stereo ambience from delays, preserving a clear centre for speech.
    for seconds,gain in [(.1875,.12),(.3125,.08),(.625,.04)]:
        delay=round(seconds*RATE);mix[delay:]+=mix[:-delay,::-1]*gain
    rms=float(np.sqrt(np.mean(mix**2)));mix*=.15/max(rms,1e-8)
    peak=float(np.max(np.abs(mix)))
    if peak>.8:mix*=.8/peak
    fade=np.minimum(np.arange(n)/RATE/1.8,1)*np.minimum((n-np.arange(n))/RATE/3,1)
    mix*=fade[:,None]
    save_pcm(path,mix)
    return {'title':'Solar Alibi','composer':'Original AFTERLIGHT procedural score','bpm':96,'key':'D minor / F major','sources':'Original synthesized instruments only; no third-party recordings or samples','durationSeconds':duration,'sampleRate':RATE,'channels':2,'seed':20261025,'rawRmsDbfs':20*math.log10(float(np.sqrt(np.mean(mix**2)))+1e-12)}
