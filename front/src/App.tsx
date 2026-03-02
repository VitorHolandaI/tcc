import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import DashboardProfessor from "./pages/DashboardProfessor";
import DashboardAluno from "./pages/DashboardAluno";
import CriarProva from "./pages/CriarProva";
import AdicionarQuestoes from "./pages/AdicionarQuestoes";
import SubmissoesProva from "./pages/SubmissoesProva";
import VisualizarSubmissao from "./pages/VisualizarSubmissao";
import DetalhesProva from "./pages/DetalhesProva";
import SimilarityAnalysis from "./pages/SimilarityAnalysis";
import EditarProva from "./pages/EditarProva";
import TextBox from "./components/TextBox";
import VerResultadoProva from "./pages/VerResultadoProva";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rota raiz "/" mostra diretamente o Login */}
          <Route path="/" element={<Login />} />

          {/* Opcional: mantém o /login funcionando e apontando para o mesmo lugar */}
          <Route path="/login" element={<Navigate to="/" replace />} />

          {/* Rotas de Dashboard */}
          <Route
            path="/dashboard/*"
            element={
              <ProtectedRoute>
                <Routes>
                  <Route path="professor" element={<DashboardProfessor />} />
                  <Route path="aluno" element={<DashboardAluno />} />
                </Routes>
              </ProtectedRoute>
            }
          />

          {/* Rotas do Professor */}
          <Route
            path="/professor/*"
            element={
              <ProtectedRoute>
                <Routes>
                  <Route path="criar-prova" element={<CriarProva />} />
                  <Route path="prova/:prova_id/adicionar-questoes" element={<AdicionarQuestoes />} />
                  <Route path="prova/:prova_id/editar" element={<EditarProva />} />
                  <Route path="prova/:prova_id/submissoes" element={<SubmissoesProva />} />
                  <Route path="prova/:prova_id/detalhes" element={<DetalhesProva />} />
                  <Route path="prova/:prova_id/aluno/:aluno_id" element={<VisualizarSubmissao />} />
                  <Route path="prova/:prova_id/similaridade" element={<SimilarityAnalysis />} />
                </Routes>
              </ProtectedRoute>
            }
          />

          {/* Resultado do Aluno (sem ScreenGuard - somente leitura) */}
          <Route
            path="/aluno/resultado/:prova_id"
            element={
              <ProtectedRoute>
                <VerResultadoProva />
              </ProtectedRoute>
            }
          />

          {/* Fazer Prova (TextBox handles fullscreen + recording) */}
          <Route
            path="/aluno/fazer-prova/:prova_id"
            element={
              <ProtectedRoute>
                <TextBox />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;