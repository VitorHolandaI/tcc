import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import ProvaService, { type Prova } from "../services/ProvaService";
import { Calendar, Clock, BookOpen, Edit, Eye } from "lucide-react";
import "../../css/DetalhesProva.css";

export default function PaginaProvaDetalhesProfessor() {
    const { prova_id } = useParams<{ prova_id: string }>();
    const navigate = useNavigate();
    const { getIdToken } = useAuth();
    const [prova, setProva] = useState<Prova | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadProvaDetails = async () => {
            try {
                const token = await getIdToken();
                if (!token || !prova_id) {
                    setError("Não foi possível carregar os detalhes da prova.");
                    return;
                }
                const data = await ProvaService.getProvaById(Number(prova_id), token);
                setProva(data);
            } catch (err) {
                setError("Erro ao buscar detalhes da prova.");
            } finally {
                setLoading(false);
            }
        };

        loadProvaDetails();
    }, [prova_id, getIdToken]);

    if (loading) {
        return <div className="details-container">Carregando...</div>;
    }

    if (error) {
        return <div className="details-container">{error}</div>;
    }

    if (!prova) {
        return <div className="details-container">Prova não encontrada.</div>;
    }

    return (
        <div className="details-container">
            <div className="details-card">
                <div className="details-header">
                    <h1 className="exam-title">{prova.titulo}</h1>
                    <div className="exam-meta">
                        <span className="meta-item">
                            <Calendar size={18} />
                            {new Date(prova.data_aplicacao + "Z").toLocaleDateString('pt-BR')}
                        </span>
                        <span className="meta-item">
                            <Clock size={18} />
                            {new Date(prova.data_aplicacao + "Z").toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        <span className="meta-item">
                            <BookOpen size={18} />
                            {prova.linguagem}
                        </span>
                    </div>
                </div>

                <div className="details-content">
                    <h2 className="section-label">Descrição</h2>
                    <p className="description-text">
                        {prova.descricao || "Esta prova não tem uma descrição detalhada."}
                    </p>

                    <div className="action-area">
                        <button className="btn-start" onClick={() => navigate(`/professor/prova/${prova_id}/submissoes`)}>
                            <Eye size={20} /> Ver Submissões
                        </button>
                        <button className="btn-start" style={{backgroundColor: '#64748b'}} onClick={() => navigate(`/professor/prova/${prova_id}/adicionar-questoes`)}>
                            <Edit size={20} /> Editar Questões
                        </button>
                        <button className="btn-back" onClick={() => navigate("/dashboard/professor")}>
                            Voltar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
