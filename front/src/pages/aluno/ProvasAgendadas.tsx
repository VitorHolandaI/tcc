import { useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import ProvaService, { type Prova } from "../../services/ProvaService";
import { ArrowLeft, Calendar, BookOpen } from "lucide-react";

export default function AlunoProvasAgendadas() {
	const { getIdToken, userType } = useAuth();
	const navigate = useNavigate();
	const [provas, setProvas] = useState<Prova[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		if (userType !== "aluno") {
			navigate("/dashboard/aluno");
			return;
		}

		loadProvas();
	}, [userType]);

	const loadProvas = async () => {
		try {
			setLoading(true);
			const token = await getIdToken();
			if (!token) {
				setError("Token não encontrado. Faça login novamente.");
				return;
			}

			const data = await ProvaService.getAlunoProvasAgendadas(token);
			setProvas(data || []);
		} catch (err: any) {
			setError(err.message || "Erro ao carregar provas");
		} finally {
			setLoading(false);
		}
	};

	if (loading) {
		return (
			<div className="min-h-screen flex items-center justify-center">
				<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 p-8">
			<div className="max-w-6xl mx-auto">
				<button
					onClick={() => navigate("/dashboard/aluno")}
					className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
				>
					<ArrowLeft size={20} />
					<span>Voltar ao Dashboard</span>
				</button>

				<div className="bg-white rounded-2xl shadow-lg p-8">
					<div className="flex items-center gap-3 mb-6">
						<Calendar className="text-blue-600" size={32} />
						<h1 className="text-3xl font-bold text-gray-900">Provas Agendadas</h1>
					</div>

					{error && (
						<div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
							{error}
						</div>
					)}

					{provas.length === 0 ? (
						<div className="text-center py-12">
							<BookOpen className="mx-auto text-gray-400 mb-4" size={48} />
							<p className="text-gray-500 text-lg">Nenhuma prova agendada disponível</p>
							<p className="text-gray-400 text-sm mt-2">
								Aguarde seu professor agendar novas provas
							</p>
						</div>
					) : (
						<div className="space-y-4">
							{provas.map((prova) => (
								<div
									key={prova.id}
									className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
									onClick={() => navigate(`/aluno/prova/${prova.id}`)}
								>
									<div className="flex justify-between items-start">
										<div className="flex-1">
											<h3 className="text-xl font-bold text-gray-900 mb-2">
												{prova.titulo}
											</h3>
											{prova.descricao && (
												<p className="text-gray-600 mb-3">{prova.descricao}</p>
											)}
											<div className="flex items-center gap-4 text-sm text-gray-500">
												<span className="flex items-center gap-1">
													<Calendar size={16} />
													Data: {new Date(prova.data_aplicacao + "Z").toLocaleDateString('pt-BR')}
												</span>
												<span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
													{prova.linguagem}
												</span>
											</div>
										</div>
										<button
											className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
											onClick={(e) => {
												e.stopPropagation();
												navigate(`/aluno/prova/${prova.id}`);
											}}
										>
											Iniciar Prova
										</button>
									</div>
								</div>
							))}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
