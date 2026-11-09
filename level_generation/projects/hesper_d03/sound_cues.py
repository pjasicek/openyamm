"""Own synthesized Quarry cues; deterministic PCM, no external recordings or licences."""
import math
import random
import struct
import wave


def build(directory):
    directory.mkdir(parents=True, exist_ok=True)
    rate = 22050
    rng = random.Random(9111)
    for name, seconds in [('pylon', 0.4), ('alarm', 2.4), ('pod', 0.7), ('crusher', 4),
                          ('membrane', 0.7), ('cage', 0.6)]:
        samples = []
        for i in range(round(rate * seconds)):
            t = i / rate
            noise = rng.uniform(-1, 1)
            if name == 'pylon':
                signal = math.sin(2 * math.pi * 620 * t) * math.exp(-12 * t)
            elif name == 'alarm':
                phase = 2 * math.pi * (180 * t + 18 * math.sin(2 * math.pi * 1.5 * t))
                signal = (math.sin(phase) + 0.35 * math.sin(3 * phase)) / 1.35
            elif name == 'pod':
                signal = noise * math.exp(-6 * t) + 0.3 * math.sin(2 * math.pi * 70 * t)
            elif name == 'crusher':
                signal = (noise * 0.5 + math.sin(2 * math.pi * 48 * t) * 0.3) * (
                    0.4 + 0.6 * math.exp(-18 * (t % 0.8)))
            elif name == 'membrane':
                signal = noise * 0.5 + math.sin(2 * math.pi * (160 * t - 50 * t * t)) * 0.3
            else:
                signal = noise * math.exp(-25 * (t % 0.12))
            envelope = min(1, t / 0.02, (seconds - t) / 0.04)
            samples.append(round(16000 * envelope * signal))
        assert max(map(abs, samples)) < 32768
        with wave.open(str(directory / f'd03_{name}.wav'), 'wb') as stream:
            stream.setparams((1, 2, rate, len(samples), 'NONE', 'not compressed'))
            stream.writeframes(struct.pack(f'<{len(samples)}h', *samples))
