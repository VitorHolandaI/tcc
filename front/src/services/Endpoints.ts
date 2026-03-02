const ENDPOINTS = {
	// Provas
	PROVA: (userid: string) => `/users/${userid}/provas`,
	PROVA_DETAIL: (userid: string, provaid: number) => `/users/${userid}/provas/${provaid}`,

	// Professores
	PROFESSORES: () => `/professores/`,
	PROFESSOR_DETAIL: (id: number) => `/professores/${id}`,
	PROFESSOR_BY_EMAIL: (email: string) => `/professores/email/${email}`,

	// Alunos
	ALUNOS: () => `/alunos/`,
	ALUNO_DETAIL: (id: number) => `/alunos/${id}`,
	ALUNO_BY_EMAIL: (email: string) => `/alunos/email/${email}`,
};

export default ENDPOINTS;
