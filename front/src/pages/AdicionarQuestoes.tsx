import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowLeft, Plus, Trash2, Save, CheckCircle, Loader2 } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/AdicionarQuestoes.css"; // Importação do arquivo CSS

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

interface Prova {
    id: number;
    titulo: string;
    linguagem: string;
    data_aplicacao: string;
}

export default function AdicionarQuestoes() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const { getIdToken } = useAuth();
    const navigate = useNavigate();

    const [prova, setProva] = useState<Prova | null>(null);
    const [questoes, setQuestoes] = useState<Questao[]>([
        {
            titulo: "",
            descricao: "",
            exemplo_input1: "",
            exemplo_output1: "",
            exemplo_input2: "",
            exemplo_output2: "",
            peso: 100,
        },
    ]);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        loadProva();
        loadQuestoes();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [prova_id]);

    const loadProva = async () => {
        try {
            const token = await getIdToken();
            const response = await axios.get(`${API_BASE_URL}/provas/${prova_id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setProva(response.data);
        } catch (err) {
            console.error("Erro ao carregar prova:", err);
            setError("Erro ao carregar dados da prova");
        }
    };

    const loadQuestoes = async () => {
        setLoading(true);
        try {
            const token = await getIdToken();
            const response = await axios.get(
                `${API_BASE_URL}/questoes/prova/${prova_id}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            if (response.data.length > 0) {
                setQuestoes(response.data);
            }
        } catch (err) {
            console.error("Erro ao carregar questões:", err);
        } finally {
            setLoading(false);
        }
    };

    const redistributeWeights = (list: Questao[]): Questao[] => {
        if (list.length === 0) return list;
        const equalWeight = parseFloat((100 / list.length).toFixed(1));
        return list.map(q => ({ ...q, peso: equalWeight }));
    };

    const handleAddQuestao = () => {
        const newList = [
            ...questoes,
            {
                titulo: "",
                descricao: "",
                exemplo_input1: "",
                exemplo_output1: "",
                exemplo_input2: "",
                exemplo_output2: "",
                peso: 0,
            },
        ];
        setQuestoes(redistributeWeights(newList));
    };

    const handleRemoveQuestao = (index: number) => {
        if (questoes.length === 1) {
            setError("A prova deve conter pelo menos uma questão.");
            return;
        }
        const newList = questoes.filter((_, i) => i !== index);
        setQuestoes(redistributeWeights(newList));
    };

    const handleQuestaoChange = (index: number, field: keyof Questao, value: string | number) => {
        const updated = [...questoes];
        // @ts-ignore - Bypass simples para tipagem dinâmica segura neste contexto
        updated[index] = { ...updated[index], [field]: value };
        setQuestoes(updated);
    };

    const handleSave = async () => {
        setError("");
        setSaving(true);

        // Validação
        for (let i = 0; i < questoes.length; i++) {
            const q = questoes[i];
            if (!q.titulo.trim()) {
                setError(`Questão ${i + 1}: O título é obrigatório.`);
                setSaving(false);
                return;
            }
            if (!q.descricao.trim()) {
                setError(`Questão ${i + 1}: A descrição é obrigatória.`);
                setSaving(false);
                return;
            }
            if (!q.exemplo_input1.trim() || !q.exemplo_output1.trim()) {
                setError(`Questão ${i + 1}: O Exemplo 1 é obrigatório.`);
                setSaving(false);
                return;
            }
        }

        try {
            const token = await getIdToken();
            const headers = { Authorization: `Bearer ${token}` };

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
            setTimeout(() => {
                navigate("/dashboard/professor");
            }, 2000);
        } catch (err: any) {
            console.error("Erro ao salvar:", err);
            setError(err.response?.data?.detail || "Erro ao salvar as questões.");
            setSaving(false);
        }
    };

    if (success) {
        return (
            <div className="feedback-screen">
                <div className="feedback-card">
                    <div className="icon-circle">
                        <CheckCircle size={40} color="#15803d" />
                    </div>
                    <h2>Sucesso!</h2>
                    <p>{questoes.length} {questoes.length === 1 ? "questão salva" : "questões salvas"}.</p>
                    <p className="header-meta">Redirecionando...</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="feedback-screen">
                <Loader2 className="loading-spinner" size={48} />
            </div>
        );
    }

    return (
        <div className="page-container">
            {/* Header */}
            <header className="page-header">
                <div className="header-content">
                    <button onClick={() => navigate("/dashboard/professor")} className="btn-back">
                        <ArrowLeft size={18} />
                        Voltar ao Dashboard
                    </button>
                    {prova && (
                        <div className="header-title">
                            <h1>{prova.titulo}</h1>
                            <p className="header-meta">
                                {prova.linguagem} • {new Date(prova.data_aplicacao + "Z").toLocaleDateString("pt-BR")}
                            </p>
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <main className="main-content">
                <div className="section-header">
                    <div>
                        <h2>Questões da Prova</h2>
                        <p>Defina os desafios que os alunos irão resolver.
                            {" "}
                            <span style={{
                                fontWeight: 600,
                                color: Math.abs(questoes.reduce((s, q) => s + q.peso, 0) - 100) < 0.5 ? '#16a34a' : '#dc2626'
                            }}>
                                (Peso total: {questoes.reduce((s, q) => s + q.peso, 0).toFixed(1)}%)
                            </span>
                        </p>
                    </div>
                    <button onClick={handleAddQuestao} className="btn btn-primary">
                        <Plus size={18} />
                        Nova Questão
                    </button>
                </div>

                {/* Lista de Questões */}
                <div className="questions-list">
                    {questoes.map((questao, index) => (
                        <div key={index} className="question-card">
                            <div className="card-header">
                                <span className="question-number">Questão {index + 1}</span>
                                {questoes.length > 1 && (
                                    <button
                                        onClick={() => handleRemoveQuestao(index)}
                                        className="btn btn-danger-ghost"
                                        title="Remover questão"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                )}
                            </div>

                            <div className="form-grid">
                                {/* Título e Peso */}
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
                                        <label>Peso (%) *</label>
                                        <input
                                            type="number"
                                            className="input-field"
                                            value={questao.peso}
                                            onChange={(e) => handleQuestaoChange(index, "peso", parseFloat(e.target.value) || 0)}
                                            min="0"
                                            step="0.5"
                                        />
                                    </div>
                                </div>

                                {/* Descrição */}
                                <div className="input-group">
                                    <label>Descrição do Problema *</label>
                                    <textarea
                                        className="textarea-field"
                                        value={questao.descricao}
                                        onChange={(e) => handleQuestaoChange(index, "descricao", e.target.value)}
                                        placeholder="Descreva detalhadamente o que o aluno deve fazer..."
                                        rows={4}
                                    />
                                </div>

                                {/* Casos de Teste / Exemplos */}
                                <div className="examples-section">
                                    {/* Exemplo 1 */}
                                    <div className="example-block">
                                        <span className="example-title">Caso de Teste 1 (Obrigatório)</span>
                                        <div className="row">
                                            <div className="input-group col-grow">
                                                <label>Input (Entrada)</label>
                                                <input
                                                    type="text"
                                                    className="input-field"
                                                    value={questao.exemplo_input1}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_input1", e.target.value)}
                                                    placeholder="Ex: 10 20"
                                                />
                                            </div>
                                            <div className="input-group col-grow">
                                                <label>Output (Saída Esperada)</label>
                                                <input
                                                    type="text"
                                                    className="input-field"
                                                    value={questao.exemplo_output1}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_output1", e.target.value)}
                                                    placeholder="Ex: 30"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Exemplo 2 */}
                                    <div className="example-block">
                                        <span className="example-title">Caso de Teste 2 (Opcional)</span>
                                        <div className="row">
                                            <div className="input-group col-grow">
                                                <label>Input (Entrada)</label>
                                                <input
                                                    type="text"
                                                    className="input-field"
                                                    value={questao.exemplo_input2}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_input2", e.target.value)}
                                                    placeholder="Ex: -5 5"
                                                />
                                            </div>
                                            <div className="input-group col-grow">
                                                <label>Output (Saída Esperada)</label>
                                                <input
                                                    type="text"
                                                    className="input-field"
                                                    value={questao.exemplo_output2}
                                                    onChange={(e) => handleQuestaoChange(index, "exemplo_output2", e.target.value)}
                                                    placeholder="Ex: 0"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Mensagem de Erro */}
                {error && (
                    <div className="error-banner">
                        <strong>Atenção:</strong> {error}
                    </div>
                )}

                {/* Footer de Ações */}
                <div className="actions-footer">
                    <button
                        onClick={() => navigate("/dashboard/professor")}
                        className="btn btn-secondary"
                        disabled={saving}
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="btn btn-primary"
                    >
                        {saving ? (
                            <>
                                <Loader2 className="animate-spin" size={20} />
                                Salvando...
                            </>
                        ) : (
                            <>
                                <Save size={20} />
                                Salvar Todas as Questões
                            </>
                        )}
                    </button>
                </div>
            </main>
        </div>
    );
}