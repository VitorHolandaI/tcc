import React, { useState, useRef } from 'react';
import { CheckCircle, Camera, Mic, Monitor, Maximize } from 'lucide-react';

interface PermissionWizardProps {
    onComplete: (streams: {
        screen: MediaStream;
        webcam: MediaStream;
        audio: MediaStream;
    }) => void;
    onCancel: () => void;
}

type Step = 'webcam' | 'microphone' | 'screen' | 'fullscreen' | 'complete';

const PermissionWizard: React.FC<PermissionWizardProps> = ({ onComplete, onCancel }) => {
    const [currentStep, setCurrentStep] = useState<Step>('webcam');
    const [error, setError] = useState<string>('');
    const [loading, setLoading] = useState(false);

    const webcamStreamRef = useRef<MediaStream | null>(null);
    const audioStreamRef = useRef<MediaStream | null>(null);
    const screenStreamRef = useRef<MediaStream | null>(null);

    const requestWebcam = async () => {
        try {
            setLoading(true);
            setError('');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 },
                audio: false
            });
            webcamStreamRef.current = stream;
            setCurrentStep('microphone');
        } catch (err: any) {
            setError(`Erro ao acessar webcam: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const requestMicrophone = async () => {
        try {
            setLoading(true);
            setError('');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: false,
                audio: true
            });
            audioStreamRef.current = stream;
            setCurrentStep('screen');
        } catch (err: any) {
            setError(`Erro ao acessar microfone: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const requestScreen = async () => {
        try {
            setLoading(true);
            setError('');
            const stream = await navigator.mediaDevices.getDisplayMedia({
                video: { mediaSource: 'screen' } as any,
                audio: false
            });
            screenStreamRef.current = stream;
            setCurrentStep('fullscreen');
        } catch (err: any) {
            setError(`Erro ao compartilhar tela: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const enterFullscreen = async () => {
        try {
            setLoading(true);
            setError('');
            await document.documentElement.requestFullscreen();

            if (webcamStreamRef.current && audioStreamRef.current && screenStreamRef.current) {
                onComplete({
                    webcam: webcamStreamRef.current,
                    audio: audioStreamRef.current,
                    screen: screenStreamRef.current
                });
            }
        } catch (err: any) {
            setError(`Erro ao entrar em tela cheia: ${err.message}. Tente pressionar F11.`);
        } finally {
            setLoading(false);
        }
    };

    const handleCancel = () => {
        webcamStreamRef.current?.getTracks().forEach(t => t.stop());
        audioStreamRef.current?.getTracks().forEach(t => t.stop());
        screenStreamRef.current?.getTracks().forEach(t => t.stop());
        onCancel();
    };

    const steps = [
        {
            id: 'webcam',
            title: 'Webcam',
            description: 'Permitir acesso à câmera',
            icon: Camera,
            action: requestWebcam,
            completed: currentStep !== 'webcam'
        },
        {
            id: 'microphone',
            title: 'Microfone',
            description: 'Permitir acesso ao microfone',
            icon: Mic,
            action: requestMicrophone,
            completed: currentStep !== 'webcam' && currentStep !== 'microphone'
        },
        {
            id: 'screen',
            title: 'Tela',
            description: 'Compartilhar a tela',
            icon: Monitor,
            action: requestScreen,
            completed: currentStep !== 'webcam' && currentStep !== 'microphone' && currentStep !== 'screen'
        },
        {
            id: 'fullscreen',
            title: 'Tela Cheia',
            description: 'Entrar em modo tela cheia',
            icon: Maximize,
            action: enterFullscreen,
            completed: currentStep === 'complete'
        }
    ];

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f8fafc',
            padding: '2rem'
        }}>
            <div style={{
                maxWidth: '600px',
                width: '100%',
                background: '#fff',
                borderRadius: '16px',
                padding: '3rem 2rem',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                border: '1px solid #e2e8f0'
            }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem', textAlign: 'center' }}>
                    Preparação para a Prova
                </h2>
                <p style={{ color: '#64748b', textAlign: 'center', marginBottom: '2rem' }}>
                    Complete os passos abaixo para iniciar
                </p>

                {error && (
                    <div style={{
                        background: '#fef2f2',
                        color: '#dc2626',
                        padding: '1rem',
                        borderRadius: '8px',
                        marginBottom: '1.5rem',
                        fontSize: '0.875rem'
                    }}>
                        {error}
                    </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {steps.map((step, index) => {
                        const Icon = step.icon;
                        const isActive = step.id === currentStep;
                        const isCompleted = step.completed;

                        return (
                            <div
                                key={step.id}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '1.25rem',
                                    border: `2px solid ${isCompleted ? '#bbf7d0' : isActive ? '#2563eb' : '#e2e8f0'}`,
                                    borderRadius: '12px',
                                    background: isCompleted ? '#f0fdf4' : isActive ? '#eff6ff' : '#fafafa'
                                }}
                            >
                                <div style={{
                                    width: '48px',
                                    height: '48px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: isCompleted ? '#16a34a' : isActive ? '#2563eb' : '#e2e8f0',
                                    color: isCompleted || isActive ? '#fff' : '#64748b',
                                    flexShrink: 0
                                }}>
                                    {isCompleted ? <CheckCircle size={24} /> : <Icon size={24} />}
                                </div>

                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.25rem' }}>
                                        {step.title}
                                    </div>
                                    <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                                        {step.description}
                                    </div>
                                </div>

                                {isActive && (
                                    <button
                                        onClick={step.action}
                                        disabled={loading}
                                        style={{
                                            padding: '0.75rem 1.5rem',
                                            background: '#2563eb',
                                            color: '#fff',
                                            border: 'none',
                                            borderRadius: '8px',
                                            fontWeight: 600,
                                            cursor: loading ? 'not-allowed' : 'pointer',
                                            fontSize: '0.875rem',
                                            opacity: loading ? 0.6 : 1
                                        }}
                                    >
                                        {loading ? 'Aguardando...' : 'Permitir'}
                                    </button>
                                )}

                                {isCompleted && (
                                    <span style={{ color: '#16a34a', fontWeight: 600, fontSize: '0.875rem' }}>
                                         Concluído
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>

                <button
                    onClick={handleCancel}
                    style={{
                        width: '100%',
                        marginTop: '1.5rem',
                        padding: '0.75rem',
                        background: 'transparent',
                        color: '#64748b',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontSize: '0.875rem'
                    }}
                >
                    Cancelar
                </button>
            </div>
        </div>
    );
};

export default PermissionWizard;
