import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, Loader2, CheckCircle, Clock, AlertCircle } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/CriarProva.css"; // Certifique-se que o caminho está correto

interface ProvaFormData {
    titulo: string;
    descricao: string;
    data_aplicacao: string;
    hora_aplicacao: string;
    data_fim_date: string;
    hora_termino: string;
    linguagem: string;
    max_saidas: number;
}

export default function CriarProva() {
    const { backendUser, getIdToken } = useAuth();
    const navigate = useNavigate();

    const [formData, setFormData] = useState<ProvaFormData>({
        titulo: "",
        descricao: "",
        data_aplicacao: "",
        hora_aplicacao: "",
        data_fim_date: "",
        hora_termino: "",
        linguagem: "Python",
        max_saidas: 3,
    });

    const [emailsBulk, setEmailsBulk] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const linguagens = ["Python", "Java", "C++", "JavaScript"];

    const parseEmails = (text: string): string[] => {
        const emails = text
            .split(/[\n,;\s]+/)
            .map((e) => e.trim().toLowerCase())
            .filter((e) => e.includes("@") && e.length > 3);
        return [...new Set(emails)];
    };

    const emailCount = emailsBulk.trim() ? parseEmails(emailsBulk).length : 0;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        // Validações básicas
        if (!formData.titulo.trim()) {
            setError("O título é obrigatório.");
            setLoading(false);
            return;
        }
        if (!formData.data_aplicacao) {
            setError("A data é obrigatória.");
            setLoading(false);
            return;
        }
        if (!formData.hora_aplicacao || !formData.hora_termino) {
            setError("Os horários de início e término são obrigatórios.");
            setLoading(false);
            return;
        }
        if (!formData.data_fim_date) {
            setError("A data de término é obrigatória.");
            setLoading(false);
            return;
        }
        const startISO = `${formData.data_aplicacao}T${formData.hora_aplicacao}:00`;
        const endISO = `${formData.data_fim_date}T${formData.hora_termino}:00`;
        if (endISO <= startISO) {
            setError("A data/hora de término deve ser posterior ao início.");
            setLoading(false);
            return;
        }

        try {
            const token = await getIdToken();
            if (!token) {
                setError("Erro de autenticação. Faça login novamente.");
                setLoading(false);
                return;
            }

            const dataInicioISO = new Date(`${formData.data_aplicacao}T${formData.hora_aplicacao}:00`).toISOString().slice(0, 19);
            const dataFimISO = new Date(`${formData.data_fim_date}T${formData.hora_termino}:00`).toISOString().slice(0, 19);
            const emailsPermitidos = parseEmails(emailsBulk);

            const response = await axios.post(
                `${API_BASE_URL}/provas/`,
                {
                    titulo: formData.titulo,
                    descricao: formData.descricao || null,
                    data_aplicacao: dataInicioISO,
                    data_fim: dataFimISO,
                    professor_id: backendUser?.id || 1, // Fallback apenas para dev
                    linguagem: formData.linguagem,
                    emails_permitidos: emailsPermitidos,
                    max_saidas: formData.max_saidas,
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setLoading(false);
            setSuccess(true);
            
            // Redirecionamento após sucesso
            setTimeout(() => {
                navigate(`/professor/prova/${response.data.id}/adicionar-questoes`);
            }, 2000);

        } catch (err: any) {
            console.error("Erro ao criar prova:", err);
            setError(err.response?.data?.detail || "Erro ao criar prova. Tente novamente.");
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="cp-success-overlay">
                <div className="cp-success-card">
                    <div className="cp-success-icon">
                        <CheckCircle size={32} />
                    </div>
                    <h2 className="cp-success-title">Prova criada!</h2>
                    <p className="cp-success-msg">Redirecionando para adicionar questões...</p>
                    <Loader2 className="cp-spinner" size={24} color="#94a3b8" style={{ margin: '0 auto' }} />
                </div>
            </div>
        );
    }

    return (
        <div className="cp-container">
            {/* Header */}
            <header className="cp-header">
                <div className="cp-header-content">
                    <button onClick={() => navigate("/dashboard/professor")} className="cp-btn-back" title="Voltar">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="cp-title">
                        <h1>Nova Prova</h1>
                        <p>Configure os detalhes do exame</p>
                    </div>
                </div>
            </header>

            <main className="cp-main">
                <form onSubmit={handleSubmit}>

                    {/* Section 1: Informações Básicas */}
                    <div className="cp-section">
                        <span className="cp-section-title">Informações Básicas</span>
                        <div className="cp-card">
                            <div className="cp-form-group">
                                <label className="cp-label">Título da Prova *</label>
                                <input
                                    type="text"
                                    value={formData.titulo}
                                    onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                                    placeholder="Ex: Prova Final de Algoritmos"
                                    className="cp-input"
                                    required
                                />
                            </div>
                            
                            <div className="cp-form-group">
                                <label className="cp-label">Descrição <span>(opcional)</span></label>
                                <textarea
                                    value={formData.descricao}
                                    onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                                    placeholder="Objetivo e conteúdo da prova..."
                                    className="cp-textarea"
                                />
                            </div>

                            <div className="cp-form-group">
                                <label className="cp-label">Linguagem de Programação *</label>
                                <div className="cp-lang-grid">
                                    {linguagens.map((lang) => (
                                        <button
                                            key={lang}
                                            type="button"
                                            onClick={() => setFormData({ ...formData, linguagem: lang })}
                                            className={`cp-lang-chip ${formData.linguagem === lang ? "active" : ""}`}
                                        >
                                            {lang}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="cp-form-group">
                                <label className="cp-label">
                                    Máximo de Saídas Permitidas *
                                    <span className="cp-hint-inline">
                                        (quantas vezes o aluno pode sair da página)
                                    </span>
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="20"
                                    value={formData.max_saidas}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        max_saidas: parseInt(e.target.value) || 0
                                    })}
                                    className="cp-input"
                                    required
                                />
                                <small className="cp-hint">
                                    Padrão: 3 saídas. Use 0 para desabilitar o monitoramento.
                                </small>
                            </div>
                        </div>
                    </div>

                    {/* Section 2: Agendamento */}
                    <div className="cp-section">
                        <span className="cp-section-title">Agendamento</span>
                        <div className="cp-card">
                            <div className="cp-grid-2">
                                <div className="cp-form-group">
                                    <label className="cp-label">Data de Início *</label>
                                    <input
                                        type="date"
                                        value={formData.data_aplicacao}
                                        onChange={(e) => setFormData({ ...formData, data_aplicacao: e.target.value })}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                                <div className="cp-form-group">
                                    <label className="cp-label">Hora de Início *</label>
                                    <input
                                        type="time"
                                        lang="pt-BR"
                                        value={formData.hora_aplicacao}
                                        onChange={(e) => setFormData({ ...formData, hora_aplicacao: e.target.value })}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                                <div className="cp-form-group">
                                    <label className="cp-label">Data de Término *</label>
                                    <input
                                        type="date"
                                        value={formData.data_fim_date}
                                        onChange={(e) => setFormData({ ...formData, data_fim_date: e.target.value })}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                                <div className="cp-form-group">
                                    <label className="cp-label">Hora de Término *</label>
                                    <input
                                        type="time"
                                        lang="pt-BR"
                                        value={formData.hora_termino}
                                        onChange={(e) => setFormData({ ...formData, hora_termino: e.target.value })}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                            </div>

                            {formData.data_aplicacao && formData.hora_aplicacao && formData.data_fim_date && formData.hora_termino && (
                                (() => {
                                    const start = new Date(`${formData.data_aplicacao}T${formData.hora_aplicacao}:00`);
                                    const end = new Date(`${formData.data_fim_date}T${formData.hora_termino}:00`);
                                    const diffMs = end.getTime() - start.getTime();
                                    if (diffMs <= 0) return null;
                                    const diffMins = Math.floor(diffMs / 60000);
                                    const days = Math.floor(diffMins / 1440);
                                    const hours = Math.floor((diffMins % 1440) / 60);
                                    const mins = diffMins % 60;
                                    const parts = [];
                                    if (days > 0) parts.push(`${days}d`);
                                    if (hours > 0) parts.push(`${hours}h`);
                                    if (mins > 0) parts.push(`${mins}min`);
                                    return (
                                        <div className="cp-duration-badge">
                                            <Clock size={14} />
                                            <span>Duração: {parts.join(" ")}</span>
                                        </div>
                                    );
                                })()
                            )}
                        </div>
                    </div>

                    {/* Section 3: Alunos */}
                    <div className="cp-section">
                        <span className="cp-section-title">Controle de Acesso</span>
                        <div className="cp-card">
                            <div className="cp-form-group">
                                <label className="cp-label">Lista de Emails Permitidos</label>
                                <textarea
                                    value={emailsBulk}
                                    onChange={(e) => setEmailsBulk(e.target.value)}
                                    placeholder={"aluno1@email.com\naluno2@email.com"}
                                    rows={5}
                                    className="cp-textarea"
                                />
                                <div className="cp-email-info">
                                    <span className={`cp-email-count ${emailCount > 0 ? "has-emails" : ""}`}>
                                        {emailCount > 0
                                            ? `${emailCount} email${emailCount > 1 ? "s" : ""} detectado${emailCount > 1 ? "s" : ""}`
                                            : "Todos os alunos cadastrados poderão acessar"}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Error Box */}
                    {error && (
                        <div className="cp-error-box">
                            <AlertCircle size={20} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="cp-actions">
                        <button
                            type="button"
                            onClick={() => navigate("/dashboard/professor")}
                            className="cp-btn-cancel"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="cp-btn-submit"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="cp-spinner" size={18} />
                                    Criando...
                                </>
                            ) : (
                                "Criar Prova e Adicionar Questões"
                            )}
                        </button>
                    </div>
                </form>
            </main>
        </div>
    );
}