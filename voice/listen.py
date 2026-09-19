import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from utils.logger import logger

class Transcriber:
    """Handles microphone recording and speech-to-text using faster-whisper."""
    
    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the transcription model.
        
        Args:
            model_size (str): The size of the whisper model (e.g., 'tiny', 'base', 'small').
            device (str): Device to run inference on ('cpu' or 'cuda').
            compute_type (str): Precision type ('int8', 'float16', etc.).
        """
        logger.info(f"Loading faster-whisper model '{model_size}' on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.sample_rate = 16000

    def listen_and_transcribe(self, duration: int = 5) -> str:
        """
        Records audio from the microphone for a fixed duration and transcribes it.
        
        Args:
            duration (int): Duration in seconds to record.
            
        Returns:
            str: The transcribed text.
        """
        logger.info(f"Listening for command ({duration}s)...")
        try:
            # Record using sounddevice
            recording = sd.rec(int(duration * self.sample_rate), 
                               samplerate=self.sample_rate, 
                               channels=1, 
                               dtype='float32')
            sd.wait()
            logger.info("Recording finished. Transcribing...")
            
            # slower-whisper can process numpy float32 directly but it needs a 1D array
            audio_data = recording.flatten()
            
            # Transcribe the numpy array
            segments, info = self.model.transcribe(audio_data, beam_size=5, language="en")
            
            transcribed_text = " ".join([segment.text for segment in segments])
            result = transcribed_text.strip()
            
            logger.info(f"User command: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during recording or transcription: {e}")
            return ""
