import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav


def record_audio():
    print('recording started...')
    recording = []

    def callback(indata, frames, time, status):
        if status:
            print(status)
        recording.append(indata.copy())

    # keep recording until interrupted by the user
    try:
        with sd.InputStream(samplerate=44100, channels=1, callback=callback):
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print('recording stopped')

    wav.write('output.wav', 44100, np.concatenate(recording, axis=0))


if __name__ == '__main__':
    record_audio()
