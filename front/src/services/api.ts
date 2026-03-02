import { API_BASE_URL } from "./apiConfig";

const BASE_URL = API_BASE_URL;

export interface ServerResponse {
	received?: string;
	status?: string;
	message?: string;
}

export const examService = {
	submitExam: async (text: string): Promise<ServerResponse> => {
		const response = await fetch(`${BASE_URL}/data`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ userText: text }),
		});
		if (!response.ok) throw new Error('Failed to submit');
		return response.json();
	},

	getExamData: async () => {
		const response = await fetch(`${BASE_URL}/description`);
		if (!response.ok) throw new Error('Failed to fetch descriptions');
		return response.json();
	}
};

