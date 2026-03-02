import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, Loader2, AlertTriangle, CheckCircle, Search, RefreshCw } from "lucide-react";
import { analysisService, type SimilarityAnalysisResult, type SimilarityQuestion } from "../services/AnalysisService";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/SimilarityAnalysis.css";

interface Prova {
    id: number;
    titulo: string;
    linguagem: string;
}

export default function SimilarityAnalysis() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const { getIdToken } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // If navigated from a specific submission, the caller may pass { from: 'submission', aluno_id }
    const alunoIdFromState = (location.state as any)?.from === 'submission' ? (location.state as any)?.aluno_id : null;

    const [prova, setProva] = useState<Prova | null>(null);
    const [analysis, setAnalysis] = useState<SimilarityAnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);

    useEffect(() => {
        loadData();
    }, [prova_id]);

    const loadData = async () => {
        try {
            setLoading(true);
            const token = await getIdToken();

            const provaResponse = await axios.get(`${API_BASE_URL}/provas/${prova_id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setProva(provaResponse.data);

            const result = await analysisService.getSimilarityAnalysis(parseInt(prova_id!), token);
            setAnalysis(result);

            if (result.status === "processing") {
                startPolling();
            }
        } catch (err: any) {
            console.error("Erro ao carregar dados:", err);
        } finally {
            setLoading(false);
        }
    };

    const startPolling = () => {
        const interval = setInterval(async () => {
            try {
                const token = await getIdToken();
                const result = await analysisService.getSimilarityAnalysis(parseInt(prova_id!), token);
                setAnalysis(result);

                if (result.status === "completed" || result.status === "failed") {
                    clearInterval(interval);
                    setAnalyzing(false);
                }
            } catch {
                clearInterval(interval);
                setAnalyzing(false);
            }
        }, 3000);
    };

    const handleStartAnalysis = async () => {
        try {
            setAnalyzing(true);
            const token = await getIdToken();
            await analysisService.startSimilarityAnalysis(parseInt(prova_id!), token);
            startPolling();
        } catch (error: any) {
            console.error("Erro ao iniciar analise:", error);
            alert(error.response?.data?.detail || "Erro ao iniciar analise de similaridade");
            setAnalyzing(false);
        }
    };

    const getSimilarityClass = (similarity: number): string => {
        if (similarity >= 70) return "high";
        if (similarity >= 40) return "medium";
        return "low";
    };

    const getSimilarityLabel = (similarity: number): string => {
        if (similarity >= 70) return "Alta";
        if (similarity >= 40) return "Media";
        return "Baixa";
    };

    if (loading) {
        return (
            <div className="sim-loading-container">
                <Loader2 className="sim-spinner" size={48} />
            </div>
        );
    }

    return (
        <div className="sim-container">
            <header className="sim-header">
                <div className="sim-header-content">
                    <button
                        onClick={() => {
                            if (alunoIdFromState) {
                                navigate(`/professor/prova/${prova_id}/aluno/${alunoIdFromState}`);
                            } else {
                                navigate(`/professor/prova/${prova_id}/submissoes`);
                            }
                        }}
                        className="sim-nav-link"
                    >
                        <ArrowLeft size={20} />
                        <span>Voltar</span>
                    </button>

                    <div className="sim-title-row">
                        <div>
                            <h1 className="sim-title">Analise de Similaridade</h1>
                            <p className="sim-subtitle">
                                {prova?.titulo} - {prova?.linguagem}
                            </p>
                        </div>

                        {analysis?.status === "completed" && (
                            <div className="sim-stats-group">
                                <div className="sim-stat-card blue">
                                    <span className="sim-stat-value">{analysis.total_students}</span>
                                    <span className="sim-stat-label">Alunos</span>
                                </div>
                                <div className={`sim-stat-card ${analysis.total_flagged_pairs! > 0 ? "red" : "green"}`}>
                                    <span className="sim-stat-value">{analysis.total_flagged_pairs}</span>
                                    <span className="sim-stat-label">Pares Suspeitos</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            <main className="sim-main">
                <div className="sim-action-bar">
                    <button
                        onClick={handleStartAnalysis}
                        disabled={analyzing}
                        className="sim-btn-analyze"
                    >
                        {analyzing ? (
                            <>
                                <Loader2 className="spinning" size={20} />
                                Analisando...
                            </>
                        ) : (
                            <>
                                {analysis?.status === "completed" ? <RefreshCw size={20} /> : <Search size={20} />}
                                {analysis?.status === "completed" ? "Re-analisar" : "Iniciar Analise"}
                            </>
                        )}
                    </button>

                    {analysis?.threshold_used && (
                        <span className="sim-threshold-info">
                            Limiar de alerta: {analysis.threshold_used}%
                        </span>
                    )}
                </div>

                {(analyzing || analysis?.status === "processing") && (
                    <div className="sim-status processing">
                        <Loader2 className="spinning" size={20} />
                        <span>Analisando similaridade entre submissoes...</span>
                    </div>
                )}

                {analysis?.status === "failed" && (
                    <div className="sim-status error">
                        <AlertTriangle size={20} />
                        <span>Erro na analise: {analysis.error}</span>
                    </div>
                )}

                {(!analysis || analysis.status === "not_found") && !analyzing && (
                    <div className="sim-empty-state">
                        <Search size={48} style={{ opacity: 0.5 }} />
                        <h3>Nenhuma analise realizada</h3>
                        <p>Clique em "Iniciar Analise" para comparar as submissoes dos alunos.</p>
                    </div>
                )}

                {analysis?.status === "completed" && analysis.questions && (
                    <div className="sim-results">
                        {analysis.questions.map((question: SimilarityQuestion) => (
                            <div key={question.questao_id} className="sim-question-card">
                                <div
                                    className="sim-question-header"
                                    onClick={() => setExpandedQuestion(
                                        expandedQuestion === question.questao_id ? null : question.questao_id
                                    )}
                                >
                                    <div className="sim-question-info">
                                        <h3>{question.questao_titulo}</h3>
                                        <span className="sim-question-meta">
                                            {question.total_submissions} submissoes - {question.total_pairs} pares comparados
                                        </span>
                                    </div>

                                    <div className="sim-question-badge-group">
                                        {question.flagged_pairs > 0 ? (
                                            <span className="sim-badge danger">
                                                <AlertTriangle size={14} />
                                                {question.flagged_pairs} pares suspeitos
                                            </span>
                                        ) : (
                                            <span className="sim-badge success">
                                                <CheckCircle size={14} />
                                                Sem alertas
                                            </span>
                                        )}
                                        <span className="sim-expand-icon">
                                            {expandedQuestion === question.questao_id ? "▼" : ""}
                                        </span>
                                    </div>
                                </div>

                                {expandedQuestion === question.questao_id && (
                                    <div className="sim-pairs-table">
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>Aluno A</th>
                                                    <th>Aluno B</th>
                                                    <th>Sim. Texto</th>
                                                    <th>Sim. Normalizada</th>
                                                    <th>Max</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {question.pairs.map((pair, idx) => (
                                                    <tr key={idx} className={pair.flagged ? "flagged-row" : ""}>
                                                        <td>
                                                            <div className="sim-aluno-cell">
                                                                <span className="sim-aluno-name">{pair.aluno_a.nome}</span>
                                                                <span className="sim-aluno-email">{pair.aluno_a.email}</span>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <div className="sim-aluno-cell">
                                                                <span className="sim-aluno-name">{pair.aluno_b.nome}</span>
                                                                <span className="sim-aluno-email">{pair.aluno_b.email}</span>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <span className={`sim-percentage ${getSimilarityClass(pair.text_similarity)}`}>
                                                                {pair.text_similarity.toFixed(1)}%
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span className={`sim-percentage ${getSimilarityClass(pair.normalized_similarity)}`}>
                                                                {pair.normalized_similarity.toFixed(1)}%
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span className={`sim-percentage ${getSimilarityClass(pair.max_similarity)}`}>
                                                                {pair.max_similarity.toFixed(1)}%
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span className={`sim-status-badge ${pair.flagged ? "danger" : "ok"}`}>
                                                                {pair.flagged ? getSimilarityLabel(pair.max_similarity) : "OK"}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>

                                        {question.pairs.length === 0 && (
                                            <div className="sim-no-pairs">
                                                Apenas 1 submissao - nao ha pares para comparar.
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
