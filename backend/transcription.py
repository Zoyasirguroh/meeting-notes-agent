"""
Audio transcription service using various methods
"""
import os
import tempfile
from typing import Optional
import speech_recognition as sr

class TranscriptionService:
    """Handle audio transcription from various sources"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    async def transcribe_audio_file(self, audio_path: str, language: str = "en-US") -> str:
        """
        Transcribe audio file using Google Speech Recognition
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: en-US)
            
        Returns:
            Transcribed text
        """
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=language)
                return text
        except sr.UnknownValueError:
            raise Exception("Could not understand audio")
        except sr.RequestError as e:
            raise Exception(f"Could not request results; {e}")
    
    async def transcribe_from_microphone(self, duration: Optional[int] = None) -> str:
        """
        Transcribe audio from microphone
        
        Args:
            duration: Recording duration in seconds (None for continuous)
            
        Returns:
            Transcribed text
        """
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source)
                
                if duration:
                    audio = self.recognizer.listen(source, timeout=duration)
                else:
                    audio = self.recognizer.listen(source)
                
                print("Transcribing...")
                text = self.recognizer.recognize_google(audio)
                return text
        except sr.UnknownValueError:
            raise Exception("Could not understand audio")
        except sr.RequestError as e:
            raise Exception(f"Could not request results; {e}")
    
    async def transcribe_whisper(self, audio_path: str) -> str:
        """
        Transcribe using OpenAI Whisper (more accurate)
        Requires: pip install openai-whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            import whisper
            
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            return result["text"]
        except ImportError:
            raise Exception("Whisper not installed. Run: pip install openai-whisper")
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {e}")
    
    async def transcribe_deepgram(self, audio_path: str) -> str:
        """
        Transcribe using Deepgram API (real-time, high accuracy)
        Requires: DEEPGRAM_API_KEY environment variable
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            from deepgram import Deepgram
            
            api_key = os.environ.get("DEEPGRAM_API_KEY")
            if not api_key:
                raise Exception("DEEPGRAM_API_KEY not set")
            
            dg_client = Deepgram(api_key)
            
            with open(audio_path, 'rb') as audio:
                source = {'buffer': audio, 'mimetype': 'audio/wav'}
                response = await dg_client.transcription.prerecorded(
                    source,
                    {'punctuate': True, 'diarize': True}
                )
            
            transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
            return transcript
        except ImportError:
            raise Exception("Deepgram SDK not installed. Run: pip install deepgram-sdk")
        except Exception as e:
            raise Exception(f"Deepgram transcription failed: {e}")


class ZoomRecorder:
    """Record and transcribe Zoom meetings"""
    
    def __init__(self):
        self.is_recording = False
        self.audio_data = []
    
    async def connect_to_zoom(self, meeting_id: str, password: Optional[str] = None):
        """
        Connect to Zoom meeting
        Note: This requires Zoom SDK or bot integration
        """
        # This would use Zoom SDK or bot API
        # For production, use: https://marketplace.zoom.us/docs/api-reference/zoom-api
        pass
    
    async def start_recording(self):
        """Start recording the meeting"""
        self.is_recording = True
        # Implementation would capture audio stream
        pass
    
    async def stop_recording(self) -> str:
        """Stop recording and return audio file path"""
        self.is_recording = False
        # Save audio to temp file and return path
        return "/tmp/meeting_audio.wav"


class GoogleMeetRecorder:
    """Record and transcribe Google Meet meetings"""
    
    def __init__(self):
        self.is_recording = False
    
    async def connect_to_meet(self, meeting_url: str):
        """
        Connect to Google Meet
        Note: This requires browser automation (Selenium/Playwright)
        """
        # Use Playwright/Selenium to join meeting and capture audio
        pass
    
    async def start_recording(self):
        """Start recording the meeting"""
        self.is_recording = True
        pass
    
    async def stop_recording(self) -> str:
        """Stop recording and return audio file path"""
        self.is_recording = False
        return "/tmp/meet_audio.wav"


# Real-time transcription using WebSocket
class RealtimeTranscriber:
    """Real-time audio transcription"""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.buffer = []
    
    async def process_audio_chunk(self, audio_chunk: bytes) -> str:
        """
        Process incoming audio chunk and return transcription
        
        Args:
            audio_chunk: Raw audio bytes
            
        Returns:
            Partial transcription
        """
        # Save chunk to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(audio_chunk)
            temp_path = f.name
        
        try:
            # Transcribe chunk
            text = await self.transcription_service.transcribe_audio_file(temp_path)
            self.buffer.append(text)
            return text
        finally:
            os.unlink(temp_path)
    
    def get_full_transcript(self) -> str:
        """Get complete transcript from all chunks"""
        return " ".join(self.buffer)
    
    def clear_buffer(self):
        """Clear transcript buffer"""
        self.buffer = []