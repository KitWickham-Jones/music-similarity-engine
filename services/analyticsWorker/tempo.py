import librosa
import time

TRACK_URL = "/Users/kitwj/Documents/Personal/Projects/QueuedMusicAnalysis/jungle.mp3"
print("Analysis starting......\n")
start = time.time()
y, sr = librosa.load(TRACK_URL, sr=None)
print(f"Load {TRACK_URL} into memory: {time.time() - start:.2f}s \n")

start = time.time()
temp, _ = librosa.beat.beat_track(y=y, sr=sr)
print(f"Serve {TRACK_URL} analytics: {time.time() - start:.2f}s \n")

print(f"Tempo= {float(temp[0])}")