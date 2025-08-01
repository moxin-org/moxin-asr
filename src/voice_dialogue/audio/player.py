import tempfile

import soundfile as sf
from playsound import playsound


def play_audio(audio_data, sample_rate=16000):
    with tempfile.NamedTemporaryFile('w+b', suffix='.wav') as soundfile:
        sf.write(soundfile, audio_data, samplerate=sample_rate, subtype='PCM_16', closefd=False)
        playsound(soundfile.name, block=True)
