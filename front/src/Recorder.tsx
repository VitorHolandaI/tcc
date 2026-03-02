// Recorder.tsx
import { useEffect, useState } from "react";
import { useReactMediaRecorder } from "react-media-recorder";

const Recorder = () => {
  const [displaySurface, setDisplaySurface] = useState<string | undefined>();

  const {
    status,
    startRecording,
    stopRecording,
    mediaBlobUrl,
    previewStream,
  } = useReactMediaRecorder({
    screen: true,
  });

  useEffect(() => {
    if (!previewStream) return;

    const track = previewStream.getVideoTracks()[0];
    if (!track) return;

    const settings = track.getSettings();
    console.log(settings); //get status of screen
    setDisplaySurface(settings.displaySurface);

    console.log("Display surface:", settings.displaySurface);
  }, [previewStream]);

  return (
    <div>
      <p>Status: {status}</p>

      {displaySurface && (
        <p>
          Selected screen type: <strong>{displaySurface}</strong>
        </p>
      )}

      <button onClick={startRecording}>Start Recording</button>
      <button onClick={stopRecording}>Stop Recording</button>

      {mediaBlobUrl && (
        <video src={mediaBlobUrl} controls autoPlay loop />
      )}
    </div>
  );
};

export default Recorder;

