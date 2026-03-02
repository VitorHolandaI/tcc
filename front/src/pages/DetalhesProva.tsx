import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, Loader2, AlertCircle, Play, Download, Trash2 } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/DetalhesProva.css";

interface Prova {
    id: number;
    titulo: string;
    descricao: string | null;
    data_aplicacao: string;
    data_fim: string;
    linguagem: string;
    emails_permitidos: string[];
}

interface Questao {
    id: number;
    titulo: string;
    peso: number;
}

interface Submissao {
    id: number;
    questao_id: number;
    aluno_id: number;
    codigo_submetido: string;
    data_envio: string;
    finalizada: boolean;
}

interface Aluno {
    id: number;
    nome: string;
    email: string;
    matricula: string;
}

interface AlunoComSubmissoes {
    aluno: Aluno;
    submissoes: Submissao[];
    total_questoes: number;
    questoes_respondidas: number;
    finalizada: boolean;
    has_recording: boolean;
}

export default function DetalhesProva() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const { getIdToken } = useAuth();
    const navigate = useNavigate();

    const [prova, setProva] = useState<Prova | null>(null);
    const [questoes, setQuestoes] = useState<Questao[]>([]);
    const [alunosData, setAlunosData] = useState<AlunoComSubmissoes[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [videoModal, setVideoModal] = useState(false);
    const [currentAlunoNome, setCurrentAlunoNome] = useState("");

    useEffect(() => {
        loadData();
    }, [prova_id]);

    const loadData = async () => {
        if (!prova_id) return;

        try {
            setLoading(true);
            const token = await getIdToken();
            const headers = { Authorization: `Bearer ${token}` };

            const provaResp = await axios.get(`${API_BASE_URL}/provas/${prova_id}`, { headers });
            setProva(provaResp.data);

            const questoesResp = await axios.get(`${API_BASE_URL}/questoes/prova/${prova_id}`, { headers });
            setQuestoes(questoesResp.data);

            const submissoesResp = await axios.get(`${API_BASE_URL}/submissoes/prova-professor/${prova_id}`, { headers });
            const todasSubmissoes: Submissao[] = submissoesResp.data;

            const alunosPorId: Record<number, AlunoComSubmissoes> = {};

            for (const sub of todasSubmissoes) {
                if (!alunosPorId[sub.aluno_id]) {
                    const alunoResp = await axios.get(`${API_BASE_URL}/alunos/${sub.aluno_id}`, { headers });

                    let hasRecording = false;
                    try {
                        const recordingStatus = await axios.get(
                            `${API_BASE_URL}/recordings/status/${prova_id}/${sub.aluno_id}`,
                            { headers }
                        );
                        hasRecording = recordingStatus.data.exists;
                    } catch {
                        hasRecording = false;
                    }

                    alunosPorId[sub.aluno_id] = {
                        aluno: alunoResp.data,
                        submissoes: [],
                        total_questoes: questoes.length || questoesResp.data.length,
                        questoes_respondidas: 0,
                        finalizada: false,
                        has_recording: hasRecording
                    };
                }

                alunosPorId[sub.aluno_id].submissoes.push(sub);
                if (sub.codigo_submetido.trim()) {
                    alunosPorId[sub.aluno_id].questoes_respondidas++;
                }
                if (sub.finalizada) {
                    alunosPorId[sub.aluno_id].finalizada = true;
                }
            }

            setAlunosData(Object.values(alunosPorId));
        } catch (err: any) {
            console.error('Erro ao carregar dados:', err);
            setError(err.response?.data?.detail || 'Erro ao carregar detalhes da prova');
        } finally {
            setLoading(false);
        }
    };

    const viewRecording = async (alunoId: number, alunoNome: string) => {
        try {
            const token = await getIdToken();
            const url = `${API_BASE_URL}/recordings/video/${prova_id}/${alunoId}`;
            setVideoUrl(url);
            setCurrentAlunoNome(alunoNome);
            setVideoModal(true);
        } catch (err) {
            alert('Erro ao carregar gravação');
        }
    };

    const deleteRecording = async (alunoId: number, alunoNome: string) => {
        if (!confirm(`Tem certeza que deseja deletar a gravação de ${alunoNome}?`)) return;

        try {
            const token = await getIdToken();
            await axios.delete(
                `${API_BASE_URL}/recordings/video/${prova_id}/${alunoId}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            alert('Gravação deletada com sucesso');
            loadData();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao deletar gravação');
        }
    };

    if (loading) {
        return (
            <div className="dp-center-screen">
                <Loader2 className="animate-spin" size={48} />
                <p>Carregando detalhes...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="dp-center-screen">
                <AlertCircle size={48} color="#dc2626" />
                <p>{error}</p>
                <button onClick={() => navigate('/dashboard/professor')}>Voltar</button>
            </div>
        );
    }

    return (
        <div className="dp-container">
            <header className="dp-header">
                <button onClick={() => navigate('/dashboard/professor')} className="dp-btn-back">
                    <ArrowLeft size={20} />
                </button>
                <div className="dp-title">
                    <h1>{prova?.titulo}</h1>
                    <p>{questoes.length} questões • {alunosData.length} alunos</p>
                </div>
            </header>

            <main className="dp-main">
                <h2>Submissões dos Alunos</h2>

                {alunosData.length === 0 && (
                    <div className="dp-empty">
                        <p>Nenhum aluno iniciou esta prova ainda.</p>
                    </div>
                )}

                <div className="dp-alunos-grid">
                    {alunosData.map(({ aluno, submissoes, questoes_respondidas, total_questoes, finalizada, has_recording }) => (
                        <div
                            key={aluno.id}
                            className="dp-aluno-card"
                            style={{ cursor: 'pointer' }}
                            onClick={() => navigate(`/professor/prova/${prova_id}/aluno/${aluno.id}`)}
                        >
                            <div className="dp-aluno-header">
                                <div>
                                    <h3>{aluno.nome}</h3>
                                    <p className="dp-aluno-email">{aluno.email}</p>
                                    <p className="dp-aluno-matricula">Matrícula: {aluno.matricula}</p>
                                </div>
                                <div className="dp-status-badges">
                                    {finalizada ? (
                                        <span className="dp-badge finalizada"> Finalizada</span>
                                    ) : (
                                        <span className="dp-badge em-andamento"> Em Andamento</span>
                                    )}
                                </div>
                            </div>

                            <div className="dp-progresso">
                                <div className="dp-progresso-bar">
                                    <div
                                        className="dp-progresso-fill"
                                        style={{ width: `${(questoes_respondidas / total_questoes) * 100}%` }}
                                    />
                                </div>
                                <span className="dp-progresso-text">
                                    {questoes_respondidas} / {total_questoes} questões respondidas
                                </span>
                            </div>

                            {has_recording && (
                                <div className="dp-actions">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            viewRecording(aluno.id, aluno.nome);
                                        }}
                                        className="dp-btn-video"
                                    >
                                        <Play size={16} /> Ver Gravação
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteRecording(aluno.id, aluno.nome);
                                        }}
                                        className="dp-btn-delete"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </main>

            {videoModal && (
                <div className="dp-video-modal" onClick={() => setVideoModal(false)}>
                    <div className="dp-video-content" onClick={(e) => e.stopPropagation()}>
                        <div className="dp-video-header">
                            <h3> Gravação de {currentAlunoNome}</h3>
                            <button onClick={() => setVideoModal(false)}></button>
                        </div>
                        <video
                            controls
                            autoPlay
                            src={videoUrl || ''}
                            style={{ width: '100%', maxHeight: '70vh' }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
