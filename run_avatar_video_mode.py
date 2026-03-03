"""
AI Avatar - Auto-Play Video Mode
Generates video and automatically plays it in your default video player
No "not responding" issues!
"""
import sys
import os
import asyncio
import numpy as np
import cv2
import logging
from pathlib import Path
import subprocess

# Setup path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import config
from preprocessing.source_loader import SourceLoader
from preprocessing.face_detector import FaceDetector
from llm.groq_stream import GroqStream
from tts.edge_tts_stream import EdgeTTSStream
from lipsync.wav2lip_processor import Wav2LipProcessor


class VideoModePipeline:
    """AI Avatar Pipeline - Saves video and auto-plays"""
    
    def __init__(self):
        self.source_loader = None
        self.face_detector = None
        self.llm = None
        self.tts = None
        self.wav2lip = None
        self.face_coords = None
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize all components"""
        try:
            print("\n" + "="*70)
            print("🤖 AI AVATAR - AUTO-PLAY VIDEO MODE")
            print("="*70)
            print("\n✨ No display issues - videos auto-play in your video player!\n")
            
            # Load source (image or video)
            source_path = config.SOURCE_IMAGE_PATH if config.SOURCE_TYPE == "image" else config.SOURCE_VIDEO_PATH
            logger.info(f"Loading source {config.SOURCE_TYPE}: {source_path.name}")
            self.source_loader = SourceLoader(source_path)
            
            logger.info("Detecting face...")
            self.face_detector = FaceDetector()
            first_frame = self.source_loader.get_next_frame()
            self.face_coords = self.face_detector.detect_face(first_frame)
            
            logger.info("Initializing Groq API...")
            self.llm = GroqStream(api_key=config.GROQ_API_KEY, model=config.GROQ_MODEL)
            self.llm.load_model()
            
            logger.info("Initializing Edge-TTS...")
            self.tts = EdgeTTSStream(
                voice=config.TTS_VOICE,
                rate=config.TTS_RATE,
                pitch=config.TTS_PITCH,
                chunk_duration=config.TTS_CHUNK_DURATION,
                token_buffer_size=config.TOKEN_BUFFER_SIZE
            )
            
            logger.info("Loading Wav2Lip model...")
            self.wav2lip = Wav2LipProcessor(
                checkpoint_path=str(config.WAV2LIP_CHECKPOINT),
                device=config.WAV2LIP_DEVICE,
                face_size=config.WAV2LIP_FACE_SIZE,
                fps=config.WAV2LIP_FPS,
                batch_size=config.WAV2LIP_BATCH_SIZE,
                use_fp16=config.WAV2LIP_USE_FP16,
                window_overlap=config.WAV2LIP_WINDOW_OVERLAP
            )
            self.wav2lip.load_model()
            
            print("\n✅ System ready!")
            print("="*70)
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    async def process_text(self, text: str, video_num: int = 1):
        """Process text and generate video"""
        try:
            print(f"\n💭 You: {text}")
            print("-"*70)
            print("⏳ Processing... (Generating response, TTS, and lip-sync)")
            
            # Generate response
            token_queue = asyncio.Queue()
            full_response = ""
            
            stream_task = asyncio.create_task(self.llm.stream_response(text, token_queue))
            
            while True:
                try:
                    token = await asyncio.wait_for(token_queue.get(), timeout=0.1)
                    if token is None:
                        break
                    full_response += token
                except asyncio.TimeoutError:
                    if stream_task.done():
                        while not token_queue.empty():
                            token = await token_queue.get()
                            if token:
                                full_response += token
                        break
            
            await stream_task
            print(f"🤖 AI: {full_response}")
            print("-"*70)
            
            # Generate TTS
            logger.info("Generating speech...")
            audio_bytes = await self.tts.text_to_audio(full_response)
            
            # Generate lip-sync
            logger.info("Generating lip-sync video...")
            from pydub import AudioSegment
            import io
            
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            audio_array = np.array(audio_segment.get_array_of_samples()).astype(np.int16)
            
            x, y, w, h = self.face_coords
            face_frame = self.source_loader.get_next_frame()[y:y+h, x:x+w]
            face_frame = cv2.resize(face_frame, (96, 96))
            
            synced_frames = self.wav2lip.generate_lip_sync(face_frame, audio_array)
            
            # Save to video file
            output_path = self.output_dir / f"avatar_response_{video_num}.mp4"
            logger.info(f"Saving video to {output_path}...")
            
            # Paste synced faces back to full frames
            output_frames = []
            for synced_face in synced_frames:
                synced_face_resized = cv2.resize(synced_face, (w, h))
                output_frame = self.source_loader.get_next_frame().copy()
                output_frame[y:y+h, x:x+w] = synced_face_resized
                output_frames.append(output_frame)
            
            # Get dimensions from full frame
            frame_h, frame_w = output_frames[0].shape[:2]
            
            # Try multiple codecs
            saved = False
            for codec in ['avc1', 'H264', 'XVID', 'MJPG', 'mp4v']:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    out = cv2.VideoWriter(str(output_path), fourcc, 25, (frame_w, frame_h))
                    if out.isOpened():
                        logger.info(f"Using codec: {codec}")
                        for frame in output_frames:
                            out.write(frame)
                        out.release()
                        saved = True
                        break
                    out.release()
                except:
                    continue
            
            if not saved:
                logger.warning("OpenCV failed, using imageio...")
                import imageio
                imageio.mimsave(str(output_path), output_frames, fps=25, codec='libx264', quality=8)
            
            print(f"✅ Video saved: {output_path}")
            
            # Auto-play video
            logger.info("Opening video in default player...")
            try:
                # Windows: use default video player
                os.startfile(str(output_path))
                print("🎬 Video is now playing in your video player!")
            except Exception as e:
                logger.warning(f"Could not auto-play: {e}")
                print(f"📁 Please open the video manually: {output_path}")
            
            print("-"*70)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.source_loader:
            self.source_loader.release()


async def interactive_mode():
    """Interactive text input mode"""
    pipeline = VideoModePipeline()
    
    try:
        await pipeline.initialize()
        
        print("\n📝 TEXT INPUT MODE")
        print("Type your messages and press Enter.")
        print("Videos will be saved and auto-played.")
        print("Type 'quit' or 'exit' to stop.")
        print("="*70)
        
        video_counter = 1
        
        while True:
            try:
                user_input = await asyncio.to_thread(input, "\n💬 Your message: ")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.strip():
                    await pipeline.process_text(user_input, video_counter)
                    video_counter += 1
                    
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
        
    finally:
        pipeline.cleanup()


def main():
    """Main entry point"""
    try:
        asyncio.run(interactive_mode())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
