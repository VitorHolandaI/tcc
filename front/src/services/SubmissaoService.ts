import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

export interface SubmissaoPayload {
  prova_id: number;
  questao_id: number;
  codigo_submetido: string;
}

export interface SubmissaoResponse extends SubmissaoPayload {
  id: number;
  aluno_id: number;
  data_envio: string;
  resultado_execucao: string | null;
  finalizada: boolean;
}

class SubmissaoService {
  public async get(questao_id: number, token: string): Promise<SubmissaoResponse | null> {
    try {
      const response = await axios.get<SubmissaoResponse>(
        `${API_BASE_URL}/submissoes/${questao_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  public async enviar(
    payload: SubmissaoPayload,
    token: string
  ): Promise<SubmissaoResponse> {
    const response = await axios.post<SubmissaoResponse>(
      `${API_BASE_URL}/submissoes/`,
      payload,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return response.data;
  }

  public async finalizar(
    prova_id: number,
    submissoes: SubmissaoPayload[],
    token: string
  ): Promise<SubmissaoResponse[]> {
    const response = await axios.post<SubmissaoResponse[]>(
      `${API_BASE_URL}/submissoes/finalizar/${prova_id}`,
      submissoes,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return response.data;
  }
}

export const submissaoService = new SubmissaoService();
