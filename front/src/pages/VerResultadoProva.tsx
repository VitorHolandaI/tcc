import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, Loader2, Code2, FileText, CheckCircle2 } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/VerResultadoProva.css";

interface Questao {
    id: number;
    titulo: string;
    descricao: string;
    exemplo_input1: string;
    exemplo_output1: string;
    exemplo_input2?: string;
    exemplo_output2?: string;
    peso: number;
    prova_id: number;
}

interface Avaliacao {
    id: number;
    questao_id: number;
    aluno_id: number;
    codigo_submetido: string;
    resultado_execucao: string | null;
    nota: number | null;
    data_submissao: string;
}

interface ProvaComResultados {
    id: number;
    titulo: string;
    descricao: string | null;
    data_aplicacao: string;
    data_fim: string;
    linguagem: string;
    avaliacoes: Avaliacao[];
}

interface QuestaoComAvaliacao {
    questao: Questao;
    avaliacao: Avaliacao | null;
}

export default function VerResultadoProva() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const navigate = useNavigate();
    const { getIdToken } = useAuth();

    const [prova, setProva] = useState<ProvaComResultados | null>(null);
    const [itens, setItens] = useState<QuestaoComAvaliacao[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeQuestao, setActiveQuestao] = useState(0);

    useEffect(() => {
        loadResultado();
    }, [prova_id]);

    const loadResultado = async () => {
        try {
            setLoading(true);
            const token = await getIdToken();
            const headers = { Authorization: `Bearer ${token}` };

            // 1. Carregar prova e avaliações de uma vez
            const res = await axios.get<ProvaComResultados>(
                `${API_BASE_URL}/provas/${prova_id}/meu-resultado`, 
                { headers }
            );
            const provaData = res.data;
            setProva(provaData);

            // 2. Carregar questões da prova
            const questoesRes = await axios.get<Questao[]>(
                `${API_BASE_URL}/questoes/prova/${prova_id}`, 
                { headers }
            );
            const questoes = questoesRes.data;

            // 3. Unir questões com suas respectivas avaliações
            const merged: QuestaoComAvaliacao[] = questoes.map(q => ({
                questao: q,
                avaliacao: provaData.avaliacoes.find(a => a.questao_id === q.id) || null,
            }));

            setItens(merged);
        } catch (err: any) {
            console.error("Erro ao carregar resultado:", err);
            setError(err.response?.data?.detail || "Erro ao carregar resultado da prova.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="vr-loading">
                <Loader2 className="vr-spinner" size={48} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="vr-container">
                <div className="vr-error">{error}</div>
            </div>
        );
    }

    const current = itens[activeQuestao];

    // Weighted average grade: sum(nota * peso) / sum(peso)
    const gradedItems = itens.filter(i => i.avaliacao?.nota !== null && i.avaliacao?.nota !== undefined);
    const totalPeso = gradedItems.reduce((sum, i) => sum + i.questao.peso, 0);
    const notaFinal = totalPeso > 0
        ? gradedItems.reduce((sum, i) => sum + (i.avaliacao?.nota || 0) * i.questao.peso, 0) / totalPeso
        : null;

    return (
        <div className="vr-container">
            <header className="vr-header">
                <div className="vr-header-content">
                    <button onClick={() => navigate("/dashboard/aluno")} className="vr-btn-back">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="vr-header-info">
                        <h1>{prova?.titulo}</h1>
                        <p>
                            {prova && new Date(prova.data_aplicacao + "Z").toLocaleDateString("pt-BR")}
                            {" - "}
                            {prova?.linguagem}
                        </p>
                    </div>
                    {notaFinal !== null && (
                        <div className="vr-nota-final" style={{
                            background: 'linear-gradient(135deg, #059669, #10b981)',
                            color: 'white',
                            padding: '0.5rem 1rem',
                            borderRadius: '0.75rem',
                            fontWeight: 700,
                            fontSize: '1.1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}>
                            Nota Final: {notaFinal.toFixed(1)}
                        </div>
                    )}
                    <div className="vr-badge-readonly">
                        <CheckCircle2 size={14} />
                        Somente Leitura
                    </div>
                </div>
            </header>

            <main className="vr-main">
                {/* Sidebar - lista de questoes */}
                <aside className="vr-sidebar">
                    <span className="vr-sidebar-title">Questoes</span>
                    {itens.map((item, idx) => (
                        <button
                            key={item.questao.id}
                            onClick={() => setActiveQuestao(idx)}
                            className={`vr-sidebar-item ${idx === activeQuestao ? "active" : ""}`}
                        >
                            <span className="vr-sidebar-num">{idx + 1}</span>
                            <span className="vr-sidebar-label">{item.questao.titulo}</span>
                            {item.avaliacao?.nota !== null && item.avaliacao?.nota !== undefined ? (
                                <span className="vr-sidebar-nota">{item.avaliacao.nota}/{item.questao.peso}</span>
                            ) : (
                                item.avaliacao && item.avaliacao.codigo_submetido.trim() && (
                                    <Code2 size={14} className="vr-sidebar-icon" />
                                )
                            )}
                        </button>
                    ))}
                </aside>

                {/* Content */}
                {current && (
                    <div className="vr-content">
                        {/* Questao details */}
                        <div className="vr-card">
                            <div className="vr-card-header">
                                <FileText size={18} />
                                <h2>Questao {activeQuestao + 1}: {current.questao.titulo}</h2>
                                <span className="vr-peso">Peso: {current.questao.peso}%</span>
                                {current.avaliacao?.nota !== null && current.avaliacao?.nota !== undefined ? (
                                    <span className="vr-nota">Nota: {current.avaliacao.nota} / {current.questao.peso}</span>
                                ) : (
                                    <span className="vr-nota-pending">Aguardando correção</span>
                                )}
                            </div>
                            <p className="vr-descricao">{current.questao.descricao}</p>

                            <div className="vr-exemplos">
                                <div className="vr-exemplo">
                                    <span className="vr-exemplo-label">Exemplo 1</span>
                                    <div className="vr-exemplo-io">
                                        <div><strong>Input:</strong> <code>{current.questao.exemplo_input1}</code></div>
                                        <div><strong>Output:</strong> <code>{current.questao.exemplo_output1}</code></div>
                                    </div>
                                </div>
                                {current.questao.exemplo_input2 && (
                                    <div className="vr-exemplo">
                                        <span className="vr-exemplo-label">Exemplo 2</span>
                                        <div className="vr-exemplo-io">
                                            <div><strong>Input:</strong> <code>{current.questao.exemplo_input2}</code></div>
                                            <div><strong>Output:</strong> <code>{current.questao.exemplo_output2}</code></div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Codigo submetido */}
                        <div className="vr-card">
                            <div className="vr-card-header">
                                <Code2 size={18} />
                                <h2>Codigo Submetido</h2>
                            </div>
                            {current.avaliacao && current.avaliacao.codigo_submetido.trim() ? (
                                <pre className="vr-code">{current.avaliacao.codigo_submetido}</pre>
                            ) : (
                                <p className="vr-no-code">Nenhum codigo foi submetido para esta questao.</p>
                            )}
                        </div>

                        {/* Resultado */}
                        {current.avaliacao?.resultado_execucao && (
                            <div className="vr-card">
                                <div className="vr-card-header">
                                    <CheckCircle2 size={18} />
                                    <h2>Resultado da Execução</h2>
                                </div>
                                <pre className="vr-resultado">{current.avaliacao.resultado_execucao}</pre>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
