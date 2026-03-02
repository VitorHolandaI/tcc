"""
Audio Speaker Diarization Engine
Uses pyannote.audio for speaker detection
"""
from pyannote.audio import Pipeline
import torch
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
import os
import subprocess

from config import config

class AudioDiarizationAnalyzer:
    """Analyzes audio files for speaker diarization"""

    def __init__(self):
        self.pipeline = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize pyannote.audio pipeline (CORRIGIDO)"""
        try:
            if not config.HUGGINGFACE_TOKEN:
                print(" HUGGINGFACE_TOKEN not set. Speaker diarization may not work.")
                return
            
            os.environ["HUGGINGFACE_TOKEN"] = config.HUGGINGFACE_TOKEN

            try:
                from huggingface_hub import login
                login(token=config.HUGGINGFACE_TOKEN)
            except ImportError:
                pass
            except Exception as e:
                print(f" HuggingFace login warning: {e}")

            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=config.HUGGINGFACE_TOKEN
            )

            if config.USE_GPU and torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                print(" Using GPU for audio analysis")
            else:
                print("ℹ Using CPU for audio analysis")

        except Exception as e:
            print(f" Failed to initialize pyannote pipeline: {e}")
            self.pipeline = None

    def analyze_audio(
        self,
        audio_path: Path,
        prova_id: int,
        aluno_id: int,
        db: Session
    ) -> Dict:
        """
        Analyze audio for speaker diarization.
        """
        from database import AudioAnalysis
        
        analysis = db.query(AudioAnalysis).filter(
            AudioAnalysis.prova_id == prova_id,
            AudioAnalysis.aluno_id == aluno_id
        ).first()

        if not analysis:
            analysis = AudioAnalysis(
                prova_id=prova_id,
                aluno_id=aluno_id,
                status="processing"
            )
            db.add(analysis)
            db.commit()

        if not audio_path.exists():
            analysis.status = "failed"
            analysis.error_message = f"Audio file not found: {audio_path}"
            db.commit()
            raise FileNotFoundError(analysis.error_message)

        if not self.pipeline:
            analysis.status = "failed"
            analysis.error_message = "Pyannote pipeline not initialized. Check HUGGINGFACE_TOKEN."
            db.commit()
            raise RuntimeError(analysis.error_message)

        converted_audio_path = None
        try:
            analysis.status = "processing"
            db.commit()
            
            print(f" Starting audio analysis: prova={prova_id}, aluno={aluno_id}")

            converted_audio_path = audio_path.with_name(f"{audio_path.stem}_converted.wav")

            command = ["ffmpeg", "-i", str(audio_path), "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(converted_audio_path)]
            
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                print(f" Successfully converted '{audio_path}' to '{converted_audio_path}'")
            except subprocess.CalledProcessError as e:
                error_message = f"ffmpeg conversion failed: {e.stderr}"
                analysis.status = "failed"
                analysis.error_message = error_message
                db.commit()
                raise RuntimeError(error_message) from e

            diarization = self.pipeline(str(converted_audio_path))

            speaker_timeline = []
            speakers_set = set()
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_timeline.append({
                    "start": float(turn.start), "end": float(turn.end),
                    "duration": float(turn.end - turn.start), "speaker": speaker
                })
                speakers_set.add(speaker)

            speaker_timeline.sort(key=lambda x: x["start"])

            total_speakers = len(speakers_set)
            total_duration = speaker_timeline[-1]["end"] if speaker_timeline else 0.0
            multiple_speaker_periods = self._find_overlapping_periods(speaker_timeline)
            total_speech_time = sum(seg["duration"] for seg in speaker_timeline)
            silence_percentage = ((total_duration - total_speech_time) / total_duration * 100) if total_duration > 0 else 0

            analysis.total_speakers = total_speakers
            analysis.has_multiple_speakers = total_speakers > 1
            analysis.speaker_timeline = json.dumps(speaker_timeline)
            analysis.multiple_speaker_periods = json.dumps(multiple_speaker_periods)
            analysis.total_duration_seconds = total_duration
            analysis.silence_percentage = silence_percentage
            analysis.status = "completed"
            analysis.completed_at = datetime.now()
            db.commit()

            print(f" Audio analysis completed: {total_speakers} speaker(s) detected")

            return {
                "status": "completed",
                "total_speakers": total_speakers,
                "has_multiple_speakers": total_speakers > 1,
                "speaker_timeline": speaker_timeline,
                "multiple_speaker_periods": multiple_speaker_periods,
                "total_duration_seconds": total_duration,
                "silence_percentage": round(silence_percentage, 2)
            }
        except Exception as e:
            print(f" ERROR DURING PIPELINE EXECUTION: {type(e).__name__}: {e}")
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
            raise
        finally:
            if converted_audio_path and converted_audio_path.exists():
                os.remove(converted_audio_path)
                print(f" Cleaned up temporary file: {converted_audio_path}")

    def _find_overlapping_periods(self, timeline: List[Dict]) -> List[Dict]:
        """
        Find periods where multiple speakers are talking simultaneously.
        """
        overlapping = []
        for i in range(len(timeline) - 1):
            current, next_seg = timeline[i], timeline[i + 1]
            if next_seg["start"] - current["end"] < 0.5 and current["speaker"] != next_seg["speaker"]:
                overlapping.append({
                    "start": current["start"], "end": next_seg["end"],
                    "duration": next_seg["end"] - current["start"],
                    "speakers": [current["speaker"], next_seg["speaker"]]
                })
        return overlapping

analyzer = AudioDiarizationAnalyzer()
