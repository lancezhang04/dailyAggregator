import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav


class AudioRecorder:
    def __init__(self, samplerate=44100, channels=1):
        self.samplerate = samplerate
        self.channels = channels

    def record(self, output_filename="output.wav"):
        print("Recording started (Press Ctrl+C to stop)...")
        recording = []

        def callback(indata, frames, time, status):
            if status:
                print(status)
            recording.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.samplerate, channels=self.channels, callback=callback
            ):
                while True:
                    sd.sleep(100)
        except KeyboardInterrupt:
            print("Recording stopped.")

        if recording:
            audio_data = np.concatenate(recording, axis=0)
            wav.write(output_filename, self.samplerate, audio_data)
            return output_filename
        return None
