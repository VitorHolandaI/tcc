"""
Storage Manager for Video Segments
Handles video recording with automatic concatenation when students exit and return
"""
from pathlib import Path
from datetime import datetime
import asyncio
import subprocess
from typing import Optional, List
import json

from config import config


class SegmentManager:
    """
    Manages video segments for each recording session.

    Features:
    - Automatic segment creation when student exits/returns
    - Concatenation of all segments into final video
    - Support for 100+ concurrent recordings
    """

    def __init__(self, prova_id: int, aluno_id: int, base_recordings_dir: Optional[Path] = None):
        self.prova_id = prova_id
        self.aluno_id = aluno_id
        self.base_filename = f"prova_{prova_id}_aluno_{aluno_id}"

        recordings_root = base_recordings_dir if base_recordings_dir else config.RECORDINGS_DIR
        self.segment_dir = recordings_root / "segments" / self.base_filename
        self.segment_dir.mkdir(exist_ok=True, parents=True)

        self.metadata_file = self.segment_dir / "metadata.json"
        self.metadata = self._load_metadata()

        self.current_segment_index = len(self.metadata.get("segments", []))
        self.current_segment_file: Optional[Path] = None
        self.current_file_handle: Optional[object] = None

    def _load_metadata(self) -> dict:
        """Load or create metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "prova_id": self.prova_id,
            "aluno_id": self.aluno_id,
            "created_at": datetime.now().isoformat(),
            "segments": [],
            "total_duration_seconds": 0,
            "total_size_bytes": 0
        }

    def _save_metadata(self):
        """Save metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def start_new_segment(self) -> Path:
        """
        Start a new recording segment.
        Called when:
        - Student starts exam
        - Student returns after exiting
        """
        segment_filename = f"segment_{self.current_segment_index:03d}.webm"
        self.current_segment_file = self.segment_dir / segment_filename

        self.current_file_handle = open(self.current_segment_file, 'wb')

        segment_info = {
            "index": self.current_segment_index,
            "filename": segment_filename,
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "size_bytes": 0
        }
        self.metadata["segments"].append(segment_info)
        self._save_metadata()

        print(f" Started segment {self.current_segment_index} for {self.base_filename}")
        return self.current_segment_file

    def write_chunk(self, data: bytes):
        """Write video chunk to current segment"""
        if not self.current_file_handle:
            raise RuntimeError("No active segment. Call start_new_segment() first.")

        self.current_file_handle.write(data)

        current_segment = self.metadata["segments"][self.current_segment_index]
        current_segment["size_bytes"] += len(data)
        self.metadata["total_size_bytes"] += len(data)

    def end_current_segment(self):
        """
        End current segment.
        Called when:
        - Student exits exam (tab focus lost)
        - Student finishes exam
        - Connection lost
        """
        if not self.current_file_handle:
            return

        self.current_file_handle.close()
        self.current_file_handle = None

        current_segment = self.metadata["segments"][self.current_segment_index]
        current_segment["ended_at"] = datetime.now().isoformat()

        size_mb = current_segment["size_bytes"] / (1024 * 1024)
        estimated_duration = size_mb * 10
        self.metadata["total_duration_seconds"] += estimated_duration

        self._save_metadata()

        print(f" Ended segment {self.current_segment_index} for {self.base_filename} ({size_mb:.2f}MB)")

        self.current_segment_index += 1

    async def concatenate_segments(self) -> Path:
        """
        Concatenate all segments into final video.
        Uses ffmpeg for efficient concatenation.

        Returns:
            Path to final concatenated video
        """
        if len(self.metadata["segments"]) == 0:
            raise ValueError("No segments to concatenate")

        if len(self.metadata["segments"]) == 1:
            segment_file = self.segment_dir / self.metadata["segments"][0]["filename"]
            final_file = config.RECORDINGS_DIR / f"{self.base_filename}.webm"

            import shutil
            shutil.copy(segment_file, final_file)

            print(f" Single segment copied to {final_file}")
            return final_file

        final_file = config.RECORDINGS_DIR / f"{self.base_filename}.webm"

        concat_list_file = self.segment_dir / "concat_list.txt"
        with open(concat_list_file, 'w') as f:
            for segment in self.metadata["segments"]:
                segment_path = self.segment_dir / segment["filename"]
                f.write(f"file '{segment_path.absolute()}'\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            "-y",
            str(final_file)
        ]

        print(f" Concatenating {len(self.metadata['segments'])} segments...")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                print(f" Concatenated to {final_file}")

                self.metadata["final_file"] = str(final_file)
                self.metadata["concatenated_at"] = datetime.now().isoformat()
                self._save_metadata()

                return final_file
            else:
                raise RuntimeError(f"ffmpeg failed: {stderr.decode()}")

        except FileNotFoundError:
            # ffmpeg not installed - fallback to simple binary concatenation
            print(" ffmpeg not found, using binary concatenation (less efficient)")
            return await self._binary_concatenate(final_file)

    async def _binary_concatenate(self, output_file: Path) -> Path:
        """
        Fallback: binary concatenation without ffmpeg.
        Less efficient but works without external dependencies.
        """
        with open(output_file, 'wb') as outfile:
            for segment in self.metadata["segments"]:
                segment_path = self.segment_dir / segment["filename"]
                with open(segment_path, 'rb') as infile:
                    outfile.write(infile.read())

        print(f" Binary concatenation completed: {output_file}")
        return output_file

    def get_segment_count(self) -> int:
        """Get number of segments"""
        return len(self.metadata["segments"])

    def get_total_size_mb(self) -> float:
        """Get total size in MB"""
        return self.metadata["total_size_bytes"] / (1024 * 1024)

    def cleanup_segments(self):
        """Delete segment files after concatenation"""
        import shutil
        if self.segment_dir.exists():
            shutil.rmtree(self.segment_dir)
            print(f" Cleaned up segments for {self.base_filename}")


class ActiveRecordingsManager:
    """
    Manages all active recording sessions.
    Thread-safe for handling 100+ concurrent students.
    """

    def __init__(self):
        self.active_recordings: dict[str, SegmentManager] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, prova_id: int, aluno_id: int) -> str:
        return f"{prova_id}_{aluno_id}"

    async def start_recording(self, prova_id: int, aluno_id: int) -> SegmentManager:
        """Start or resume recording session"""
        async with self._lock:
            key = self._get_key(prova_id, aluno_id)

            if key in self.active_recordings:
                manager = self.active_recordings[key]
                manager.start_new_segment()
            else:
                manager = SegmentManager(prova_id, aluno_id)
                manager.start_new_segment()
                self.active_recordings[key] = manager

            print(f" Active recordings: {len(self.active_recordings)}")
            return manager

    async def end_recording(self, prova_id: int, aluno_id: int, concatenate: bool = True) -> Optional[Path]:
        """End recording session and optionally concatenate"""
        async with self._lock:
            key = self._get_key(prova_id, aluno_id)

            if key not in self.active_recordings:
                return None

            manager = self.active_recordings[key]
            manager.end_current_segment()

            final_file = None
            if concatenate:
                final_file = await manager.concatenate_segments()
                # manager.cleanup_segments()

            del self.active_recordings[key]

            print(f" Active recordings: {len(self.active_recordings)}")
            return final_file

    async def pause_recording(self, prova_id: int, aluno_id: int):
        """Pause recording (student exited tab)"""
        key = self._get_key(prova_id, aluno_id)

        if key in self.active_recordings:
            manager = self.active_recordings[key]
            manager.end_current_segment()
            print(f"⏸ Paused recording for {key}")

    def get_active_count(self) -> int:
        """Get number of active recordings"""
        return len(self.active_recordings)


active_recordings = ActiveRecordingsManager()
