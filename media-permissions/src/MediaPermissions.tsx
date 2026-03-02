import React, { useState } from 'react';

type PermissionStatus = 'idle' | 'granted' | 'denied';

const MediaPermissions: React.FC = () => {
  const [camera, setCamera] = useState<PermissionStatus>('idle');
  const [microphone, setMicrophone] = useState<PermissionStatus>('idle');
  const [screen, setScreen] = useState<PermissionStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  const requestCameraAndMic = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      setCamera('granted');
      setMicrophone('granted');
      setError(null);

      console.log('Camera e microfone liberados', stream);
    } catch (err: any) {
      setCamera('denied');
      setMicrophone('denied');
      setError(err.message);
    }
  };

  const requestScreen = async () => {
    try {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true, // só funciona se o browser permitir
      });

      setScreen('granted');
      setError(null);

      console.log('Tela liberada', screenStream);
    } catch (err: any) {
      setScreen('denied');
      setError(err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Permissões de mídia</h2>

      <button onClick={requestCameraAndMic}>
        Pedir câmera e microfone
      </button>

      <br /><br />

      <button onClick={requestScreen}>
        Pedir gravação de tela
      </button>

      <hr />

      <p> Câmera: {camera}</p>
      <p> Microfone: {microphone}</p>
      <p> Tela: {screen}</p>

      {error && <p style={{ color: 'red' }}>Erro: {error}</p>}
    </div>
  );
};

export default MediaPermissions;

