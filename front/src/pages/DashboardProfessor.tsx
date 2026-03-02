import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { BookOpen, Calendar, LogOut, Loader2, Edit, Users, Clock, CheckCircle } from "lucide-react";
import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import "../css/DashboardProfessor.css"

interface Prova {
  id: number;
  titulo: string;
  descricao: string | null;
  data_aplicacao: string;
  data_fim: string;
  linguagem: string;
  professor_id: number;
  emails_permitidos?: string[];
}

export default function DashboardProfessor() {
  const { backendUser, logout, userType, getIdToken } = useAuth();
  const navigate = useNavigate();
  const [provas, setProvas] = useState<Prova[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Redirect if not a professor
  if (userType !== "professor") {
    navigate("/dashboard/aluno");
    return null;
  }

  useEffect(() => {
    loadProvas();
  }, []);

  const loadProvas = async () => {
    try {
      setLoading(true);
      const token = await getIdToken();
      const response = await axios.get(`${API_BASE_URL}/provas/me/todas`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Ordenar provas por data de aplicação (mais próximas primeiro)
      const provasOrdenadas = response.data.sort((a: Prova, b: Prova) => {
        const dataA = new Date(a.data_aplicacao + "Z").getTime();
        const dataB = new Date(b.data_aplicacao + "Z").getTime();
        return dataA - dataB;
      });

      setProvas(provasOrdenadas);
    } catch (err: any) {
      console.error("Erro ao carregar provas:", err);
      const errorMessage = typeof err.response?.data?.detail === 'string'
        ? err.response.data.detail
        : "Erro ao carregar provas";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const handleEditProva = (provaId: number) => {
    navigate(`/professor/prova/${provaId}/adicionar-questoes`);
  };

  const now = new Date();
  const provasAgendadas = provas.filter(p => new Date(p.data_aplicacao + "Z") > now);
  const provasEmAndamento = provas.filter(p => new Date(p.data_aplicacao + "Z") <= now && new Date(p.data_fim + "Z") >= now);
  const provasPassadas = provas.filter(p => new Date(p.data_fim + "Z") < now);

  // Componente interno do Card para manter o código organizado
  const ProvaCard = ({ prova }: { prova: Prova }) => {
    const isPast = new Date(prova.data_fim + "Z") < now;
    const isInProgress = new Date(prova.data_aplicacao + "Z") <= now && new Date(prova.data_fim + "Z") >= now;

    let statusClass = "scheduled";
    let statusText = "Agendada";
    
    if (isPast) {
      statusClass = "past";
      statusText = "Finalizada";
    } else if (isInProgress) {
      statusClass = "ongoing";
      statusText = "Em Andamento";
    }

    return (
      <div className="prova-card">
        <div className="card-header">
          <div className="flex-1">
            <h3
              className="card-title"
              onClick={() => navigate(`/professor/prova/${prova.id}/editar`)}
              style={{ cursor: 'pointer' }}
              title="Clique para editar a prova"
            >
              {prova.titulo}
            </h3>
            {prova.descricao && (
              <p className="card-desc">{prova.descricao}</p>
            )}
          </div>
          <div className={`status-badge ${statusClass}`}>
            {statusText}
          </div>
        </div>

        <div className="card-meta">
          <span className="meta-item">
            <Calendar size={16} />
            {new Date(prova.data_aplicacao + "Z").toLocaleDateString("pt-BR")}
          </span>
          <span className="meta-item">
            <Clock size={16} />
            {new Date(prova.data_aplicacao + "Z").toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit' })}
            {" - "}
            {new Date(prova.data_fim + "Z").toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit' })}
          </span>
          <span className="lang-tag">
            {prova.linguagem}
          </span>
          {prova.emails_permitidos && prova.emails_permitidos.length > 0 && (
            <span className="meta-item">
              <Users size={16} />
              {prova.emails_permitidos.length} aluno{prova.emails_permitidos.length > 1 ? "s" : ""}
            </span>
          )}
        </div>

        {isPast ? (
          <button
            onClick={() => navigate(`/professor/prova/${prova.id}/detalhes`)}
            className="btn-card view"
          >
            <Users size={18} />
            Ver Detalhes
          </button>
        ) : isInProgress ? (
          <button
            onClick={() => navigate(`/professor/prova/${prova.id}/detalhes`)}
            className="btn-card track"
          >
            <Users size={18} />
            Ver Detalhes
          </button>
        ) : (
          <button
            onClick={() => handleEditProva(prova.id)}
            className="btn-card edit"
          >
            <Edit size={18} />
            Editar Questões
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="brand">
            <h1>Proctor Lcc</h1>
            <p>Painel do Professor</p>
          </div>
          <div className="user-controls">
            <div className="user-info">
              <span className="user-name">{backendUser?.nome}</span>
              <span className="user-email">{backendUser?.email}</span>
            </div>
            <button onClick={handleLogout} className="btn-logout" title="Sair">
              <LogOut size={18} />
              <span className="text-sm">Sair</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="welcome-section">
          <h2 className="welcome-title">
            Bem-vindo, Professor {backendUser?.nome?.split(" ")[0]}!
          </h2>
          <p className="text-muted">
            Gerencie suas provas e acompanhe o desempenho dos alunos
          </p>
        </div>

        {/* Create Prova Button */}
        <div className="create-btn-container">
          <button
            onClick={() => navigate("/professor/criar-prova")}
            className="btn-primary-large"
          >
            <BookOpen size={24} />
            Criar Nova Prova
          </button>
        </div>

        {/* Quick Stats */}
        <div className="stats-container">
          <h3 className="card-title">Estatísticas Rápidas</h3>
          <div className="stats-grid">
            <div className="stat-item blue">
              <span className="stat-number text-blue">{provas.length}</span>
              <span className="stat-label">Provas Criadas</span>
            </div>
            <div className="stat-item indigo">
              <span className="stat-number text-indigo">{provasAgendadas.length}</span>
              <span className="stat-label">Agendadas</span>
            </div>
            <div className="stat-item green">
              <span className="stat-number text-green">{provasEmAndamento.length}</span>
              <span className="stat-label">Em Andamento</span>
            </div>
            <div className="stat-item purple">
              <span className="stat-number text-purple">{provasPassadas.length}</span>
              <span className="stat-label">Passadas</span>
            </div>
          </div>
        </div>

        {/* Provas List */}
        {loading ? (
          <div className="loading-container">
            <Loader2 className="spinner text-blue" size={48} />
          </div>
        ) : error ? (
          <div className="error-container">
            <p className="error-text">{error}</p>
          </div>
        ) : provas.length === 0 ? (
          <div className="empty-state">
            <BookOpen className="empty-icon" size={64} />
            <h3 className="card-title">Nenhuma prova criada ainda</h3>
            <p className="text-muted">Comece criando sua primeira prova de programação</p>
            <button
              onClick={() => navigate("/professor/criar-prova")}
              className="btn-empty"
            >
              Criar Primeira Prova
            </button>
          </div>
        ) : (
          <>
            {/* Provas Em Andamento */}
            {provasEmAndamento.length > 0 && (
              <section>
                <div className="section-title">
                  <Loader2 className="text-green" size={24} />
                  <h3>Em Andamento ({provasEmAndamento.length})</h3>
                </div>
                <div className="provas-grid">
                  {provasEmAndamento.map((prova) => (
                    <ProvaCard key={prova.id} prova={prova} />
                  ))}
                </div>
              </section>
            )}

            {/* Provas Agendadas */}
            {provasAgendadas.length > 0 && (
              <section>
                <div className="section-title">
                  <Clock className="text-blue" size={24} />
                  <h3>Agendadas ({provasAgendadas.length})</h3>
                </div>
                <div className="provas-grid">
                  {provasAgendadas.map((prova) => (
                    <ProvaCard key={prova.id} prova={prova} />
                  ))}
                </div>
              </section>
            )}

            {/* Provas Passadas */}
            {provasPassadas.length > 0 && (
              <section>
                <div className="section-title">
                  <CheckCircle className="text-muted" size={24} />
                  <h3>Passadas ({provasPassadas.length})</h3>
                </div>
                <div className="provas-grid">
                  {provasPassadas.map((prova) => (
                    <ProvaCard key={prova.id} prova={prova} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}