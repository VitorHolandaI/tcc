"""
Video Gaze Analysis Engine
Uses MediaPipe Face Mesh (Solutions API) for head pose estimation,
based on the more reliable legacy implementation.
"""
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session

from config import config

mp_face_mesh = mp.solutions.face_mesh


class VideoGazeAnalyzer:
    """Analyzes videos for head pose and gaze patterns"""

    def __init__(self):
        # 3D face model — anthropometric reference (Solvay model, in mm)
        self.face_3d_model = np.array([
            (0.0, 0.0, 0.0), # Nose tip
            (-225.0, 170.0, -135.0), # Left eye inner corner
            (225.0, 170.0, -135.0), # Right eye inner corner
            (-150.0, -150.0, -125.0), # Left mouth corner
            (150.0, -150.0, -125.0), # Right mouth corner
            (0.0, -330.0, -65.0) # Chin
        ], dtype=np.float64)

        self.LANDMARK_MAPPING = {
            "nose": 1,
            "left_eye": 33,
            "right_eye": 263,
            "left_mouth": 61,
            "right_mouth": 291,
            "chin": 199
        }

    def analyze_video(
        self,
        video_path: Path,
        prova_id: int,
        aluno_id: int,
        db: Session,
        progress_callback=None
    ) -> Dict:
        """
        Analyze video with progress tracking, using the Face Mesh (Solutions) API.
        Can be resumed if interrupted.
        """
        from database import VideoAnalysis

        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.prova_id == prova_id,
            VideoAnalysis.aluno_id == aluno_id
        ).first()

        if not analysis:
            analysis = VideoAnalysis(
                prova_id=prova_id,
                aluno_id=aluno_id,
                status="processing"
            )
            db.add(analysis)
            db.commit()

        if not video_path.exists():
            analysis.status = "failed"
            analysis.error_message = f"Video not found: {video_path}"
            db.commit()
            raise FileNotFoundError(analysis.error_message)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            analysis.status = "failed"
            analysis.error_message = f"Could not open video file: {video_path}"
            db.commit()
            raise IOError(analysis.error_message)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames_raw = cap.get(cv2.CAP_PROP_FRAME_COUNT)

        if total_frames_raw <= 0 or total_frames_raw > 2_147_483_647:
            duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 if cap.get(cv2.CAP_PROP_POS_MSEC) > 0 else 0
            if duration > 0:
                total_frames = int(duration * fps)
            else:
                total_frames = 0 # Will process until video ends
        else:
            total_frames = int(total_frames_raw)

        analysis.total_frames = total_frames
        analysis.status = "processing"
        db.commit()

        start_frame = getattr(analysis, 'current_frame', 0) or 0
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            print(f" Resuming from frame {start_frame}/{total_frames}")

        counts = {
            "Forward": 0,
            "Looking Left": 0,
            "Looking Right": 0,
            "Looking Up": 0,
            "Looking Down": 0,
            "No Face": 0
        }

        timeline = []
        last_direction = None
        position_changes = 0
        current_frame = start_frame

        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:
            while True:
                if total_frames > 0 and current_frame >= total_frames:
                    break

                success, frame = cap.read()
                if not success:
                    break

                current_frame += 1

                if current_frame % config.PROCESS_EVERY_N_FRAMES != 0:
                    continue

                direction = self._analyze_frame_with_face_mesh(frame, face_mesh)
                timestamp = current_frame / fps

                counts[direction] = counts.get(direction, 0) + 1

                if last_direction and last_direction != direction and direction != "No Face":
                    position_changes += 1
                last_direction = direction

                timeline.append({
                    "frame": current_frame,
                    "timestamp": round(timestamp, 2),
                    "direction": direction
                })

                if current_frame % 500 == 0:
                    analysis.current_frame = current_frame
                    if total_frames > 0:
                        analysis.progress_percentage = (current_frame / total_frames) * 100
                        print(f" Progress: {current_frame}/{total_frames} ({analysis.progress_percentage:.1f}%)")
                    else:
                        print(f" Progress: {current_frame} frames processed (total unknown)")
                    db.commit()

                    if progress_callback:
                        progress_callback(current_frame, total_frames)

        cap.release()

        if total_frames == 0:
            total_frames = current_frame
            analysis.total_frames = total_frames

        total_analyzed = sum(counts.values())
        duration_minutes = total_frames / fps / 60 if total_frames > 0 else 0

        if total_analyzed > 0:
            analysis.percentage_forward = (counts["Forward"] / total_analyzed) * 100
            analysis.percentage_left = (counts["Looking Left"] / total_analyzed) * 100
            analysis.percentage_right = (counts["Looking Right"] / total_analyzed) * 100
            analysis.percentage_up = (counts["Looking Up"] / total_analyzed) * 100
            analysis.percentage_down = (counts["Looking Down"] / total_analyzed) * 100
            analysis.percentage_no_face = (counts["No Face"] / total_analyzed) * 100

        analysis.total_position_changes = position_changes
        analysis.position_changes_per_minute = (
            position_changes / duration_minutes if duration_minutes > 0 else 0
        )

        suspicious = self._find_suspicious_periods(timeline)
        analysis.suspicious_periods = json.dumps(suspicious)

        analysis.status = "completed"
        analysis.progress_percentage = 100.0
        analysis.current_frame = current_frame
        analysis.completed_at = datetime.now()

        db.commit()

        print(f" Analysis completed: prova={prova_id}, aluno={aluno_id}")

        return {
            "status": "completed",
            "metrics": {
                "percentage_forward": round(analysis.percentage_forward, 2),
                "percentage_left": round(analysis.percentage_left, 2),
                "percentage_right": round(analysis.percentage_right, 2),
                "percentage_up": round(analysis.percentage_up, 2),
                "percentage_down": round(analysis.percentage_down, 2),
                "percentage_no_face": round(analysis.percentage_no_face, 2),
                "position_changes_per_minute": round(analysis.position_changes_per_minute, 2),
                "total_position_changes": analysis.total_position_changes
            },
            "suspicious_periods": suspicious
        }

    def _analyze_frame_with_face_mesh(self, frame, face_mesh) -> str:
        """Analyze a single frame using the Face Mesh (Solutions) API."""
        frame = cv2.flip(frame, 1) # Mirror to match head_estimate.py convention
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False # Performance boost
        results = face_mesh.process(rgb)
        rgb.flags.writeable = True

        if not results.multi_face_landmarks:
            return "No Face"

        img_h, img_w, _ = frame.shape
        face_landmarks = results.multi_face_landmarks[0]

        landmarks_2d = {}
        for name, idx in self.LANDMARK_MAPPING.items():
            lm = face_landmarks.landmark[idx]
            landmarks_2d[name] = (int(lm.x * img_w), int(lm.y * img_h))

        if len(landmarks_2d) == 6:
            face_2d = np.array([
                landmarks_2d["nose"],
                landmarks_2d["left_eye"],
                landmarks_2d["right_eye"],
                landmarks_2d["left_mouth"],
                landmarks_2d["right_mouth"],
                landmarks_2d["chin"]
            ], dtype=np.float64)

            focal_length = float(img_w)
            cam_matrix = np.array([
                [focal_length, 0, img_w / 2],
                [0, focal_length, img_h / 2],
                [0, 0, 1]
            ], dtype=np.float64)

            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            success, rot_vec, trans_vec = cv2.solvePnP(
                self.face_3d_model, face_2d, cam_matrix, dist_matrix
            )

            if success:
                rmat, _ = cv2.Rodrigues(rot_vec)
                angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

                x, y = angles[0], angles[1]

                if y < -10:
                    return "Looking Left"
                elif y > 10:
                    return "Looking Right"
                elif x < -10:
                    return "Looking Down"
                elif x > 10:
                    return "Looking Up"
                else:
                    return "Forward"

        return "No Face"


    def _find_suspicious_periods(self, timeline: List[Dict]) -> List[Dict]:
        """Find periods looking away > 10 seconds"""
        suspicious = []
        current_period = None

        for entry in timeline:
            if entry["direction"] not in ["Forward", "No Face"]:
                if current_period is None:
                    current_period = {
                        "start": entry["timestamp"],
                        "direction": entry["direction"]
                    }
            else:
                if current_period is not None:
                    duration = entry["timestamp"] - current_period["start"]
                    if duration > 10:
                        suspicious.append({
                            "start": current_period["start"],
                            "end": entry["timestamp"],
                            "duration": round(duration, 2),
                            "direction": current_period["direction"]
                        })
                    current_period = None

        if current_period is not None and timeline:
            duration = timeline[-1]["timestamp"] - current_period["start"]
            if duration > 10:
                suspicious.append({
                    "start": current_period["start"],
                    "end": timeline[-1]["timestamp"],
                    "duration": round(duration, 2),
                    "direction": current_period["direction"]
                })

        return suspicious


analyzer = VideoGazeAnalyzer()
