import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, User, Loader2, FileText, XCircle } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/ListaSubmissoes.css"; // Importação do arquivo de estilos

interface Prova {
    id: number;
    titulo: string;
    descricao: string | null;
    data_aplicacao: string;
    linguagem: string;
}

interface Aluno {
    id: number;
    nome: string;
    email: string;
    matricula: string;
}

interface Avaliacao {
    id: number;
    questao_id: number;
    aluno_id: number;
    codigo_submetido: string;
    resultado_execucao: string | null;
    nota: number | null;
}

interface AlunoComAvaliacoes {
    aluno: Aluno;
    avaliacoes: Avaliacao[];
    questoes_respondidas: number;
    total_questoes: number;
    nota_total: number | null;
}

export default function SubmissoesProva() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const { getIdToken } = useAuth();
    const navigate = useNavigate();

    const [prova, setProva] = useState<Prova | null>(null);
    const [alunosComAvaliacoes, setAlunosComAvaliacoes] = useState<AlunoComAvaliacoes[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        loadSubmissoes();
    }, [prova_id]);

    const loadSubmissoes = async () => {
        try {
            setLoading(true);
            const token = await getIdToken();

            // 1. Buscar info da prova
            const provaResponse = await axios.get(`${API_BASE_URL}/provas/${prova_id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setProva(provaResponse.data);

            // 2. Buscar questões da prova
            const questoesResponse = await axios.get(`${API_BASE_URL}/questoes/prova/${prova_id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const questoes = questoesResponse.data;
            const totalQuestoes = questoes.length;

            // 3. Buscar todas as avaliações da prova
            const avaliacoesResponse = await axios.get(`${API_BASE_URL}/avaliacoes/prova/${prova_id}/todas`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const avaliacoes: Avaliacao[] = avaliacoesResponse.data;

            // 4. Agrupar avaliações por aluno
            const alunosMap = new Map<number, AlunoComAvaliacoes>();

            // Pré-carregar dados dos alunos envolvidos
            for (const avaliacao of avaliacoes) {
                if (!alunosMap.has(avaliacao.aluno_id)) {
                    const alunoResponse = await axios.get(`${API_BASE_URL}/alunos/${avaliacao.aluno_id}`, {
                        headers: { Authorization: `Bearer ${token}` },
                    });

                    alunosMap.set(avaliacao.aluno_id, {
                        aluno: alunoResponse.data,
                        avaliacoes: [],
                        questoes_respondidas: 0,
                        total_questoes: totalQuestoes,
                        nota_total: null,
                    });
                }

                const alunoData = alunosMap.get(avaliacao.aluno_id)!;
                alunoData.avaliacoes.push(avaliacao);

                if (avaliacao.codigo_submetido && avaliacao.codigo_submetido.trim().length > 0) {
                    alunoData.questoes_respondidas++;
                }
            }

            // 5. Calcular nota total (média ponderada: sum(nota * peso) / sum(peso))
            const pesoMap = new Map<number, number>();
            for (const q of questoes) {
                pesoMap.set(q.id, q.peso || 1);
            }

            for (const alunoData of alunosMap.values()) {
                const notasValidas = alunoData.avaliacoes.filter(av => av.nota !== null);
                if (notasValidas.length > 0) {
                    const totalPeso = notasValidas.reduce((sum, av) => sum + (pesoMap.get(av.questao_id) || 1), 0);
                    alunoData.nota_total = totalPeso > 0
                        ? notasValidas.reduce((sum, av) => sum + (av.nota || 0) * (pesoMap.get(av.questao_id) || 1), 0) / totalPeso
                        : 0;
                }
            }

            setAlunosComAvaliacoes(Array.from(alunosMap.values()));
        } catch (err: any) {
            console.error("Erro ao carregar submissões:", err);
            setError(err.response?.data?.detail || "Erro ao carregar submissões");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="sp-loading-container">
                <Loader2 className="sp-spinner" size={48} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="sp-error-container">
                <div className="sp-error-card">
                    <XCircle className="text-red-600 mx-auto" style={{ color: '#dc2626', margin: '0 auto 1rem' }} size={64} />
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Erro</h2>
                    <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>{error}</p>
                    <button
                        onClick={() => navigate("/dashboard/professor")}
                        className="sp-btn-back-error"
                    >
                        Voltar ao Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="sp-container">
            {/* Header */}
            <header className="sp-header">
                <div className="sp-header-content">
                    <button
                        onClick={() => navigate("/dashboard/professor")}
                        className="sp-nav-link"
                    >
                        <ArrowLeft size={20} />
                        <span>Voltar ao Dashboard</span>
                    </button>
                    <h1 className="sp-header-title">{prova?.titulo}</h1>
                    <p className="sp-header-meta">
                        {new Date((prova?.data_aplicacao || "") + "Z").toLocaleDateString("pt-BR")} às{" "}
                        {new Date((prova?.data_aplicacao || "") + "Z").toLocaleTimeString("pt-BR", {
                            hour: '2-digit',
                            minute: '2-digit'
                        })} • {prova?.linguagem}
                    </p>
                </div>
            </header>

            {/* Main Content */}
            <main className="sp-main">
                <div className="sp-page-intro">
                    <h2 className="sp-page-title">Submissões dos Alunos</h2>
                    <p className="sp-page-desc">
                        {alunosComAvaliacoes.length} {alunosComAvaliacoes.length === 1 ? "aluno" : "alunos"} {alunosComAvaliacoes.length === 1 ? "fez" : "fizeram"} esta prova
                    </p>
                </div>

                {alunosComAvaliacoes.length === 0 ? (
                    <div className="sp-empty-state">
                        <FileText className="sp-empty-icon" size={64} style={{ display: 'block', margin: '0 auto 1rem' }} />
                        <h3 className="sp-empty-title">
                            Nenhuma submissão ainda
                        </h3>
                        <p className="sp-empty-desc">
                            Aguardando os alunos realizarem a prova
                        </p>
                    </div>
                ) : (
                    <div className="sp-grid">
                        {alunosComAvaliacoes.map((alunoData) => (
                            <div
                                key={alunoData.aluno.id}
                                className="sp-card"
                            >
                                <div className="sp-card-header">
                                    <div className="sp-avatar">
                                        <User size={24} />
                                    </div>
                                    <div className="sp-student-info">
                                        <h3>{alunoData.aluno.nome}</h3>
                                        <p className="sp-student-email" title={alunoData.aluno.email}>{alunoData.aluno.email}</p>
                                        <p className="sp-student-mat">Mat: {alunoData.aluno.matricula}</p>
                                    </div>
                                </div>

                                {/* Progresso */}
                                <div className="sp-progress-section">
                                    <div className="sp-progress-labels">
                                        <span>Questões respondidas</span>
                                        <span>{alunoData.questoes_respondidas}/{alunoData.total_questoes}</span>
                                    </div>
                                    <div className="sp-progress-track">
                                        <div
                                            className="sp-progress-bar"
                                            style={{
                                                width: `${alunoData.total_questoes > 0 ? (alunoData.questoes_respondidas / alunoData.total_questoes) * 100 : 0}%`
                                            }}
                                        />
                                    </div>
                                </div>

                                {/* Nota */}
                                {alunoData.nota_total !== null && (
                                    <div className="sp-grade-badge">
                                        <span className="sp-grade-label">Nota Total:</span>
                                        <span className="sp-grade-value">
                                            {alunoData.nota_total.toFixed(1)}
                                        </span>
                                    </div>
                                )}

                                {/* Botão */}
                                <button
                                    onClick={() => navigate(`/professor/prova/${prova_id}/aluno/${alunoData.aluno.id}`)}
                                    className="sp-btn-view"
                                >
                                    <FileText size={18} />
                                    Ver Submissão
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}