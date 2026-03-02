import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, Loader2, CheckCircle, AlertCircle, Clock, Plus, Trash2, Save } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/CriarProva.css";
import "../css/AdicionarQuestoes.css";

interface ProvaData {
    id: number;
    titulo: string;
    descricao: string | null;
    data_aplicacao: string;
    data_fim: string;
    linguagem: string;
    max_saidas: number;
    emails_permitidos: string[];
    professor_id: number;
}

interface Questao {
    id?: number;
    titulo: string;
    descricao: string;
    exemplo_input1: string;
    exemplo_output1: string;
    exemplo_input2: string;
    exemplo_output2: string;
    peso: number;
}

const linguagens = ["Python", "Java", "C++", "JavaScript"];

function parseDateTimeFields(isoString: string) {
    if (!isoString) return { date: "", time: "" };
    const d = new Date(isoString + "Z"); // stored as UTC, parse correctly
    const pad = (n: number) => n.toString().padStart(2, "0");
    return {
        date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
        time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
    };
}

export default function EditarProva() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const { getIdToken, userType, backendUser } = useAuth();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    // --- Exam Info ---
    const [titulo, setTitulo] = useState("");
    const [descricao, setDescricao] = useState("");
    const [linguagem, setLinguagem] = useState("Python");
    const [maxSaidas, setMaxSaidas] = useState(3);
    const [dataAplicacao, setDataAplicacao] = useState("");
    const [dataFim, setDataFim] = useState("");
    const [horaInicio, setHoraInicio] = useState("");
    const [horaTermino, setHoraTermino] = useState("");
    const [emailsBulk, setEmailsBulk] = useState("");
    const [originalProvaData, setOriginalProvaData] = useState<ProvaData | null>(null);

    // --- Questions ---
    const [questoes, setQuestoes] = useState<Questao[]>([]);

    useEffect(() => {
        loadAll();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [prova_id]);

    const parseEmails = (text: string): string[] => {
        const emails = text
            .split(/[\n,;\s]+/)
            .map((e) => e.trim().toLowerCase())
            .filter((e) => e.includes("@") && e.length > 3);
        return [...new Set(emails)];
    };

    const emailCount = emailsBulk.trim() ? parseEmails(emailsBulk).length : 0;

    const loadAll = async () => {
        setLoading(true);
        try {
            const token = await getIdToken();
            const headers = { Authorization: `Bearer ${token}` };

            const [provaRes, questoesRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/provas/${prova_id}`, { headers }),
                axios.get(`${API_BASE_URL}/questoes/prova/${prova_id}`, { headers }),
            ]);

            const prova: ProvaData = provaRes.data;

            // Only the owning professor may edit this exam
            if (userType !== "professor") {
                navigate("/dashboard/aluno", { replace: true });
                return;
            }
            if (backendUser && prova.professor_id !== backendUser.id) {
                navigate("/dashboard/professor", { replace: true });
                return;
            }

            setOriginalProvaData(prova);

            // Populate exam info fields
            setTitulo(prova.titulo);
            setDescricao(prova.descricao || "");
            setLinguagem(prova.linguagem);
            setMaxSaidas(prova.max_saidas ?? 3);

            const { date: dateStart, time: timeStart } = parseDateTimeFields(prova.data_aplicacao);
            const { date: dateEnd, time: timeEnd } = parseDateTimeFields(prova.data_fim);
            setDataAplicacao(dateStart);
            setDataFim(dateEnd);
            setHoraInicio(timeStart);
            setHoraTermino(timeEnd);

            if (prova.emails_permitidos?.length > 0) {
                setEmailsBulk(prova.emails_permitidos.join("\n"));
            }

            // Populate questions
            if (questoesRes.data.length > 0) {
                setQuestoes(questoesRes.data);
            } else {
                setQuestoes([{
                    titulo: "", descricao: "",
                    exemplo_input1: "", exemplo_output1: "",
                    exemplo_input2: "", exemplo_output2: "",
                    peso: 100,
                }]);
            }
        } catch (err: any) {
            console.error("Erro ao carregar dados da prova:", err);
            setError(err.response?.data?.detail || "Erro ao carregar dados da prova.");
        } finally {
            setLoading(false);
        }
    };

    // --- Question management ---
    const redistributeWeights = (list: Questao[]): Questao[] => {
        if (list.length === 0) return list;
        const equalWeight = parseFloat((100 / list.length).toFixed(1));
        return list.map(q => ({ ...q, peso: equalWeight }));
    };

    const handleAddQuestao = () => {
        const newList = [...questoes, {
            titulo: "", descricao: "",
            exemplo_input1: "", exemplo_output1: "",
            exemplo_input2: "", exemplo_output2: "",
            peso: 0,
        }];
        setQuestoes(redistributeWeights(newList));
    };

    const handleRemoveQuestao = (index: number) => {
        if (questoes.length === 1) {
            setError("A prova deve conter pelo menos uma questão.");
            return;
        }
        setQuestoes(redistributeWeights(questoes.filter((_, i) => i !== index)));
    };

    const handleQuestaoChange = (index: number, field: keyof Questao, value: string | number) => {
        const updated = [...questoes];
        // @ts-ignore
        updated[index] = { ...updated[index], [field]: value };
        setQuestoes(updated);
    };

    // --- Save ---
    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        // Validate exam fields
        if (!titulo.trim()) return setError("O título é obrigatório.");
        if (!dataAplicacao) return setError("A data de início é obrigatória.");
        if (!dataFim) return setError("A data de término é obrigatória.");
        if (!horaInicio || !horaTermino) return setError("Os horários de início e término são obrigatórios.");
        const startISO = `${dataAplicacao}T${horaInicio}:00`;
        const endISO = `${dataFim}T${horaTermino}:00`;
        if (endISO <= startISO) return setError("A data/hora de término deve ser posterior ao início.");

        // Validate questions
        for (let i = 0; i < questoes.length; i++) {
            const q = questoes[i];
            if (!q.titulo.trim()) return setError(`Questão ${i + 1}: O título é obrigatório.`);
            if (!q.descricao.trim()) return setError(`Questão ${i + 1}: A descrição é obrigatória.`);
            if (!q.exemplo_input1.trim() || !q.exemplo_output1.trim()) return setError(`Questão ${i + 1}: O Exemplo 1 é obrigatório.`);
        }

        setSaving(true);
        try {
            const token = await getIdToken();
            const headers = { Authorization: `Bearer ${token}` };

            const dataInicioISO = new Date(`${dataAplicacao}T${horaInicio}:00`).toISOString().slice(0, 19);
            const dataFimISO = new Date(`${dataFim}T${horaTermino}:00`).toISOString().slice(0, 19);
            const emailsPermitidos = parseEmails(emailsBulk);

            // Update exam info
            await axios.put(
                `${API_BASE_URL}/provas/${prova_id}`,
                {
                    titulo,
                    descricao: descricao || null,
                    data_aplicacao: dataInicioISO,
                    data_fim: dataFimISO,
                    professor_id: originalProvaData?.professor_id,
                    linguagem,
                    emails_permitidos: emailsPermitidos,
                    max_saidas: maxSaidas,
                },
                { headers }
            );

            // Save questions (PUT for existing, POST for new)
            for (const questao of questoes) {
                const payload = {
                    prova_id: parseInt(prova_id!),
                    titulo: questao.titulo,
                    descricao: questao.descricao,
                    exemplo_input1: questao.exemplo_input1,
                    exemplo_output1: questao.exemplo_output1,
                    exemplo_input2: questao.exemplo_input2 || null,
                    exemplo_output2: questao.exemplo_output2 || null,
                    peso: questao.peso,
                };
                if (questao.id) {
                    await axios.put(`${API_BASE_URL}/questoes/${questao.id}`, payload, { headers });
                } else {
                    await axios.post(`${API_BASE_URL}/questoes/`, payload, { headers });
                }
            }

            setSuccess(true);
            setTimeout(() => navigate("/dashboard/professor"), 2000);
        } catch (err: any) {
            console.error("Erro ao salvar:", err);
            setError(err.response?.data?.detail || "Erro ao salvar as alterações.");
            setSaving(false);
        }
    };

    // --- Render states ---
    if (loading) {
        return (
            <div className="cp-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
                <Loader2 size={48} style={{ animation: 'spin 1s linear infinite', color: '#6366f1' }} />
            </div>
        );
    }

    if (success) {
        return (
            <div className="cp-success-overlay">
                <div className="cp-success-card">
                    <div className="cp-success-icon"><CheckCircle size={32} /></div>
                    <h2 className="cp-success-title">Prova atualizada!</h2>
                    <p className="cp-success-msg">Redirecionando para o dashboard...</p>
                    <Loader2 className="cp-spinner" size={24} color="#94a3b8" style={{ margin: '0 auto' }} />
                </div>
            </div>
        );
    }

    const totalPeso = questoes.reduce((s, q) => s + q.peso, 0);

    return (
        <div className="cp-container">
            {/* Header */}
            <header className="cp-header">
                <div className="cp-header-content">
                    <button onClick={() => navigate("/dashboard/professor")} className="cp-btn-back" title="Voltar">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="cp-title">
                        <h1>Editar Prova</h1>
                        <p>{titulo || "Carregando..."}</p>
                    </div>
                </div>
            </header>

            <main className="cp-main">
                <form onSubmit={handleSave}>

                    {/* ══════════════ SECTION 1: Basic Info ══════════════ */}
                    <div className="cp-section">
                        <span className="cp-section-title">Informações Básicas</span>
                        <div className="cp-card">
                            <div className="cp-form-group">
                                <label className="cp-label">Título da Prova *</label>
                                <input
                                    type="text"
                                    value={titulo}
                                    onChange={(e) => setTitulo(e.target.value)}
                                    placeholder="Ex: Prova Final de Algoritmos"
                                    className="cp-input"
                                    required
                                />
                            </div>

                            <div className="cp-form-group">
                                <label className="cp-label">Descrição <span>(opcional)</span></label>
                                <textarea
                                    value={descricao}
                                    onChange={(e) => setDescricao(e.target.value)}
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
                                            onClick={() => setLinguagem(lang)}
                                            className={`cp-lang-chip ${linguagem === lang ? "active" : ""}`}
                                        >
                                            {lang}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="cp-form-group">
                                <label className="cp-label">
                                    Máximo de Saídas Permitidas *
                                    <span className="cp-hint-inline">(quantas vezes o aluno pode sair da página)</span>
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="20"
                                    value={maxSaidas}
                                    onChange={(e) => setMaxSaidas(parseInt(e.target.value) || 0)}
                                    className="cp-input"
                                    required
                                />
                                <small className="cp-hint">Padrão: 3 saídas. Use 0 para desabilitar o monitoramento.</small>
                            </div>
                        </div>
                    </div>

                    {/* ══════════════ SECTION 2: Scheduling ══════════════ */}
                    <div className="cp-section">
                        <span className="cp-section-title">Agendamento</span>
                        <div className="cp-card">
                            <div className="cp-grid-2">
                                <div className="cp-form-group">
                                    <label className="cp-label">Data de Início *</label>
                                    <input
                                        type="date"
                                        value={dataAplicacao}
                                        onChange={(e) => setDataAplicacao(e.target.value)}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                                <div className="cp-form-group">
                                    <label className="cp-label">Hora de Início *</label>
                                    <input
                                        type="time"
                                        lang="pt-BR"
                                        value={horaInicio}
                                        onChange={(e) => setHoraInicio(e.target.value)}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                                <div className="cp-form-group">
                                    <label className="cp-label">Data de Término *</label>
                                    <input
                                        type="date"
                                        value={dataFim}
                                        onChange={(e) => setDataFim(e.target.value)}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                                <div className="cp-form-group">
                                    <label className="cp-label">Hora de Término *</label>
                                    <input
                                        type="time"
                                        lang="pt-BR"
                                        value={horaTermino}
                                        onChange={(e) => setHoraTermino(e.target.value)}
                                        className="cp-input"
                                        required
                                    />
                                </div>
                            </div>

                            {dataAplicacao && horaInicio && dataFim && horaTermino && (
                                (() => {
                                    const start = new Date(`${dataAplicacao}T${horaInicio}:00`);
                                    const end = new Date(`${dataFim}T${horaTermino}:00`);
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

                    {/* ══════════════ SECTION 3: Access Control ══════════════ */}
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

                    {/* ══════════════ SECTION 4: Questions ══════════════ */}
                    <div className="cp-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                            <div>
                                <span className="cp-section-title" style={{ marginBottom: 0 }}>Questões</span>
                                <span style={{
                                    marginLeft: '12px',
                                    fontSize: '13px',
                                    fontWeight: 600,
                                    color: Math.abs(totalPeso - 100) < 0.5 ? '#16a34a' : '#dc2626'
                                }}>
                                    (Peso total: {totalPeso.toFixed(1)}%)
                                </span>
                            </div>
                            <button type="button" onClick={handleAddQuestao} className="cp-btn-submit" style={{ padding: '8px 16px', width: 'auto' }}>
                                <Plus size={16} /> Nova Questão
                            </button>
                        </div>

                        <div className="questions-list">
                            {questoes.map((questao, index) => (
                                <div key={index} className="question-card">
                                    <div className="card-header">
                                        <span className="question-number">Questão {index + 1}</span>
                                        {questoes.length > 1 && (
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveQuestao(index)}
                                                className="btn btn-danger-ghost"
                                                title="Remover questão"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        )}
                                    </div>

                                    <div className="form-grid">
                                        <div className="row">
                                            <div className="input-group col-grow">
                                                <label>Título da Questão *</label>
                                                <input
                                                    type="text"
                                                    className="input-field"
                                                    value={questao.titulo}
                                                    onChange={(e) => handleQuestaoChange(index, "titulo", e.target.value)}
                                                    placeholder="Ex: Soma Simples"
                                                />
                                            </div>
                                            <div className="input-group col-fixed">
                                                <label>Peso (%)</label>
                                                <input
                                                    type="number"
                                                    className="input-field"
                                                    value={questao.peso}
                                                    min="0"
                                                    max="100"
                                                    step="0.1"
                                                    onChange={(e) => handleQuestaoChange(index, "peso", parseFloat(e.target.value) || 0)}
                                                />
                                            </div>
                                        </div>

                                        <div className="input-group">
                                            <label>Descrição do Problema *</label>
                                            <textarea
                                                className="input-field textarea-field"
                                                value={questao.descricao}
                                                onChange={(e) => handleQuestaoChange(index, "descricao", e.target.value)}
                                                placeholder="Descreva o problema, regras e restrições..."
                                                rows={4}
                                            />
                                        </div>

                                        <div className="row">
                                            <div className="input-group col-half">
                                                <label>Input Exemplo 1 *</label>
                                                <textarea
                                                    className="input-field textarea-sm"
                                                    value={questao.exemplo_input1}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_input1", e.target.value)}
                                                    placeholder="5 3"
                                                    rows={3}
                                                />
                                            </div>
                                            <div className="input-group col-half">
                                                <label>Output Esperado 1 *</label>
                                                <textarea
                                                    className="input-field textarea-sm"
                                                    value={questao.exemplo_output1}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_output1", e.target.value)}
                                                    placeholder="8"
                                                    rows={3}
                                                />
                                            </div>
                                        </div>

                                        <div className="row">
                                            <div className="input-group col-half">
                                                <label>Input Exemplo 2 <span style={{ color: '#94a3b8' }}>(opcional)</span></label>
                                                <textarea
                                                    className="input-field textarea-sm"
                                                    value={questao.exemplo_input2}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_input2", e.target.value)}
                                                    placeholder="10 7"
                                                    rows={3}
                                                />
                                            </div>
                                            <div className="input-group col-half">
                                                <label>Output Esperado 2 <span style={{ color: '#94a3b8' }}>(opcional)</span></label>
                                                <textarea
                                                    className="input-field textarea-sm"
                                                    value={questao.exemplo_output2}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_output2", e.target.value)}
                                                    placeholder="17"
                                                    rows={3}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="cp-error-box">
                            <AlertCircle size={20} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="cp-actions">
                        <button type="button" onClick={() => navigate("/dashboard/professor")} className="cp-btn-cancel">
                            Cancelar
                        </button>
                        <button type="submit" disabled={saving} className="cp-btn-submit">
                            {saving ? (
                                <><Loader2 className="cp-spinner" size={18} /> Salvando...</>
                            ) : (
                                <><Save size={18} /> Salvar Alterações</>
                            )}
                        </button>
                    </div>
                </form>
            </main>
        </div>
    );
}
