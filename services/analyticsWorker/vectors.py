from transformers import ClapModel, ClapProcessor
import torchaudio
import torch
import time

print("Loading CLAP model........\n")
start = time.time()
model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
print(f"Loaded CLAP model in {time.time() - start:.2f}s\n")

print("Loading song........\n")
start = time.time()

waveform, sr = torchaudio.load("/Users/kitwj/Documents/Personal/Projects/QueuedMusicAnalysis/jungle.mp3")
print(f"Loaded audio into memory in {time.time() - start:.2f}s\n")

#CLAP is trained at 48000hz so rescaling songs if needed
if sr != 48000:
	print("Rescaling audio file to 48000h........\n")
	start = time.time()
	resampler = torchaudio.transforms.Resample(sr, 48000)
	waveform = resampler(waveform)
	print(f"Rescaled audio in {time.time() - start:.2f}s")

start = time.time()
print(f"Converting waveform to numpy........\n")

y = waveform.mean(dim=0).numpy()

print(f"Converted in {time.time() - start:.2f}s")


start = time.time()
print(f"Applying CLAP processor........\n")

inputs = processor(audio=y, return_tensors="pt", sampling_rate=48000)

print(f"Applied processor in {time.time() - start:.2f}s\n")

start = time.time()
print(f"Extracting audio features........\n")

with torch.no_grad():
	embedding = model.get_audio_features(**inputs)
	print(f"Embedded shape of tensor: {embedding.pooler_output.shape}")

vector = embedding[0].numpy().tolist()

print(f"Extracted features in {time.time() - start:.2f}s\n")
print(f"Embedded vector dimensions: {len(vector[0])}\n")

