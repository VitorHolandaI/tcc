"""
Video Analysis Service - Background Analysis with Progress Tracking
"""
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.video_analysis_model import VideoAnalysis


class VideoAnalysisService:
    """Analyzes videos with progress tracking and resume capability"""

    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.face_3d_model = np.array([
            (0.0, 0.0, 0.0), (-30.0, -30.0, -30.0), (30.0, -30.0, -30.0),
            (-25.0, 30.0, -30.0), (25.0, 30.0, -30.0), (0.0, 60.0, -50.0)
        ], dtype=np.float64)

    def analyze_video_with_progress(
        self,
        video_path: Path,
        prova_id: int,
        aluno_id: int,
        db: Session
    ) -> Dict:
        """
        Analyze video with progress tracking in database.
        Can be resumed if interrupted.
        """
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

        start_frame = analysis.current_frame if analysis.status == "processing" else 0

        if not video_path.exists():
            analysis.status = "failed"
            analysis.error_message = f"Video not found: {video_path}"
            db.commit()
            raise FileNotFoundError(analysis.error_message)

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        analysis.total_frames = total_frames
        analysis.status = "processing"
        db.commit()

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

        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            print(f" Resuming analysis from frame {start_frame}/{total_frames}")

        current_frame = start_frame

        while current_frame < total_frames:
            success, frame = cap.read()
            if not success:
                break

            current_frame += 1

            if current_frame % 5 != 0:
                continue

            direction = self._analyze_frame(frame)
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
                analysis.progress_percentage = (current_frame / total_frames) * 100
                db.commit()
                print(f" Progress: {current_frame}/{total_frames} ({analysis.progress_percentage:.1f}%)")

        cap.release()

        total_analyzed = sum(counts.values())
        duration_minutes = total_frames / fps / 60

        analysis.percentage_forward = (counts["Forward"] / total_analyzed * 100) if total_analyzed > 0 else 0
        analysis.percentage_left = (counts["Looking Left"] / total_analyzed * 100) if total_analyzed > 0 else 0
        analysis.percentage_right = (counts["Looking Right"] / total_analyzed * 100) if total_analyzed > 0 else 0
        analysis.percentage_up = (counts["Looking Up"] / total_analyzed * 100) if total_analyzed > 0 else 0
        analysis.percentage_down = (counts["Looking Down"] / total_analyzed * 100) if total_analyzed > 0 else 0
        analysis.percentage_no_face = (counts["No Face"] / total_analyzed * 100) if total_analyzed > 0 else 0

        analysis.total_position_changes = position_changes
        analysis.position_changes_per_minute = position_changes / duration_minutes if duration_minutes > 0 else 0

        suspicious = self._find_suspicious_periods(timeline)
        analysis.suspicious_periods = json.dumps(suspicious)

        analysis.status = "completed"
        analysis.progress_percentage = 100.0
        analysis.current_frame = total_frames
        analysis.completed_at = datetime.now()

        db.commit()

        print(f" Analysis completed for prova={prova_id}, aluno={aluno_id}")

        return {
            "status": "completed",
            "percentage_forward": round(analysis.percentage_forward, 2),
            "percentage_left": round(analysis.percentage_left, 2),
            "percentage_right": round(analysis.percentage_right, 2),
            "percentage_up": round(analysis.percentage_up, 2),
            "percentage_down": round(analysis.percentage_down, 2),
            "position_changes_per_minute": round(analysis.position_changes_per_minute, 2),
            "suspicious_periods": suspicious
        }

    def _analyze_frame(self, frame) -> str:
        """Analyze single frame"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return "No Face"

        img_h, img_w, _ = frame.shape

        for face_landmarks in results.multi_face_landmarks:
            face_2d = []

            for idx, lm in enumerate(face_landmarks.landmark):
                if idx == 1:
                    face_2d.insert(0, (int(lm.x * img_w), int(lm.y * img_h)))
                elif idx == 33:
                    face_2d.insert(1, (int(lm.x * img_w), int(lm.y * img_h)))
                elif idx == 263:
                    face_2d.insert(2, (int(lm.x * img_w), int(lm.y * img_h)))
                elif idx == 61:
                    face_2d.insert(3, (int(lm.x * img_w), int(lm.y * img_h)))
                elif idx == 291:
                    face_2d.insert(4, (int(lm.x * img_w), int(lm.y * img_h)))
                elif idx == 199:
                    face_2d.insert(5, (int(lm.x * img_w), int(lm.y * img_h)))

            if len(face_2d) == 6:
                face_2d = np.array(face_2d, dtype=np.float64)

                focal_length = img_w
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

                    if y < -15:
                        return "Looking Left"
                    elif y > 15:
                        return "Looking Right"
                    elif x < -15:
                        return "Looking Down"
                    elif x > 15:
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

        return suspicious


video_analysis_service = VideoAnalysisService()
