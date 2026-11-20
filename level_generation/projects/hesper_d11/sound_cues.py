"""Small original PCM cues for the ship's heartbeat, neural hum and attack warning."""
import math
import random
import struct
import wave

def build(directory):
    directory.mkdir(parents=True,exist_ok=True)
    rate=22050
    rng=random.Random(9123)
    for name,seconds in [('heartbeat',.8),('convulsion',1.2),('lunge',1.5)]+[(f'hum{k}',2.5) for k in range(1,5)]:
        samples=[]
        for i in range(round(rate*seconds)):
            t=i/rate
            if name=='heartbeat':value=math.sin(2*math.pi*55*t)*(math.exp(-18*t)+.65*math.exp(-25*abs(t-.26)))
            elif name=='convulsion':value=.6*rng.uniform(-1,1)*math.exp(-3*t)+.3*math.sin(2*math.pi*44*t)
            elif name=='lunge':value=.45*math.sin(2*math.pi*(180*t+180*t*t))
            else:value=.22*math.sin(2*math.pi*(70+int(name[-1])*25)*t)
            envelope=min(1,t/.02,(seconds-t)/.08)
            samples.append(round(15000*envelope*value))
        assert max(map(abs,samples))<32768
        with wave.open(str(directory/f'd11_{name}.wav'),'wb') as f:
            f.setparams((1,2,rate,len(samples),'NONE','not compressed'));f.writeframes(struct.pack(f'<{len(samples)}h',*samples))
