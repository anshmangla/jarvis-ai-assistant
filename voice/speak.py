import pyttsx3
from utils.logger import logger

class Speaker:
    """Handles Text-to-Speech using pyttsx3."""
    
    def __init__(self, rate: int = 175, volume: float = 1.0):
        """
        Store TTS configuration.
        """
        self.rate = rate
        self.volume = volume

    def speak(self, text: str) -> None:
        """
        Convert text to speech and play it immediately.
        Instantiates the engine per-call to avoid Windows event-loop lockups.
        
        Args:
            text (str): The text string to speak out loud.
        """
        try:
            logger.info(f"Assistant says: {text}")
            
            # Init engine locally to prevent SAPI5 COM errors
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            voices = engine.getProperty('voices')
            for voice in voices:
                if "Zira" in voice.name:
                    engine.setProperty('voice', voice.id)
                    break
                    
            engine.say(text)
            engine.runAndWait()
            
            # Explicitly delete to free up SAPI5 context
            del engine
        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}")
