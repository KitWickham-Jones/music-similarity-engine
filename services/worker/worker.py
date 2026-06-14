from transformers import ClapModel, ClapProcessor
import torchaudio
import torch
from torch import Tensor
import time
import logging
import contextlib
import os
import librosa
import numpy as np

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def log_time(label):
	start = time.time()
	yield
	logger.info(f"{label} in {time.time() - start:.2f}s")

class TrackProcessor:
	def __init__(self):
		with log_time("Loaded CLAP Model"):
			self.model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
		with log_time("Loading CLAP Processor"):
			self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")

	def load_song(self, songPath: str) -> tuple[Tensor, int, np.ndarray]:	
		if not os.path.exists(songPath):
			raise FileNotFoundError(f"Audio file not found at: {songPath}")
		with log_time("Loaded song"):
			waveform, sr = torchaudio.load(songPath)
		if sr != 48000:
			waveform = self.rescale_song(waveform, sr)
		y = waveform.mean(dim=0).numpy()
		return waveform, sr, y

	def rescale_song(self, waveform: Tensor, sr: int) -> Tensor:
		resampler = torchaudio.transforms.Resample(sr, 48000)
		with log_time("Rescaled waveform"):
			return resampler(waveform)
	
	def extract_embedding(self, y: np.ndarray) -> list[float]:
		with log_time("Processor"):
			inputs = self.processor(audio=y, return_tensors="pt", sampling_rate=48000) # type: ignore
		with log_time("CLAP inferences"), torch.no_grad():
			embedding = self.model.get_audio_features(**inputs)
		return embedding.pooler_output[0].numpy().tolist()  # type: ignore

	def extract_metainfo(self, waveform: Tensor, sr: int, y: np.ndarray) -> dict:
		with log_time("Extracting metadata"):
			bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
			bpm = round(float(bpm[0]))  # type: ignore
			duration = waveform.shape[1] / sr
		return {"bpm": bpm, "duration": duration}
	
	def process(self, songPath: str) -> dict:
		#these have to be local to the scope of the caller of process (per thread)
		#otherwise multiple threads can access and corrupt the process variable space 
		#of each other 
		waveform, sr, y = self.load_song(songPath=songPath)
		embedding = self.extract_embedding(y=y)
		meta = self.extract_metainfo(waveform=waveform, y=y, sr=sr)
		return {
			"embedding" : embedding,
			"metadata" : meta 
		}
		
