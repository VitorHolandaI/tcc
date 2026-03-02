import ApiMethods from "./ApiMethods";

export type Prova = {
  id: number;
  titulo: string;
  descricao: string | null;
  data_aplicacao: string;
  professor_id: number;
  linguagem: string;
};

class ProvaService {
  /**
   * Get scheduled provas for the authenticated professor
   */
  static async getProfessorProvasAgendadas(token: string): Promise<Prova[]> {
    return ApiMethods.get("/provas/me/agendadas", token) as Promise<Prova[]>;
  }

  /**
   * Get past provas for the authenticated professor
   */
  static async getProfessorProvasPassadas(token: string): Promise<Prova[]> {
    return ApiMethods.get("/provas/me/passadas", token) as Promise<Prova[]>;
  }

  /**
   * Get all provas for the authenticated professor
   */
  static async getProfessorTodasProvas(token: string): Promise<Prova[]> {
    return ApiMethods.get("/provas/me/todas", token) as Promise<Prova[]>;
  }

  /**
   * Get scheduled provas for the authenticated aluno
   */
  static async getAlunoProvasAgendadas(token: string): Promise<Prova[]> {
    return ApiMethods.get("/provas/aluno/agendadas", token) as Promise<Prova[]>;
  }

  /**
   * Get past provas for the authenticated aluno
   */
  static async getAlunoProvasPassadas(token: string): Promise<Prova[]> {
    return ApiMethods.get("/provas/aluno/passadas", token) as Promise<Prova[]>;
  }

  /**
   * Create a new prova (professor only)
   */
  static async createProva(token: string, prova: {
    titulo: string;
    descricao?: string;
    data_aplicacao: string;
    professor_id: number;
    linguagem: string;
  }): Promise<Prova> {
    return ApiMethods.post("/provas/", prova, token) as Promise<Prova>;
  }

  /**
   * Get a specific prova by ID
   */
  static async getProvaById(provaId: number, token?: string): Promise<Prova> {
    return ApiMethods.get(`/provas/${provaId}`, token) as Promise<Prova>;
  }

  /**
   * Update a prova
   */
  static async updateProva(provaId: number, prova: any, token: string): Promise<Prova> {
    return ApiMethods.put(`/provas/${provaId}`, prova, token) as Promise<Prova>;
  }

  /**
   * Delete a prova
   */
  static async deleteProva(provaId: number, token: string): Promise<void> {
    return ApiMethods.delete(`/provas/${provaId}`, token) as Promise<void>;
  }
}

export default ProvaService;
