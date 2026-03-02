import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, ArrowRight, Play, CheckCircle, Loader2, AlertCircle, Send } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../services/apiConfig';
import Editor from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import { createRunner, type CodeRunner } from '../runners';
import { registerAutocomplete } from '../autocomplete'
import { submissaoService, type SubmissaoResponse } from '../services/SubmissaoService';
import { useKeystrokeCapture } from '../hooks/useKeystrokeCapture';
import PermissionWizard from './PermissionWizard';
import '../css/TextBox.css';

interface Questao {
    id: number;
    prova_id: number;
    titulo: string;
    descricao: string;
    exemplo_input1: string;
    exemplo_output1: string;
    exemplo_input2: string | null;
    exemplo_output2: string | null;
    peso: number;
}

interface Prova {
    id: number;
    titulo: string;
    descricao: string | null;
    data_aplicacao: string;
    linguagem: string;
    professor_id: number;
}

const MONACO_LANGUAGE_MAP: Record<string, string> = {
    python: 'python',
    javascript: 'javascript',
    js: 'javascript',
    java: 'java',
    c: 'c',
    cpp: 'cpp',
    'c++': 'cpp',
    csharp: 'csharp',
    'c#': 'csharp',
    typescript: 'typescript',
    go: 'go',
    rust: 'rust',
    ruby: 'ruby',
    php: 'php',
};

function getMonacoLanguage(linguagem: string): string {
    return MONACO_LANGUAGE_MAP[linguagem.toLowerCase().trim()] || 'plaintext';
}

const TextBox: React.FC = () => {
    const { prova_id } = useParams<{ prova_id: string }>();
    const { getIdToken } = useAuth();
    const navigate = useNavigate();

    const editorRef = useRef<any>(null);

    const { keystrokeEvents, clearEvents } = useKeystrokeCapture(editorRef.current);

    const runnerRef = useRef<CodeRunner | null>(null);

    const [prova, setProva] = useState<Prova | null>(null);
    const [questoes, setQuestoes] = useState<Questao[]>([]);
    const [submissoes, setSubmissoes] = useState<Record<number, string>>({}); // questao_id -> codigo_submetido
    const [currentSubmissao, setCurrentSubmissao] = useState<SubmissaoResponse | null>(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
    const [keystrokeSubmissaoId, setKeystrokeSubmissaoId] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');
    const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error' | 'idle'>('idle');
    const [executionResult, setExecutionResult] = useState<string | null>(null);
    const [isExecuting, setIsExecuting] = useState(false);
    const [runnerReady, setRunnerReady] = useState(false);
    const [isProvaFinalizada, setIsProvaFinalizada] = useState(false);

    const [saidasCount, setSaidasCount] = useState(0);
    const [maxSaidas, setMaxSaidas] = useState(3);
    const [showExitWarning, setShowExitWarning] = useState(false);

    const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const [isRecording, setIsRecording] = useState(false);
    const [recordingStatus, setRecordingStatus] = useState<string>('');

    const screenRecorderRef = useRef<MediaRecorder | null>(null);
    const screenSocketRef = useRef<WebSocket | null>(null);
    const screenStreamRef = useRef<MediaStream | null>(null);

    const webcamRecorderRef = useRef<MediaRecorder | null>(null);
    const webcamSocketRef = useRef<WebSocket | null>(null);
    const webcamStreamRef = useRef<MediaStream | null>(null);

    const audioRecorderRef = useRef<MediaRecorder | null>(null);
    const audioSocketRef = useRef<WebSocket | null>(null);
    const audioStreamRef = useRef<MediaStream | null>(null);

    const [permissionsGranted, setPermissionsGranted] = useState(false);
    const grantedWebcamStreamRef = useRef<MediaStream | null>(null);
    const grantedAudioStreamRef = useRef<MediaStream | null>(null);
    const grantedScreenStreamRef = useRef<MediaStream | null>(null);

    const handlePermissionsComplete = (streams: { screen: MediaStream; webcam: MediaStream; audio: MediaStream }) => {
        grantedScreenStreamRef.current = streams.screen;
        grantedWebcamStreamRef.current = streams.webcam;
        grantedAudioStreamRef.current = streams.audio;
        setPermissionsGranted(true);
    };

    const handlePermissionsCancel = () => {
        navigate('/dashboard/aluno');
    };

    // Ref guard to prevent React Strict Mode duplicate calls
    const provaInitializedRef = useRef(false);

    useEffect(() => {
        if (provaInitializedRef.current) return;

        const initProva = async () => {
            if (!prova_id) return;

            provaInitializedRef.current = true;

            try {
                setLoading(true);
                setError('');
                const token = await getIdToken();

                if (!token) {
                    setError('Erro de autenticação. Faça login novamente.');
                    setLoading(false);
                    return;
                }

                const headers = { Authorization: `Bearer ${token}` };

                const provaResp = await axios.get<Prova>(`${API_BASE_URL}/provas/${prova_id}`, { headers });
                setProva(provaResp.data);

                const questoesResp = await axios.get<Questao[]>(`${API_BASE_URL}/questoes/prova/${prova_id}`, { headers });
                const fetchedQuestoes = questoesResp.data;
                setQuestoes(fetchedQuestoes);

                const submissaoPromises = fetchedQuestoes.map(q => submissaoService.get(q.id, token));
                const submissaoResults = await Promise.all(submissaoPromises);

                const submissoesMap: Record<number, string> = {};
                let provaFinalizada = false;

                submissaoResults.forEach((submissao, index) => {
                    if (submissao) {
                        const questaoId = fetchedQuestoes[index].id;
                        submissoesMap[questaoId] = submissao.codigo_submetido;

                        if (submissao.finalizada) {
                            provaFinalizada = true;
                        }

                        // Guardar ID da primeira submissão para keystroke tracking
                        if (index === 0) {
                            setKeystrokeSubmissaoId(submissao.id);
                        }
                    }
                });

                setSubmissoes(submissoesMap);
                setIsProvaFinalizada(provaFinalizada);

                // Criar submissões vazias se não existirem (para professor ver que aluno iniciou)
                const questoesSemSubmissao = fetchedQuestoes.filter(
                    q => !submissoesMap[q.id]
                );

                if (questoesSemSubmissao.length > 0) {
                    const submissoesVazias = questoesSemSubmissao.map(q => ({
                        prova_id: parseInt(prova_id, 10),
                        questao_id: q.id,
                        codigo_submetido: ''
                    }));

                    try {
                        const newSubmissions = await Promise.all(
                            submissoesVazias.map(sub => submissaoService.enviar(sub, token))
                        );

                        // Se o keystrokeSubmissaoId ainda não foi setado, pega da primeira nova submissão
                        if (!keystrokeSubmissaoId && newSubmissions.length > 0) {
                            setKeystrokeSubmissaoId(newSubmissions[0].id);
                        }
                        
                        console.log(' Submissões vazias criadas para marcar início da prova');
                    } catch (err) {
                        console.error('Erro ao criar submissões vazias:', err);
                    }
                }

            } catch (err: any) {
                console.error('Erro ao carregar prova:', err);
                setError(err.response?.data?.detail || 'Erro ao carregar prova');
            } finally {
                setLoading(false);
            }
        };

        initProva();
    }, [prova_id, getIdToken]);

    useEffect(() => {
        const fetchMonitoringStatus = async () => {
            if (!prova_id) return;
            try {
                const token = await getIdToken();
                if (!token) return;

                const response = await axios.get(
                    `${API_BASE_URL}/provas/${prova_id}/status-monitoramento`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                if (response.data.invalidada) {
                    setError('Esta prova foi invalidada por excesso de saídas.');
                    setIsProvaFinalizada(true);
                    return;
                }

                setSaidasCount(response.data.numero_saidas);
                setMaxSaidas(response.data.max_saidas);
            } catch (err: any) {
                // Silently fail if monitoring not configured
                console.log('Monitoring status not available:', err.response?.status);
            }
        };

        if (prova_id) {
            fetchMonitoringStatus();
        }
    }, [prova_id, getIdToken]);

    useEffect(() => {
        if (!prova) return;

        const initRunner = async () => {
            try {
                const runner = createRunner(prova.linguagem, getIdToken);
                await runner.init();
                runnerRef.current = runner;
                setRunnerReady(true);
                console.log(` Runner [${prova.linguagem}] pronto`);
            } catch (err) {
                console.error('Erro ao carregar runner:', err);
                setExecutionResult(' Falha ao carregar ambiente de execução. Recarregue a página.');
            }
        };

        initRunner();

        return () => {
            runnerRef.current?.dispose();
            runnerRef.current = null;
            setRunnerReady(false);
        };
    }, [prova?.linguagem]);

    useEffect(() => {
        const handler = (e: BeforeUnloadEvent) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, []);

    useEffect(() => {
        if (!prova_id || isProvaFinalizada) return;

        let visibilityTimer: NodeJS.Timeout;

        const handleVisibilityChange = async () => {
            if (document.visibilityState === 'hidden') {
                visibilityTimer = setTimeout(async () => {
                    try {
                        const token = await getIdToken();
                        if (!token) return;

                        const response = await axios.post(
                            `${API_BASE_URL}/provas/${prova_id}/registrar-saida`,
                            {},
                            { headers: { Authorization: `Bearer ${token}` } }
                        );

                        setSaidasCount(response.data.numero_saidas);

                        if (response.data.invalidada) {
                            alert(`PROVA INVALIDADA! Você saiu da página ${response.data.numero_saidas} vezes (máximo: ${response.data.max_saidas}). Sua prova foi encerrada.`);
                            navigate('/dashboard/aluno');
                        } else {
                            setShowExitWarning(true);
                        }
                    } catch (err: any) {
                        console.error('Erro ao registrar saída:', err);
                    }
                }, 3000);
            } else if (document.visibilityState === 'visible') {
                clearTimeout(visibilityTimer);
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            clearTimeout(visibilityTimer);
        };
    }, [prova_id, navigate, getIdToken, isProvaFinalizada]);

    // Refs to track recording state across effect re-runs
    const recordingActiveRef = useRef(false);
    const startingRecordingRef = useRef(false); // True while requesting permissions

    const stopAllRecordings = useCallback(() => {
        // Parar screen recording
        if (screenRecorderRef.current && screenRecorderRef.current.state !== 'inactive') {
            screenRecorderRef.current.stop();
        }
        if (screenStreamRef.current) {
            screenStreamRef.current.getTracks().forEach(track => track.stop());
            screenStreamRef.current = null;
        }
        if (screenSocketRef.current) {
            screenSocketRef.current.close();
            screenSocketRef.current = null;
        }

        // Parar webcam
        if (webcamRecorderRef.current && webcamRecorderRef.current.state !== 'inactive') {
            webcamRecorderRef.current.stop();
        }
        if (webcamStreamRef.current) {
            webcamStreamRef.current.getTracks().forEach(track => track.stop());
            webcamStreamRef.current = null;
        }
        if (webcamSocketRef.current) {
            webcamSocketRef.current.close();
            webcamSocketRef.current = null;
        }

        // Parar audio
        if (audioRecorderRef.current && audioRecorderRef.current.state !== 'inactive') {
            audioRecorderRef.current.stop();
        }
        if (audioStreamRef.current) {
            audioStreamRef.current.getTracks().forEach(track => track.stop());
            audioStreamRef.current = null;
        }
        if (audioSocketRef.current) {
            audioSocketRef.current.close();
            audioSocketRef.current = null;
        }

        screenRecorderRef.current = null;
        webcamRecorderRef.current = null;
        audioRecorderRef.current = null;
        recordingActiveRef.current = false;
        setIsRecording(false);
        setRecordingStatus('Gravações finalizadas');

        console.log(' All recordings stopped');
    }, []);

    useEffect(() => {
        if (!prova_id || isProvaFinalizada || !permissionsGranted) {
            return;
        }

        if (recordingActiveRef.current) {
            return;
        }

        if (!grantedScreenStreamRef.current || !grantedWebcamStreamRef.current || !grantedAudioStreamRef.current) {
            console.error('Missing pre-granted streams');
            return;
        }

        recordingActiveRef.current = true;

        let cancelled = false;

        const startAllRecordings = async () => {
            try {
                setRecordingStatus('Conectando...');

                const screenStream = grantedScreenStreamRef.current!;
                const webcamStream = grantedWebcamStreamRef.current!;
                const audioStream = grantedAudioStreamRef.current!;

                screenStreamRef.current = screenStream;
                webcamStreamRef.current = webcamStream;
                audioStreamRef.current = audioStream;

                const token = await getIdToken();
                if (!token || cancelled) {
                    setRecordingStatus('Erro: Token não disponível');
                    stopAllRecordings();
                    return;
                }

                const { RECORDING_SERVICE_URL, WEBCAM_SERVICE_URL, AUDIO_SERVICE_URL } = await import('../services/apiConfig');

                // Helper: converte URL (absoluta ou path relativo) para WebSocket
                const toWsUrl = (base: string, path: string): string => {
                    if (base.startsWith('http')) {
                        return `${base.replace('http', 'ws')}${path}`;
                    }
                    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    return `${wsProtocol}//${window.location.host}${base}${path}`;
                };

                const screenSocket = new WebSocket(
                    toWsUrl(RECORDING_SERVICE_URL, `/ws/${prova_id}`)
                );
                screenSocketRef.current = screenSocket;

                const webcamSocket = new WebSocket(
                    toWsUrl(WEBCAM_SERVICE_URL, `/ws/${prova_id}`)
                );
                webcamSocketRef.current = webcamSocket;

                const audioSocket = new WebSocket(
                    toWsUrl(AUDIO_SERVICE_URL, `/ws/${prova_id}`)
                );
                audioSocketRef.current = audioSocket;

                screenSocket.onopen = async () => {
                    screenSocket.send(JSON.stringify({
                        type: 'auth',
                        token
                    }));

                    screenSocket.onmessage = (event) => {
                        const data = JSON.parse(event.data);

                        if (data.error) {
                            console.error('Screen recording error:', data.error);
                            return;
                        }

                        if (data.status === 'ready' || data.status === 'authenticated') {
                            const screenRecorder = new MediaRecorder(screenStream, {
                                mimeType: 'video/webm; codecs=vp8'
                            });
                            screenRecorderRef.current = screenRecorder;

                            screenRecorder.ondataavailable = (event) => {
                                if (event.data.size > 0 && screenSocket.readyState === WebSocket.OPEN) {
                                    screenSocket.send(event.data);
                                }
                            };

                            screenRecorder.start(1000);
                            console.log(' Screen recording started');
                        }
                    };
                };

                webcamSocket.onopen = async () => {
                    webcamSocket.send(JSON.stringify({
                        type: 'auth',
                        token
                    }));

                    webcamSocket.onmessage = (event) => {
                        const data = JSON.parse(event.data);

                        if (data.error) {
                            console.error('Webcam error:', data.error);
                            return;
                        }

                        if (data.status === 'ready' || data.status === 'authenticated') {
                            const webcamRecorder = new MediaRecorder(webcamStream, {
                                mimeType: 'video/webm; codecs=vp8'
                            });
                            webcamRecorderRef.current = webcamRecorder;

                            webcamRecorder.ondataavailable = (event) => {
                                if (event.data.size > 0 && webcamSocket.readyState === WebSocket.OPEN) {
                                    webcamSocket.send(event.data);
                                }
                            };

                            webcamRecorder.start(1000);
                            console.log(' Webcam recording started');
                        }
                    };
                };

                audioSocket.onopen = async () => {
                    audioSocket.send(JSON.stringify({
                        type: 'auth',
                        token
                    }));

                    audioSocket.onmessage = (event) => {
                        const data = JSON.parse(event.data);

                        if (data.error) {
                            console.error('Audio error:', data.error);
                            return;
                        }

                        if (data.status === 'ready' || data.status === 'authenticated') {
                            const audioRecorder = new MediaRecorder(audioStream, {
                                mimeType: 'audio/webm; codecs=opus'
                            });
                            audioRecorderRef.current = audioRecorder;

                            audioRecorder.ondataavailable = (event) => {
                                if (event.data.size > 0 && audioSocket.readyState === WebSocket.OPEN) {
                                    audioSocket.send(event.data);
                                }
                            };

                            audioRecorder.start(1000);
                            console.log(' Audio recording started');
                        }
                    };
                };

                screenStream.getVideoTracks()[0].onended = () => {
                    // Don't auto-restart - just warn. Auto-restart causes permission loops.
                    console.warn('Screen sharing ended by user');
                    setRecordingStatus(' Compartilhamento de tela encerrado');
                };

                startingRecordingRef.current = false;
                recordingActiveRef.current = true; // Now fully active
                setIsRecording(true);
                setRecordingStatus(' Gravando: Tela + Webcam + Áudio');

            } catch (err: any) {
                console.error('Erro ao iniciar gravações:', err);
                startingRecordingRef.current = false;

                if (err.name === 'NotAllowedError') {
                    // Only navigate away on the initial attempt, not on Strict Mode re-runs
                    if (!cancelled) {
                        alert(' Você precisa permitir o acesso à tela, webcam e microfone para fazer a prova.');
                        navigate('/dashboard/aluno');
                    }
                } else {
                    setRecordingStatus(`Erro: ${err.message}`);
                }

                stopAllRecordings();
            }
        };

        startAllRecordings();

        return () => {
            // Only cancel if we're in the middle of starting (not yet successful)
            // This prevents cancelling when fullscreen briefly exits for permission dialogs
            if (startingRecordingRef.current) {
                cancelled = true;
                startingRecordingRef.current = false;
            }
        };
    }, [prova_id, isProvaFinalizada, permissionsGranted, getIdToken, navigate, stopAllRecordings]);

    // Cleanup recordings on actual unmount (not Strict Mode)
    useEffect(() => {
        return () => {
            stopAllRecordings();
        };
    }, [stopAllRecordings]);

    useEffect(() => {
        if (!keystrokeSubmissaoId || keystrokeEvents.length === 0 || isProvaFinalizada) return;

        const intervalId = setInterval(async () => {
            try {
                const token = await getIdToken();
                if (!token) return;

                await axios.put(
                    `${API_BASE_URL}/submissoes/keystroke/${keystrokeSubmissaoId}`,
                    keystrokeEvents,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                clearEvents();
            } catch (error) {
                console.error('Erro ao salvar keystroke dynamics:', error);
            }
        }, 120000); // 2 minutos

        return () => clearInterval(intervalId);
    }, [keystrokeSubmissaoId, keystrokeEvents, getIdToken, clearEvents, isProvaFinalizada]);

    const saveSubmission = async (questaoId: number, code: string) => {
        if (!prova_id) return;
        try {
            setSaveStatus('saving');
            const token = await getIdToken();
            if (!token) throw new Error("Token not available");

            await submissaoService.enviar(
                {
                    prova_id: parseInt(prova_id, 10),
                    questao_id: questaoId,
                    codigo_submetido: code
                },
                token
            );
            
            setSaveStatus('saved');
            setTimeout(() => setSaveStatus('idle'), 2000);
        } catch (err) {
            console.error('Erro ao salvar submissão:', err);
            setSaveStatus('error');
            setTimeout(() => setSaveStatus('idle'), 3000);
        }
    };

    const debouncedSave = useCallback((questaoId: number, code: string) => {
        if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
        saveTimeoutRef.current = setTimeout(() => saveSubmission(questaoId, code), 2000);
    }, []);

    const handleCodeChange = (newCode: string = '') => {
        const questao = getCurrentQuestao();
        if (!questao) return;

        setSubmissoes(prev => ({
            ...prev,
            [questao.id]: newCode,
        }));
        debouncedSave(questao.id, newCode);
    };

    const getCurrentQuestao = () => questoes[currentQuestionIndex];
    const getCurrentSubmissionCode = () => {
        const q = getCurrentQuestao();
        return q ? submissoes[q.id] || '' : '';
    };

    const goToQuestion = async (index: number) => {
        if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
        
        const currentQuestao = getCurrentQuestao();
        const currentCode = getCurrentSubmissionCode();
        if (currentQuestao && currentCode) {
            await saveSubmission(currentQuestao.id, currentCode);
        }

        setCurrentQuestionIndex(index);
        setExecutionResult(null);
    };

    const goToNextQuestion = () => {
        if (currentQuestionIndex < questoes.length - 1) goToQuestion(currentQuestionIndex + 1);
    };

    const goToPreviousQuestion = () => {
        if (currentQuestionIndex > 0) goToQuestion(currentQuestionIndex - 1);
    };

    const executeCode = async () => {
        const code = getCurrentSubmissionCode();
        if (!code) return;

        const runner = runnerRef.current;
        if (!runner || !runner.isReady()) {
            setExecutionResult(' Ambiente ainda carregando... Tente novamente.');
            return;
        }

        try {
            setIsExecuting(true);
            setExecutionResult(' Executando...');

            const result = await runner.execute(code);

            const parts: string[] = [];
            if (result.stdout) parts.push(` Saída:\n${result.stdout}`);
            if (result.stderr) parts.push(` Stderr:\n${result.stderr}`);
            if (result.error) parts.push(` Erro:\n${result.error}`);
            if (result.success && !result.stdout && !result.stderr) {
                parts.push(' Código executado com sucesso (sem saída)');
            }

            setExecutionResult(parts.join('\n\n'));
        } catch (err: any) {
            setExecutionResult(` Erro inesperado: ${err.message || String(err)}`);
        } finally {
            setIsExecuting(false);
        }
    };

    const submitCode = async () => {
        const questao = getCurrentQuestao();
        const code = getCurrentSubmissionCode();
        if (questao && code) {
            if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
            await saveSubmission(questao.id, code);
        }
    };

    const finishProva = async () => {
        if (!prova_id) return;

        const confirmed = window.confirm(
            'Tem certeza que deseja finalizar a prova? Você não poderá mais editar suas respostas.'
        );
        if (!confirmed) return;

        try {
            setSaveStatus('saving');

            const token = await getIdToken();
            if (!token) throw new Error("Token not available");

            // Enviar keystroke dynamics final antes de finalizar
            if (keystrokeEvents.length > 0 && keystrokeSubmissaoId) {
                try {
                    await axios.put(
                        `${API_BASE_URL}/submissoes/keystroke/${keystrokeSubmissaoId}`,
                        keystrokeEvents,
                        { headers: { Authorization: `Bearer ${token}` } }
                    );
                    } catch (error) {
                    console.error('Erro ao salvar keystroke dynamics final:', error);
                }
            }

            const submissoesToFinalize = questoes.map(questao => ({
                prova_id: parseInt(prova_id, 10),
                questao_id: questao.id,
                codigo_submetido: submissoes[questao.id] || ''
            }));

            await submissaoService.finalizar(
                parseInt(prova_id, 10),
                submissoesToFinalize,
                token
            );

            setSaveStatus('saved');
            alert('Prova finalizada com sucesso!');
            navigate('/dashboard/aluno');
        } catch (err: any) {
            console.error('Erro ao finalizar prova:', err);
            setSaveStatus('error');
            alert(err.response?.data?.detail || 'Erro ao finalizar prova. Tente novamente.');
        }
    };

    const handleEditorDidMount = (editor: any, monacoInstance: typeof monaco) => {
        editorRef.current = editor;

        if (prova) {
            registerAutocomplete(monacoInstance, prova.linguagem);
        }
    };

    if (loading) {
        return (
            <div className="tb-center-screen">
                <Loader2 className="animate-spin text-purple-600 mb-4" size={48} />
                <p className="text-gray-700 font-medium">Carregando prova...</p>
            </div>
        );
    }

    if (!permissionsGranted) {
        return (
            <PermissionWizard
                onComplete={handlePermissionsComplete}
                onCancel={handlePermissionsCancel}
            />
        );
    }

    if (error) {
        return (
            <div className="tb-center-screen">
                <div className="tb-question-card" style={{ maxWidth: '400px', textAlign: 'center' }}>
                    <AlertCircle className="text-red-600 mx-auto mb-4" size={48} />
                    <h2 className="text-xl font-bold text-gray-900 mb-2">Erro</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button
                        onClick={() => navigate('/dashboard/aluno')}
                        className="tb-btn-nav"
                        style={{ justifyContent: 'center', width: '100%' }}
                    >
                        Voltar ao Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const currentQuestao = getCurrentQuestao();
    const currentCode = getCurrentSubmissionCode();

    if (!currentQuestao) {
        return (
            <div className="tb-center-screen">
                <p className="text-gray-700">Nenhuma questão encontrada</p>
            </div>
        );
    }

    const monacoLang = prova ? getMonacoLanguage(prova.linguagem) : 'plaintext';

    return (
        <div className="tb-container">
            <header className="tb-header">
                <div className="tb-header-info">
                    <div className="tb-header-title">
                        <h1>{prova?.titulo}</h1>
                    </div>
                    <div className="tb-header-meta">
                        {prova?.linguagem} • Questão {currentQuestionIndex + 1} de {questoes.length}

                        {isRecording && (
                            <span className="recording-badge">
                                 Gravando
                            </span>
                        )}

                        {saidasCount > 0 && (
                            <span className={`exit-badge ${saidasCount >= maxSaidas - 1 ? 'danger' : 'warning'}`}>
                                 Saídas: {saidasCount}/{maxSaidas}
                            </span>
                        )}
                    </div>
                </div>

                <div className="tb-header-actions">
                    <div className="tb-save-status">
                        {isProvaFinalizada
                            ? <><CheckCircle size={14} className="text-green-600" /> Prova Finalizada</>
                            : saveStatus === 'saving'
                                ? <><Loader2 className="animate-spin" size={14} /> Salvando...</>
                                : saveStatus === 'saved'
                                    ? <><CheckCircle size={14} className="text-green-600" /> Salvo</>
                                    : saveStatus === 'error'
                                        ? <><AlertCircle size={14} className="text-red-600" /> Erro</>
                                        : null
                        }
                    </div>

                    <button
                        onClick={finishProva}
                        className="tb-btn-finish"
                        disabled={isProvaFinalizada}
                        style={{ opacity: isProvaFinalizada ? 0.5 : 1, cursor: isProvaFinalizada ? 'not-allowed' : 'pointer' }}
                    >
                        <CheckCircle size={16} />
                        {isProvaFinalizada ? 'Prova Finalizada' : 'Finalizar Prova'}
                    </button>
                </div>
            </header>

            <main className="tb-main">
                <div className="tb-left-panel">
                    <div className="tb-editor-wrapper">
                        <Editor
                            height="100%"
                            defaultLanguage={monacoLang}
                            language={monacoLang}
                            theme="vs-dark"
                            value={currentCode}
                            onChange={(value) => handleCodeChange(value)}
                            onMount={handleEditorDidMount}
                            options={{
                                readOnly: isProvaFinalizada,
                                minimap: { enabled: false },
                                fontSize: 14,
                                automaticLayout: true,
                                suggestOnTriggerCharacters: true,
                                quickSuggestions: { other: true, comments: false, strings: false },
                                quickSuggestionsDelay: 100,
                                acceptSuggestionOnEnter: 'on',
                                tabCompletion: 'on',
                                wordBasedSuggestions: 'off',
                                parameterHints: { enabled: true },
                                suggest: {
                                    showMethods: true,
                                    showFunctions: true,
                                    showConstructors: true,
                                    showFields: true,
                                    showVariables: true,
                                    showClasses: true,
                                    showKeywords: true,
                                    showWords: false,
                                },
                                tabSize: 4,
                                insertSpaces: true,
                                scrollBeyondLastLine: false,
                                padding: { top: 8 },
                            }}
                        />

                        <div className="tb-editor-toolbar">
                            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                                {isProvaFinalizada
                                    ? <> Prova finalizada - apenas leitura</>
                                    : runnerReady
                                        ? <> {prova?.linguagem} pronto • <b>Ctrl+Space</b> autocomplete</>
                                        : <> Carregando {prova?.linguagem}... • <b>Ctrl+Space</b> autocomplete</>
                                }
                            </span>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button
                                    className="tb-btn-run"
                                    onClick={executeCode}
                                    disabled={isExecuting || !runnerReady || isProvaFinalizada}
                                >
                                    {isExecuting
                                        ? <><Loader2 className="animate-spin" size={16} /> Executando...</>
                                        : <><Play size={16} /> Executar</>
                                    }
                                </button>
                                <button
                                    className="tb-btn-submit"
                                    onClick={submitCode}
                                    disabled={saveStatus === 'saving' || isProvaFinalizada}
                                >
                                    {saveStatus === 'saving'
                                        ? <><Loader2 className="animate-spin" size={16} /> Salvando...</>
                                        : <><Send size={16} /> Submeter</>
                                    }
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="tb-console">
                        <span className="tb-console-title">Console / Resultado</span>
                        <div className="tb-console-content">
                            {isExecuting
                                ? ' Executando...'
                                : executionResult || 'O resultado da execução aparecerá aqui...'
                            }
                        </div>
                    </div>
                </div>

                <div className="tb-right-panel">
                    <div className="tb-question-card">
                        <div className="tb-question-header">
                            <h2 className="tb-question-title">{currentQuestao.titulo}</h2>
                            <span className="tb-points-badge">{currentQuestao.peso} pts</span>
                        </div>

                        <div className="tb-question-desc">{currentQuestao.descricao}</div>

                        <div className="tb-example-box">
                            <span className="tb-example-title">Exemplo 1</span>
                            <div>
                                <small style={{ color: '#64748b' }}>Input:</small>
                                <div className="tb-code-block">{currentQuestao.exemplo_input1}</div>
                            </div>
                            <div>
                                <small style={{ color: '#64748b' }}>Output:</small>
                                <div className="tb-code-block">{currentQuestao.exemplo_output1}</div>
                            </div>
                        </div>

                        {currentQuestao.exemplo_input2 && (
                            <div className="tb-example-box" style={{ borderLeftColor: '#94a3b8' }}>
                                <span className="tb-example-title">Exemplo 2</span>
                                <div>
                                    <small style={{ color: '#64748b' }}>Input:</small>
                                    <div className="tb-code-block">{currentQuestao.exemplo_input2}</div>
                                </div>
                                <div>
                                    <small style={{ color: '#64748b' }}>Output:</small>
                                    <div className="tb-code-block">{currentQuestao.exemplo_output2}</div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="tb-nav-bar">
                        <button className="tb-btn-nav" onClick={goToPreviousQuestion} disabled={currentQuestionIndex === 0}>
                            <ArrowLeft size={18} /> Anterior
                        </button>
                        <span className="text-gray-600 font-medium text-sm">
                            {currentQuestionIndex + 1} / {questoes.length}
                        </span>
                        <button className="tb-btn-nav" onClick={goToNextQuestion} disabled={currentQuestionIndex === questoes.length - 1}>
                            Próxima <ArrowRight size={18} />
                        </button>
                    </div>
                </div>
            </main>

            {showExitWarning && (
                <div className="exit-warning-modal" onClick={() => setShowExitWarning(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h3> Atenção!</h3>
                        <p>
                            Você saiu da prova {saidasCount} vez(es).
                            {saidasCount >= maxSaidas - 1
                                ? ` ÚLTIMA CHANCE! A próxima saída invalidará sua prova!`
                                : ` Restam ${maxSaidas - saidasCount} saída(s) permitida(s).`
                            }
                        </p>
                        <button onClick={() => setShowExitWarning(false)}>Entendi</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TextBox;
