import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Calendar, PlayCircle, LogOut, Loader2, Clock, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/DashBoardAluno.css"; // Importando estilos

interface Prova {
    id: number;
    titulo: string;
    descricao: string | null;
    data_aplicacao: string;
    data_fim: string;
    linguagem: string;
    professor_id: number;
}

interface Avaliacao {
    id: number;
    questao_id: number;
    aluno_id: number;
    codigo_submetido: string;
    resultado_execucao: string | null;
    nota: number | null;
    data_submissao: string;
    finalizada: boolean;
}

interface ProvaComStatus extends Prova {
    status: "nao_iniciada" | "em_andamento" | "finalizada";
    avaliacoes?: Avaliacao[];
    progresso?: {
        questoes_com_codigo: number;
        total_questoes: number;
    };
}

export default function DashboardAluno() {
    const { backendUser, logout, userType, getIdToken } = useAuth();
    const navigate = useNavigate();

    const [provas, setProvas] = useState<ProvaComStatus[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState<"andamento" | "agendadas" | "feitas">("andamento");

    useEffect(() => {
        if (userType === "aluno") {
            loadProvasComAvaliacoes();
        }
    }, [userType]);

    const handleLogout = async () => {
        await logout();
        navigate("/login");
    };

    if (userType !== "aluno") {
        navigate("/dashboard/professor");
        return null;
    }

    const loadProvasComAvaliacoes = async () => {
        try {
            setLoading(true);
            const token = await getIdToken();

            const provasResponse = await axios.get(`${API_BASE_URL}/provas/aluno/disponiveis`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const provasDisponiveis: Prova[] = provasResponse.data;

            const avaliacoesResponse = await axios.get(`${API_BASE_URL}/submissoes/me/todas`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const todasAvaliacoes: Avaliacao[] = avaliacoesResponse.data;

            const provasComStatus: ProvaComStatus[] = [];

            for (const prova of provasDisponiveis) {
                try {
                    const questoesResponse = await axios.get(`${API_BASE_URL}/questoes/prova/${prova.id}`, {
                        headers: { Authorization: `Bearer ${token}` },
                    });
                    const questoes = questoesResponse.data;
                    const totalQuestoes = questoes.length;

                    const avaliacoesDaProva = todasAvaliacoes.filter(av =>
                        questoes.some((q: any) => q.id === av.questao_id)
                    );

                    const agora = new Date();
                    let status: "nao_iniciada" | "em_andamento" | "finalizada" = "nao_iniciada";

                    // Verificar se a prova foi finalizada pelo aluno
                    const provaFinalizada = avaliacoesDaProva.some((av: any) => av.finalizada === true);

                    if (provaFinalizada) {
                        // Se o aluno finalizou a prova, marcar como finalizada independente do tempo
                        status = "finalizada";
                    } else if (agora < new Date(prova.data_aplicacao + "Z")) {
                        status = "nao_iniciada";
                    } else if (agora <= new Date(prova.data_fim + "Z")) {
                        status = "em_andamento";
                    } else {
                        if (avaliacoesDaProva.length > 0) {
                            status = "finalizada";
                        } else {
                            // Se o tempo passou e não há submissões, não mostrar a prova
                            continue;
                        }
                    }
                    
                    const questoesComCodigo = new Set(avaliacoesDaProva.map(av => av.questao_id)).size;
                    const progresso = {
                        questoes_com_codigo: questoesComCodigo,
                        total_questoes: totalQuestoes
                    };

                    provasComStatus.push({ ...prova, status, progresso, avaliacoes: avaliacoesDaProva });
                } catch (loopErr) {
                    console.error(`Erro ao carregar detalhes da prova ID ${prova.id}:`, loopErr);
                    continue;
                }
            }

            // Ordenar provas por data de aplicação (mais próximas primeiro)
            provasComStatus.sort((a, b) => {
                const dataA = new Date(a.data_aplicacao + "Z").getTime();
                const dataB = new Date(b.data_aplicacao + "Z").getTime();
                return dataA - dataB;
            });

            setProvas(provasComStatus);
        } catch (err: any) {
            console.error("Erro ao carregar provas:", err);
setError(err.response?.data?.detail || "Erro ao carregar dashboard do aluno");
        } finally {
            setLoading(false);
        }
    };

    const handleIniciarProva = (prova_id: number) => {
        navigate(`/aluno/fazer-prova/${prova_id}`);
    };

    const handleVerResultado = (prova_id: number) => {
        navigate(`/aluno/resultado/${prova_id}`);
    };

    const provasEmAndamento = provas.filter(p => p.status === "em_andamento");
    const provasAgendadas = provas.filter(p => p.status === "nao_iniciada");
    const provasFeitas = provas.filter(p => p.status === "finalizada");

    const ProvaCard = ({ prova, type }: { prova: ProvaComStatus; type: "andamento" | "agendada" | "feita" }) => {
        // Definições visuais baseadas no tipo
        const isAndamento = type === "andamento";
        const isAgendada = type === "agendada";

        const iconBoxClass = isAndamento ? "green" : isAgendada ? "blue" : "gray";
        const Icon = isAndamento ? PlayCircle : isAgendada ? Clock : CheckCircle2;
        
        let buttonText = "Iniciar Prova";
        let buttonClass = "start"; // green default
        
        if (prova.status === "em_andamento") {
            buttonText = "Continuar Prova";
        } else if (prova.status === "finalizada") {
            buttonText = "Ver Resultado";
            buttonClass = "closed";
        } else if (isAgendada) {
            buttonClass = "schedule";
        }

        return (
            <div className="prova-card">
                <div className="card-header">
                    <div className="flex-1">
                        <h3 className="card-title">{prova.titulo}</h3>
                        {prova.descricao && (
                            <p className="card-desc">{prova.descricao}</p>
                        )}
                    </div>
                    <div className={`status-icon-box ${iconBoxClass}`}>
                        <Icon size={24} />
                    </div>
                </div>

                <div className="card-meta">
                    <span className="meta-item">
                        <Calendar size={16} />
                        {new Date(prova.data_aplicacao + "Z").toLocaleDateString("pt-BR")} às{" "}
                        {new Date(prova.data_aplicacao + "Z").toLocaleTimeString("pt-BR", {
                            hour: '2-digit', minute: '2-digit'
                        })}
                    </span>


                    <span className="meta-item">
                       -- <Calendar size={16} />
                        {new Date(prova.data_fim + "Z").toLocaleDateString("pt-BR")} às{" "}
                        {new Date(prova.data_fim + "Z").toLocaleTimeString("pt-BR", {
                            hour: '2-digit', minute: '2-digit'
                        })}
                    </span>


                    <span className="lang-tag">
                        {prova.linguagem}
                    </span>
                </div>

                {/* Progresso (apenas se iniciada ou finalizada) */}
                {prova.status !== "nao_iniciada" && prova.progresso && (
                    <div className="progress-section">
                        <div className="progress-labels">
                            <span>Progresso</span>
                            <span>{prova.progresso.questoes_com_codigo}/{prova.progresso.total_questoes} questões</span>
                        </div>
                        <div className="progress-track">
                            <div
                                className={`progress-fill ${isAndamento ? "green" : "gray"}`}
                                style={{
                                    width: `${(prova.progresso.questoes_com_codigo / prova.progresso.total_questoes) * 100}%`
                                }}
                            />
                        </div>
                    </div>
                )}

                {!isAgendada && (
                    <button
                        onClick={() => prova.status === "finalizada" ? handleVerResultado(prova.id) : handleIniciarProva(prova.id)}
                        className={`btn-action ${buttonClass}`}
                    >
                        {prova.status === "finalizada" ? <CheckCircle2 size={18} /> : <PlayCircle size={18} />}
                        {buttonText}
                    </button>
                )}
            </div>
        );
    };

    if (loading) {
        return (
            <div className="loading-wrapper">
                <Loader2 className="animate-spin text-blue-600" size={48} />
            </div>
        );
    }

    return (
        <div className="dashboard-container">
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-content">
                    <div className="brand">
                        <h1>Proctor Lcc</h1>
                        <p>Painel do Aluno</p>
                    </div>
                    <div className="user-controls">
                        <div className="user-info">
                            <span className="user-name">{backendUser?.nome}</span>
                            <span className="user-email">{backendUser?.email}</span>
                        </div>
                        <button onClick={handleLogout} className="btn-logout">
                            <LogOut size={18} />
                            <span>Sair</span>
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="main-content">
                <div className="welcome-section">
                    <h2 className="welcome-title">
                        Bem-vindo, {backendUser?.nome?.split(" ")[0]}!
                    </h2>
                    <p className="text-muted">Suas provas de programação</p>
                </div>

                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4">
                        <p className="text-sm text-red-600">{error}</p>
                    </div>
                )}

                {/* Tabs */}
                <div className="tabs-container">
                    <button
                        onClick={() => setActiveTab("andamento")}
                        className={`tab-btn ${activeTab === "andamento" ? "active" : ""}`}
                    >
                        Em Andamento ({provasEmAndamento.length})
                    </button>
                    <button
                        onClick={() => setActiveTab("agendadas")}
                        className={`tab-btn ${activeTab === "agendadas" ? "active" : ""}`}
                    >
                        Agendadas ({provasAgendadas.length})
                    </button>
                    <button
                        onClick={() => setActiveTab("feitas")}
                        className={`tab-btn ${activeTab === "feitas" ? "active" : ""}`}
                    >
                        Feitas ({provasFeitas.length})
                    </button>
                </div>

                {/* Content */}
                {activeTab === "andamento" && (
                    <div className="provas-grid">
                        {provasEmAndamento.length === 0 ? (
                            <div className="empty-state">
                                <PlayCircle className="empty-icon mx-auto" size={64} />
                                <h3 className="empty-title">Nenhuma prova em andamento</h3>
                                <p className="empty-desc">Quando você iniciar uma prova, ela aparecerá aqui</p>
                            </div>
                        ) : (
                            provasEmAndamento.map((prova) => <ProvaCard key={prova.id} prova={prova} type="andamento" />)
                        )}
                    </div>
                )}

                {activeTab === "agendadas" && (
                    <div className="provas-grid">
                        {provasAgendadas.length === 0 ? (
                            <div className="empty-state">
                                <Clock className="empty-icon mx-auto" size={64} />
                                <h3 className="empty-title">Nenhuma prova agendada</h3>
                                <p className="empty-desc">Suas próximas provas aparecerão aqui</p>
                            </div>
                        ) : (
                            provasAgendadas.map((prova) => <ProvaCard key={prova.id} prova={prova} type="agendada" />)
                        )}
                    </div>
                )}

                {activeTab === "feitas" && (
                    <div className="provas-grid">
                        {provasFeitas.length === 0 ? (
                            <div className="empty-state">
                                <CheckCircle2 className="empty-icon mx-auto" size={64} />
                                <h3 className="empty-title">Nenhuma prova finalizada</h3>
                                <p className="empty-desc">Provas concluídas aparecerão aqui</p>
                            </div>
                        ) : (
                            provasFeitas.map((prova) => <ProvaCard key={prova.id} prova={prova} type="feita" />)
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
