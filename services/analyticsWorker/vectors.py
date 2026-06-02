# from transformers import ClapModel, ClapProcessor
import torchaudio
import time

# print("Loading in CLAP models........\n")

# start = time.time()
# model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
# processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")

# print(f"Loaded CLAP models:{time.time() - start:.2f}s \n")

print("Beginning analysis.....\n")
start = time.time()

waveform, sr = torchaudio.load("/Users/kitwj/Documents/Personal/Projects/QueuedMusicAnalysis/jungle.mp3")
print(f"Loaded audio into memory:{time.time() - start:.2f}s")

start = time.time()


print(f"Song Hz: {sr}\n")
