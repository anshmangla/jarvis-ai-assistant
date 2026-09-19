import numpy as np
import sounddevice as sd
from openwakeword.model import Model
from utils.logger import logger
from config import config

class WakeWordDetector:
    """Handles wake word detection using openwakeword and sounddevice."""
    
    def __init__(self, wakeword: str = None):
        # Normalize the wakeword and handle official model name mapping
        raw_wakeword = wakeword or config.WAKE_WORD.lower()
        
        # Mapping common phrases to official openwakeword model names
        mapping = {
            "hey jarvis": "hey_jarvis",
            "hey nova": "hey_jarvis",
            "hey alexa": "alexa",
            "jarvis": "hey_jarvis",
        }
        
        self.wakeword = mapping.get(raw_wakeword, raw_wakeword.replace(" ", "_"))
        self.sample_rate = 16000
        self.chunk_size = 1280
        
        logger.info(f"Initializing Wake Word Detector for '{self.wakeword}' (ONNX mode)...")
        try:
            # Explicitly use ONNX since tflite-runtime is unavailable on some Python versions
            self.model = Model(
                wakeword_models=[self.wakeword],
                inference_framework="onnx"
            )
        except Exception as e:
            logger.error(f"Failed to load wake word model '{self.wakeword}'. "
                         f"Check if it's a valid openwakeword model: {e}")
            raise

    def wait_for_wakeword(self) -> bool:
        """
        Blocks and listens to the microphone until the wake word is detected.
        
        Returns:
            bool: True when the wake word is detected.
        """
        logger.info(f"Listening for wake word: {self.wakeword}")
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, 
                                channels=1, 
                                dtype='int16', 
                                blocksize=self.chunk_size) as stream:
                while True:
                    audio_chunk, overflowed = stream.read(self.chunk_size)
                    if overflowed:
                        logger.warning("Audio buffer overflow")
                        
                    # Flatten out the 2D array from sounddevice to a 1D numpy array
                    audio_data = audio_chunk.flatten()
                    
                    # openwakeword handles the state of the stream internally
                    prediction = self.model.predict(audio_data)
                    
                    for mdl_name, scores in self.model.prediction_buffer.items():
                        # The prediction buffer stores the recent probability window
                        if scores[-1] > 0.5:
                            logger.info(f"Wake word '{mdl_name}' detected!")
                            return True
                            
        except Exception as e:
            logger.error(f"Error while listening for wake word: {e}")
            return False
