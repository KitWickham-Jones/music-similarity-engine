from transformers import ClapModel, ClapProcessor
import torchaudio
import torch
from torch import Tensor
import time
import logging
import contextlib
import os
import librosa

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def log_time(label):
	start = time.time()
	yield
	logger.info(f"{label} in {time.time() - start:.2f}s")

class TrackProcessor:
	def __init__(self):
		with log_time("Loaded CLAP Model"):
			self.model = self.model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
		with log_time("Loading CLAP Processor"):
			self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
		self.sr = None
		self.waveform = None
		self.y = None

	def load_song(self, songPath: str, jobID: str):
		try:
			if not os.path.exists(songPath):
				raise FileNotFoundError(f"Audio file not found at: {songPath}")
			with log_time("Loaded song"):
				self.waveform, self.sr = torchaudio.load(songPath)
			if self.sr != 48000:
				self.rescale_song(self.waveform, self.sr)
			self.y = self.waveform.mean(dim=0).numpy()
		except Exception as e:
			logger.error(f"Job {jobID} failed: {e}")

	def rescale_song(self, waveform: Tensor, sr: int):
		resampler = torchaudio.transforms.Resample(sr, 48000)
		with log_time("Rescaled waveform"):
			self.waveform = resampler(waveform)
	
	def extract_embedding(self):
		with log_time("Processor"):
			inputs = self.processor(audio=self.y, return_tensors="pt", sampling_rate=48000)
		with log_time("CLAP inferences"), torch.no_grad():
			embedding = self.model.get_audio_features(**inputs)
		return embedding.pooler_output[0].numpy().tolist()

	def extract_metainfo(self):
		with log_time("Extracting metadata"):
			bpm, _ = librosa.beat.beat_track(y = self.y, sr= self.sr)
			bpm = round(float(bpm[0]))
			duration = self.waveform.shape[1] / self.sr
		return {"bpm": bpm, "duration": duration}
	
	def process(self, songPath: str, jobID: str):
		#Cleanup previous state
		self.waveform = self.sr = self.y = None

		self.load_song(songPath=songPath, jobID=jobID)
		if self.y is None:
			logger.error(f"Job {jobID} failed to load")
			return
		embedding = self.extract_embedding()
		meta = self.extract_metainfo()
		return {
			"embedding" : embedding,
			"metadata" : meta 
		}
		

