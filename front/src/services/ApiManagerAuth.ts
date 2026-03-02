import ENDPOINTS from "./Endpoints";
import ApiMethods from "./ApiMethods";

export interface ProfessorData {
	nome: string;
	email: string;
}

export interface AlunoData {
	nome: string;
	email: string;
	matricula: string;
}

export interface Professor extends ProfessorData {
	id: number;
}

export interface Aluno extends AlunoData {
	id: number;
}

class ApiManagerAuth {
	// Professores
	static createProfessor = (data: ProfessorData): Promise<Professor> => {
		const url = ENDPOINTS.PROFESSORES();
		return ApiMethods.post(url, data) as Promise<Professor>;
	};

	static getProfessorByEmail = (email: string): Promise<Professor | null> => {
		const url = ENDPOINTS.PROFESSOR_BY_EMAIL(email);
		return ApiMethods.get(url) as Promise<Professor | null>;
	};

	// Alunos
	static createAluno = (data: AlunoData): Promise<Aluno> => {
		const url = ENDPOINTS.ALUNOS();
		return ApiMethods.post(url, data) as Promise<Aluno>;
	};

	static getAlunoByEmail = (email: string): Promise<Aluno | null> => {
		const url = ENDPOINTS.ALUNO_BY_EMAIL(email);
		return ApiMethods.get(url) as Promise<Aluno | null>;
	};
}

export default ApiManagerAuth;
