import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
	ArrowLeft, User, Loader2, CheckCircle, XCircle, FileText,
	Eye, Mic, Keyboard, Video, GitCompare, ChevronDown, Play, Search, Camera
} from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "../services/apiConfig";
import { analysisService, type GazeAnalysisResult, type AudioAnalysisResult, type KeystrokeAnalysisResult } from "../services/AnalysisService";
import { recordingService } from "../services/RecordingService";
import "../css/VisualizarSubmissao.css";

interface Prova {
	id: number;
	titulo: string;
	linguagem: string;
	data_aplicacao: string;
}

interface Questao {
	id: number;
	titulo: string;
	descricao: string;
	exemplo_input1: string;
	exemplo_output1: string;
	exemplo_input2: string | null;
	exemplo_output2: string | null;
	peso: number;
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

interface Aluno {
	id: number;
	nome: string;
	email: string;
	matricula: string;
}

interface QuestaoComAvaliacao extends Questao {
	avaliacao: Avaliacao | null;
}

export default function VisualizarSubmissao() {
	const { prova_id, aluno_id } = useParams<{ prova_id: string; aluno_id: string }>();
	const { getIdToken } = useAuth();
	const navigate = useNavigate();

	const [prova, setProva] = useState<Prova | null>(null);
	const [aluno, setAluno] = useState<Aluno | null>(null);
	const [questoesComAvaliacoes, setQuestoesComAvaliacoes] = useState<QuestaoComAvaliacao[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState("");
	const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

	const [gazeAnalysis, setGazeAnalysis] = useState<GazeAnalysisResult | null>(null);
	const [audioAnalysis, setAudioAnalysis] = useState<AudioAnalysisResult | null>(null);
	const [keystrokeAnalysis, setKeystrokeAnalysis] = useState<KeystrokeAnalysisResult | null>(null);

	const [analyzingGaze, setAnalyzingGaze] = useState(false);
	const [analyzingAudio, setAnalyzingAudio] = useState(false);
	const [analyzingKeystroke, setAnalyzingKeystroke] = useState(false);

	const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
	const dropdownRef = useRef<HTMLDivElement>(null);

	const [showVideoModal, setShowVideoModal] = useState(false);

	const [editingNota, setEditingNota] = useState<number | null>(null);
	const [notaInput, setNotaInput] = useState<string>("");
	const [savingNota, setSavingNota] = useState(false);
	const [videoBlob, setVideoBlob] = useState<string | null>(null);
	const [loadingVideo, setLoadingVideo] = useState(false);

	const [analysisError, setAnalysisError] = useState<string | null>(null);

	useEffect(() => {
		loadSubmissao();

		function handleClickOutside(event: MouseEvent) {
			if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
				setActiveDropdown(null);
			}
		}
		document.addEventListener("mousedown", handleClickOutside);
		return () => document.removeEventListener("mousedown", handleClickOutside);
	}, [prova_id, aluno_id]);

	const toggleDropdown = (name: string) => {
		if (activeDropdown === name) {
			setActiveDropdown(null);
		} else {
			setActiveDropdown(name);
			setAnalysisError(null); // Limpa o erro ao abrir outro dropdown
		}
	};

	const fetchGazeResult = async () => {
		try {
			setActiveDropdown(null);
			setAnalysisError(null);
			const token = await getIdToken();
			const result = await analysisService.getGazeAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);
			setGazeAnalysis(result);
			if (!result || result.status !== 'completed') {
				setAnalysisError("Nenhuma análise de gaze encontrada ou ainda está em processamento. Gere uma nova análise se necessário.");
			}
		} catch (error: any) {
			console.error('Erro ao buscar gaze:', error);
			setAnalysisError(error.response?.data?.detail || 'Erro ao buscar resultado da análise de gaze.');
		}
	};

	const fetchAudioResult = async () => {
		try {
			setActiveDropdown(null);
			setAnalysisError(null);
			const token = await getIdToken();
			const result = await analysisService.getAudioAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);
			setAudioAnalysis(result);
			if (!result || result.status !== 'completed') {
				setAnalysisError("Nenhuma análise de áudio encontrada ou ainda está em processamento. Gere uma nova análise se necessário.");
			}
		} catch (error: any) {
			console.error('Erro ao buscar áudio:', error);
			setAnalysisError(error.response?.data?.detail || 'Erro ao buscar resultado da análise de áudio.');
		}
	};

	const fetchKeystrokeResult = async () => {
		try {
			setActiveDropdown(null);
			setAnalysisError(null);
			const token = await getIdToken();
			const result = await analysisService.getKeystrokeAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);
			setKeystrokeAnalysis(result);
			if (!result || result.status !== 'completed') {
				setAnalysisError("Nenhuma análise de teclado encontrada ou ainda está em processamento. Gere uma nova análise se necessário.");
			}
		} catch (error: any) {
			console.error('Erro ao buscar keystroke:', error);
			setAnalysisError(error.response?.data?.detail || 'Erro ao buscar resultado da análise de teclado.');
		}
	};

	const handleGazeAnalysis = async () => {
		try {
			setActiveDropdown(null);
			setAnalysisError(null);
			setAnalyzingGaze(true);
			const token = await getIdToken();
			await analysisService.startGazeAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);

			const interval = setInterval(async () => {
				try {
					const result = await analysisService.getGazeAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);
					setGazeAnalysis(result);

					if (result.status === 'completed' || result.status === 'failed') {
						clearInterval(interval);
						setAnalyzingGaze(false);
						if (result.status === 'failed') {
							setAnalysisError("A análise de gaze falhou.");
						}
					}
				} catch {
					// Silenciosamente ignora falhas de polling, o erro principal será pego no catch externo
				}
			}, 5000);
		} catch (error: any) {
			console.error('Erro ao iniciar análise de gaze:', error);
			setAnalysisError(error.response?.data?.detail || 'Erro ao iniciar análise de gaze.');
			setAnalyzingGaze(false);
		}
	};

	const handleAudioAnalysis = async () => {
		try {
			setActiveDropdown(null);
			setAnalysisError(null);
			setAnalyzingAudio(true);
			const token = await getIdToken();
			await analysisService.startAudioAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);

			let retries = 0;
			const MAX_RETRIES = 36; // 3 minutos (36 × 5s)
			const interval = setInterval(async () => {
				retries++;
				if (retries > MAX_RETRIES) {
					clearInterval(interval);
					setAnalyzingAudio(false);
					setAnalysisError("A análise de áudio demorou demais. Verifique se o serviço está configurado corretamente e tente novamente.");
					return;
				}
				try {
					const result = await analysisService.getAudioAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);
					setAudioAnalysis(result);

					if (result.status === 'completed' || result.status === 'failed') {
						clearInterval(interval);
						setAnalyzingAudio(false);
						if (result.status === 'failed') {
							setAnalysisError("A análise de áudio falhou. Verifique se há um arquivo de áudio disponível para este aluno.");
						}
					}
				} catch {
					// Ignora falhas de polling
				}
			}, 5000);
		} catch (error: any) {
			console.error('Erro ao iniciar análise de áudio:', error);
			setAnalysisError(error.response?.data?.detail || 'Erro ao iniciar análise de áudio.');
			setAnalyzingAudio(false);
		}
	};

	const handleKeystrokeAnalysis = async () => {
		try {
			setActiveDropdown(null);
			setAnalysisError(null);
			setAnalyzingKeystroke(true);
			const token = await getIdToken();
			await analysisService.startKeystrokeAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);

			let retries = 0;
			const MAX_RETRIES = 24; // 2 minutos (24 × 5s)
			const interval = setInterval(async () => {
				retries++;
				if (retries > MAX_RETRIES) {
					clearInterval(interval);
					setAnalyzingKeystroke(false);
					setAnalysisError("A análise de teclado demorou demais. Tente novamente.");
					return;
				}
				try {
					const result = await analysisService.getKeystrokeAnalysis(parseInt(prova_id!), parseInt(aluno_id!), token);
					setKeystrokeAnalysis(result);

					if (result.status === 'completed' || result.status === 'failed') {
						clearInterval(interval);
						setAnalyzingKeystroke(false);
						if (result.status === 'failed') {
							setAnalysisError("A análise de teclado falhou.");
						}
					}
				} catch {
					// Ignora falhas de polling
				}
			}, 5000);
		} catch (error: any) {
			console.error('Erro ao iniciar análise de keystroke:', error);
			setAnalysisError(error.response?.data?.detail || 'Erro ao iniciar análise de teclado.');
			setAnalyzingKeystroke(false);
		}
	};

	const handleStartEditNota = (questaoIndex: number, notaAtual: number | null) => {
		setEditingNota(questaoIndex);
		setNotaInput(notaAtual !== null ? notaAtual.toString() : "");
	};

	const handleCancelEditNota = () => {
		setEditingNota(null);
		setNotaInput("");
	};

	const handleSaveNota = async (questaoIndex: number) => {
		const questao = questoesComAvaliacoes[questaoIndex];
		if (!questao.avaliacao) {
			alert('Nenhuma submissão encontrada para esta questão');
			return;
		}

		const nota = parseFloat(notaInput);
		if (isNaN(nota) || nota < 0 || nota > 10) {
			alert('Nota inválida. Digite um valor entre 0 e 10.');
			return;
		}

		try {
			setSavingNota(true);
			const token = await getIdToken();

			await axios.put(
				`${API_BASE_URL}/avaliacoes/${questao.avaliacao.id}/nota`,
				{ nota },
				{ headers: { Authorization: `Bearer ${token}` } }
			);

			const updatedQuestoes = [...questoesComAvaliacoes];
			if (updatedQuestoes[questaoIndex].avaliacao) {
				updatedQuestoes[questaoIndex].avaliacao!.nota = nota;
			}
			setQuestoesComAvaliacoes(updatedQuestoes);

			setEditingNota(null);
			setNotaInput("");
		} catch (err: any) {
			console.error('Erro ao salvar nota:', err);
			alert(err.response?.data?.detail || 'Erro ao salvar nota');
		} finally {
			setSavingNota(false);
		}
	};

	const loadVideoWithAuth = async () => {
		try {
			setLoadingVideo(true);
			const token = await getIdToken();

			const response = await fetch(
				`${API_BASE_URL}/recordings/video/${prova_id}/${aluno_id}`,
				{
					headers: {
						'Authorization': `Bearer ${token}`
					}
				}
			);

			if (!response.ok) {
				throw new Error(`Erro ao carregar vídeo: ${response.status} - ${response.statusText}`);
			}

			const blob = await response.blob();
			const blobUrl = URL.createObjectURL(blob);
			setVideoBlob(blobUrl);
		} catch (err: any) {
			console.error('Erro ao carregar vídeo:', err);
			alert(err.message || 'Erro ao carregar vídeo');
		} finally {
			setLoadingVideo(false);
		}
	};

	const loadWebcamVideo = async () => {
		try {
			setLoadingVideo(true);
			setAnalysisError(null);
			const token = await getIdToken();
			const url = recordingService.getWebcamVideoUrl(parseInt(prova_id!), parseInt(aluno_id!));

			const response = await fetch(url, {
				headers: { 'Authorization': `Bearer ${token}` }
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || `Erro ao carregar vídeo da webcam: ${response.status}`);
			}

			const blob = await response.blob();
			const blobUrl = URL.createObjectURL(blob);
			setVideoBlob(blobUrl);
			setShowVideoModal(true);
		} catch (err: any) {
			console.error('Erro ao carregar vídeo da webcam:', err);
			setAnalysisError(err.message || 'Erro ao carregar vídeo da webcam.');
		} finally {
			setLoadingVideo(false);
		}
	};

	const loadSubmissao = async () => {
		try {
			setLoading(true);
			const token = await getIdToken();

			const provaResponse = await axios.get(`${API_BASE_URL}/provas/${prova_id}`, {
				headers: { Authorization: `Bearer ${token}` },
			});
			setProva(provaResponse.data);

			const alunoResponse = await axios.get(`${API_BASE_URL}/alunos/${aluno_id}`, {
				headers: { Authorization: `Bearer ${token}` },
			});
			setAluno(alunoResponse.data);

			const questoesResponse = await axios.get(`${API_BASE_URL}/questoes/prova/${prova_id}`, {
				headers: { Authorization: `Bearer ${token}` },
			});
			const questoes: Questao[] = questoesResponse.data;

			const avaliacoesResponse = await axios.get(
				`${API_BASE_URL}/avaliacoes/prova/${prova_id}/todas`,
				{
					headers: { Authorization: `Bearer ${token}` },
				}
			);
			const todasAvaliacoes: Avaliacao[] = avaliacoesResponse.data;
			const avaliacoesDoAluno = todasAvaliacoes.filter(av => av.aluno_id === parseInt(aluno_id || "0"));

			const questoesComAvs: QuestaoComAvaliacao[] = questoes.map(questao => {
				const avaliacao = avaliacoesDoAluno.find(av => av.questao_id === questao.id);
				return {
					...questao,
					avaliacao: avaliacao || null,
				};
			});

			setQuestoesComAvaliacoes(questoesComAvs);
		} catch (err: any) {
			console.error("Erro ao carregar submissão:", err);
			setError(err.response?.data?.detail || "Erro ao carregar submissão");
		} finally {
			setLoading(false);
		}
	};

	if (loading) {
		return (
			<div className="vs-loading-container">
				<Loader2 className="vs-spinner" size={48} />
			</div>
		);
	}

	if (error) {
		return (
			<div className="vs-error-container">
				<div className="vs-error-card">
					<XCircle className="text-red-600 mx-auto" size={64} style={{ color: '#dc2626' }} />
					<h2 className="vs-error-title">Erro</h2>
					<p className="mb-6 text-gray-600">{error}</p>
					<button
						onClick={() => navigate(`/professor/prova/${prova_id}/submissoes`)}
						className="vs-btn-back"
					>
						Voltar
					</button>
				</div>
			</div>
		);
	}

	const currentQuestao = questoesComAvaliacoes[currentQuestionIndex];
	const totalRespondidas = questoesComAvaliacoes.filter(
		q => q.avaliacao && q.avaliacao.codigo_submetido.trim().length > 0
	).length;

	const gradedQuestions = questoesComAvaliacoes.filter(q => q.avaliacao?.nota !== null && q.avaliacao?.nota !== undefined);
	const totalPeso = gradedQuestions.reduce((sum, q) => sum + q.peso, 0);
	const notaTotal = totalPeso > 0
		? gradedQuestions.reduce((sum, q) => sum + (q.avaliacao?.nota || 0) * q.peso, 0) / totalPeso
		: 0;

	return (
		<div className="vs-container">
			<header className="vs-header">
				<div className="vs-header-content">
					<button
						onClick={() => navigate(`/professor/prova/${prova_id}/submissoes`)}
						className="vs-nav-link"
					>
						<ArrowLeft size={20} />
						<span>Voltar às Submissões</span>
					</button>

					<div className="vs-title-row">
						<div>
							<h1 className="vs-title">{prova?.titulo}</h1>
							<p className="vs-subtitle">
								Submissão de {aluno?.nome} • {prova?.linguagem}
							</p>
						</div>
						<div className="vs-stats-group">
							<div className="vs-stat-card blue">
								<span className="vs-stat-value">{totalRespondidas}/{questoesComAvaliacoes.length}</span>
								<span className="vs-stat-label">Questões</span>
							</div>
							<div className="vs-stat-card green">
								<span className="vs-stat-value">{notaTotal.toFixed(1)}</span>
								<span className="vs-stat-label">Nota Total</span>
							</div>
						</div>
					</div>
				</div>
			</header>

			<main className="vs-main">
				<div className="vs-student-card">
					<div className="vs-avatar">
						<User size={24} />
					</div>
					<div>
						<h3 className="vs-student-name">{aluno?.nome}</h3>
						<p className="vs-student-detail">{aluno?.email} • Mat: {aluno?.matricula}</p>
					</div>
				</div>

				{currentQuestao && (
					<div className="vs-split-view">
						<div className="vs-card">
							<h2 className="vs-card-title">
								Questão {currentQuestionIndex + 1}: {currentQuestao.titulo}
							</h2>

							<div className="mb-4">
								<h3 className="vs-section-title">Descrição</h3>
								<p className="vs-description">{currentQuestao.descricao}</p>
							</div>

							<div className="vs-example-box primary">
								<h4 className="vs-section-title">Exemplo 1</h4>
								<div>
									<div>
										<span className="vs-label">Input:</span>
										<pre className="vs-code-snippet">{currentQuestao.exemplo_input1}</pre>
									</div>
									<div>
										<span className="vs-label">Output:</span>
										<pre className="vs-code-snippet">{currentQuestao.exemplo_output1}</pre>
									</div>
								</div>
							</div>

							{currentQuestao.exemplo_input2 && (
								<div className="vs-example-box">
									<h4 className="vs-section-title">Exemplo 2</h4>
									<div>
										<div>
											<span className="vs-label">Input:</span>
											<pre className="vs-code-snippet">{currentQuestao.exemplo_input2}</pre>
										</div>
										<div>
											<span className="vs-label">Output:</span>
											<pre className="vs-code-snippet">{currentQuestao.exemplo_output2}</pre>
										</div>
									</div>
								</div>
							)}

							<div className="vs-weight">
								<strong>Peso:</strong> {currentQuestao.peso}%
							</div>
						</div>

						<div className="vs-card">
							<div className="vs-code-header">
								<h3 className="vs-card-title" style={{ marginBottom: 0 }}>Código Submetido</h3>
								{currentQuestao.avaliacao && (
									<div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
										{editingNota === currentQuestionIndex ? (
											<>
												<input
													type="number"
													min="0"
													max="10"
													step="0.1"
													value={notaInput}
													onChange={(e) => setNotaInput(e.target.value)}
													disabled={savingNota}
													placeholder="0-10"
													style={{ width: '70px', padding: '0.5rem', border: '2px solid #3b82f6', borderRadius: '6px', fontSize: '0.875rem' }}
												/>
												<button
													onClick={() => handleSaveNota(currentQuestionIndex)}
													disabled={savingNota}
													style={{ padding: '0.5rem 1rem', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 600, cursor: savingNota ? 'not-allowed' : 'pointer', opacity: savingNota ? 0.6 : 1 }}
												>
													{savingNota ? 'Salvando...' : 'Salvar'}
												</button>
												<button
													onClick={handleCancelEditNota}
													disabled={savingNota}
													style={{ padding: '0.5rem 1rem', background: '#6b7280', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 600, cursor: savingNota ? 'not-allowed' : 'pointer', opacity: savingNota ? 0.6 : 1 }}
												>
													Cancelar
												</button>
											</>
										) : (
											<>
												<span className="vs-grade-badge">
													Nota: {currentQuestao.avaliacao.nota !== null ? currentQuestao.avaliacao.nota : '-'}
												</span>
												<button
													onClick={() => handleStartEditNota(currentQuestionIndex, currentQuestao.avaliacao?.nota || null)}
													style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer' }}
												>
													{currentQuestao.avaliacao.nota !== null ? 'Editar Nota' : 'Dar Nota'}
												</button>
											</>
										)}
									</div>
								)}
							</div>

							{currentQuestao.avaliacao && currentQuestao.avaliacao.codigo_submetido.trim() ? (
								<>
									<div className="vs-full-code">
										<pre><code style={{ whiteSpace: 'pre-wrap' }}>{currentQuestao.avaliacao.codigo_submetido}</code></pre>
									</div>
									{currentQuestao.avaliacao.resultado_execucao && (
										<div className="vs-execution-result">
											<h4 className="vs-section-title">Resultado da Execução:</h4>
											<div className="vs-console-output">
												{currentQuestao.avaliacao.resultado_execucao}
											</div>
										</div>
									)}
									<div className="vs-timestamp">
										Submetido em: {new Date(currentQuestao.avaliacao.data_submissao).toLocaleString("pt-BR")}
									</div>
								</>
							) : (
								<div className="vs-empty-state">
									<FileText size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
									<p>Nenhum código submetido para esta questão</p>
								</div>
							)}
						</div>
					</div>
				)}

				<div className="vs-controls-card">
					<div className="vs-nav-header">
						<button
							onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
							disabled={currentQuestionIndex === 0}
							className="vs-btn-nav"
						>
							← Anterior
						</button>
						<span style={{ fontWeight: 500, color: '#334155' }}>
							Questão {currentQuestionIndex + 1} de {questoesComAvaliacoes.length}
						</span>
						<button
							onClick={() => setCurrentQuestionIndex(Math.min(questoesComAvaliacoes.length - 1, currentQuestionIndex + 1))}
							disabled={currentQuestionIndex === questoesComAvaliacoes.length - 1}
							className="vs-btn-nav primary"
						>
							Próxima →
						</button>
					</div>
					<div className="vs-question-list">
						{questoesComAvaliacoes.map((questao, index) => {
							const hasCode = questao.avaliacao && questao.avaliacao.codigo_submetido.trim().length > 0;
							const isCurrent = index === currentQuestionIndex;
							return (
								<button
									key={questao.id}
									onClick={() => setCurrentQuestionIndex(index)}
									className={`vs-q-btn ${isCurrent ? "active" : ""} ${hasCode ? "answered" : ""}`}
								>
									Q{index + 1}
									{hasCode && !isCurrent && <CheckCircle size={14} />}
								</button>
							);
						})}
					</div>
				</div>

				<div className="vs-analysis-section" ref={dropdownRef}>
					<h2 className="vs-analysis-title">Análises Comportamentais</h2>

					<div className="vs-analysis-toolbar">

						<div className="vs-dropdown-container">
							<button
								className="vs-btn-tool"
								onClick={() => toggleDropdown('gaze')}
							>
								{analyzingGaze ? <Loader2 className="spinning" size={18} /> : <Eye size={18} />}
								Análise de Gaze
								<ChevronDown size={14} style={{ marginLeft: '4px' }} />
							</button>

							{activeDropdown === 'gaze' && (
								<div className="vs-dropdown-menu">
									<button
										className="vs-dropdown-item generate"
										onClick={handleGazeAnalysis}
										disabled={analyzingGaze}
									>
										<Play size={14} /> Gerar Análise
									</button>
									<button
										className="vs-dropdown-item"
										onClick={fetchGazeResult}
									>
										<Search size={14} /> Ver Análise
									</button>
								</div>
							)}
						</div>

						<div className="vs-dropdown-container">
							<button
								className="vs-btn-tool"
								onClick={() => toggleDropdown('audio')}
							>
								{analyzingAudio ? <Loader2 className="spinning" size={18} /> : <Mic size={18} />}
								Análise de Áudio
								<ChevronDown size={14} style={{ marginLeft: '4px' }} />
							</button>

							{activeDropdown === 'audio' && (
								<div className="vs-dropdown-menu">
									<button
										className="vs-dropdown-item generate"
										onClick={handleAudioAnalysis}
										disabled={analyzingAudio}
									>
										<Play size={14} /> Gerar Análise
									</button>
									<button
										className="vs-dropdown-item"
										onClick={fetchAudioResult}
									>
										<Search size={14} /> Ver Análise
									</button>
								</div>
							)}
						</div>

						<div className="vs-dropdown-container">
							<button
								className="vs-btn-tool"
								onClick={() => toggleDropdown('keystroke')}
							>
								{analyzingKeystroke ? <Loader2 className="spinning" size={18} /> : <Keyboard size={18} />}
								Análise de Teclado
								<ChevronDown size={14} style={{ marginLeft: '4px' }} />
							</button>

							{activeDropdown === 'keystroke' && (
								<div className="vs-dropdown-menu">
									<button
										className="vs-dropdown-item generate"
										onClick={handleKeystrokeAnalysis}
										disabled={analyzingKeystroke}
									>
										<Play size={14} /> Gerar Análise
									</button>
									<button
										className="vs-dropdown-item"
										onClick={fetchKeystrokeResult}
									>
										<Search size={14} /> Ver Análise
									</button>
								</div>
							)}
						</div>

						<button
							onClick={() => {
								setShowVideoModal(true);
								loadVideoWithAuth();
							}}
							disabled={loadingVideo}
							className="vs-btn-tool video-btn"
						>
							{loadingVideo ? <Loader2 className="spinning" size={18} /> : <Video size={18} />}
							Ver Gravação da Tela
						</button>

						<button
							onClick={loadWebcamVideo}
							disabled={loadingVideo}
							className="vs-btn-tool"
						>
							{loadingVideo ? <Loader2 className="spinning" size={18} /> : <Camera size={18} />}
							Ver Gravação da Webcam
						</button>

						<button
							onClick={() => navigate(`/professor/prova/${prova_id}/similaridade`, { state: { from: 'submission', aluno_id } })}
							className="vs-btn-tool sim-btn"
						>
							<GitCompare size={18} />
							Similaridade de Código
						</button>
					</div>

					{analysisError && (
						<div className="vs-analysis-error-card">
							<div className="vs-error-icon-area">
								<XCircle size={24} />
							</div>
							<div className="vs-error-content-area">
								<strong>Erro na Análise</strong>
								<p>{analysisError}</p>
							</div>
							<button onClick={() => setAnalysisError(null)} className="vs-close-error-btn">
								&times;
							</button>
						</div>
					)}

					{gazeAnalysis && gazeAnalysis.status === 'completed' && gazeAnalysis.metrics && (
						<div className="analysis-results gaze">
							<h3>Análise de Gaze (MediaPipe)</h3>
							<div className="results-grid">
								<div className="result-item">
									<span className="result-label">% Olhando para Frente:</span>
									<span className="result-value">{gazeAnalysis.metrics.percentage_forward.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">% Olhando para Cima:</span>
									<span className="result-value">{gazeAnalysis.metrics.percentage_up.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">% Olhando para Baixo:</span>
									<span className="result-value">{gazeAnalysis.metrics.percentage_down.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">% Olhando para Esquerda:</span>
									<span className="result-value">{gazeAnalysis.metrics.percentage_left.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">% Olhando para Direita:</span>
									<span className="result-value">{gazeAnalysis.metrics.percentage_right.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">% Sem Rosto Detectado:</span>
									<span className="result-value">{gazeAnalysis.metrics.percentage_no_face.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">Total de Trocas de Posição:</span>
									<span className="result-value">{gazeAnalysis.metrics.total_position_changes}</span>
								</div>
								<div className="result-item">
									<span className="result-label">Trocas de Posição / Minuto:</span>
									<span className="result-value">{gazeAnalysis.metrics.position_changes_per_minute.toFixed(2)}</span>
								</div>
							</div>
						</div>
					)}

					{audioAnalysis && audioAnalysis.status === 'completed' && audioAnalysis.results && (
						<div className="analysis-results audio">
							<h3>Análise de Áudio</h3>
							<div className="results-grid">
								<div className="result-item">
									<span className="result-label">Pessoas Detectadas:</span>
									<span className="result-value">{audioAnalysis.results.total_speakers}</span>
								</div>
								<div className="result-item">
									<span className="result-label">Múltiplos Falantes:</span>
									<span className="result-value">
										{audioAnalysis.results.has_multiple_speakers ? ' Sim' : ' Não'}
									</span>
								</div>
								<div className="result-item">
									<span className="result-label">% de Silêncio:</span>
									<span className="result-value">{audioAnalysis.results.silence_percentage?.toFixed(1)}%</span>
								</div>
								<div className="result-item">
									<span className="result-label">Duração Total:</span>
									<span className="result-value">{audioAnalysis.results.total_duration_seconds?.toFixed(0)}s</span>
								</div>
							</div>
						</div>
					)}

					{keystrokeAnalysis && keystrokeAnalysis.status === 'completed' && keystrokeAnalysis.typing_metrics && (
						<div className="analysis-results keystroke">
							<h3>Análise de Teclado</h3>
							<div className="results-grid">
								<div className="result-item">
									<span className="result-label">Total de Eventos:</span>
									<span className="result-value">{keystrokeAnalysis.typing_metrics.total_events}</span>
								</div>
								<div className="result-item">
									<span className="result-label">Pressão média:</span>
									<span className="result-value">{keystrokeAnalysis.typing_metrics.hold_time_avg?.toFixed(3)}s</span>
								</div>
								<div className="result-item">
									<span className="result-label">Voo médio:</span>
									<span className="result-value">{keystrokeAnalysis.typing_metrics.flight_time_avg?.toFixed(3)}s</span>
								</div>
								{keystrokeAnalysis.suspicious_commands && (
									<div className="result-item">
										<span className="result-label">Score Suspeito:</span>
										<span className="result-value">{keystrokeAnalysis.suspicious_commands.suspicious_percentage?.toFixed(1)}%</span>
									</div>
								)}
							</div>
						</div>
					)}
				</div>
			</main>

			{showVideoModal && (
				<div className="video-modal-overlay" onClick={() => setShowVideoModal(false)}>
					<div className="video-modal-content" onClick={e => e.stopPropagation()}>
						<button className="close-modal" onClick={() => setShowVideoModal(false)}>
							<XCircle size={24} />
						</button>
						<h2>Gravação da Prova</h2>
						{videoBlob ? (
							<video src={videoBlob} controls autoPlay className="full-video-player" />
						) : (
							<div className="loading-video">
								<Loader2 className="spinning" size={48} />
								<p>Carregando vídeo...</p>
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
}
