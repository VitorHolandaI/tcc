import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import {
	signInWithPopup,
	signOut,
	onAuthStateChanged,
	type User  // <-- importa como type
} from "firebase/auth";
import { auth, googleProvider } from "../config/firebase";
import ApiManagerAuth from "../services/ApiManagerAuth";

type UserType = "professor" | "aluno" | null;

interface BackendUser {
	id: number;
	nome: string;
	email: string;
	matricula?: string;
}

interface AuthContextType {
	user: User | null;
	userType: UserType;
	backendUser: BackendUser | null;
	loading: boolean;
	signInWithGoogle: () => Promise<void>;
	logout: () => Promise<void>;
	getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);
//does not realy matter since i cant display page dependen on what the front end shows but from that the back end getes and displays
//how to work with auth and diferent types of users acess to certain pages or not
//TODO
function isProfessorEmail(email: string): boolean {
	const PROFESSOR_WHITELIST = new Set(["vitor.holanda@ccc.ufcg.edu.br"]);
	return email.endsWith("@computacao.ufcg.edu.br") || PROFESSOR_WHITELIST.has(email);
}

function generateMatricula(): string {
	return `ALU${Date.now().toString().slice(-8)}`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
	const [user, setUser] = useState<User | null>(null);
	const [userType, setUserType] = useState<UserType>(null);
	const [backendUser, setBackendUser] = useState<BackendUser | null>(null);
	const [loading, setLoading] = useState(true);

	const registerOrFetchUser = async (firebaseUser: User) => {
		const email = firebaseUser.email || "";
		const nome = firebaseUser.displayName || "Usuário";
		const isProfessor = isProfessorEmail(email);

		try {
			if (isProfessor) {
				// POST /professores/ already does get_or_create on backend
				const professor = await ApiManagerAuth.createProfessor({ nome, email });
				setUserType("professor");
				setBackendUser(professor);
			} else {
				// POST /alunos/ already does get_or_create on backend
				const matricula = generateMatricula();
				const aluno = await ApiManagerAuth.createAluno({ nome, email, matricula });
				setUserType("aluno");
				setBackendUser(aluno);
			}
		} catch (error) {
			console.error("Erro ao registrar/buscar usuário:", error);
		}
	};

	useEffect(() => {
		const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
			setUser(firebaseUser);

			if (firebaseUser?.email) {
				await registerOrFetchUser(firebaseUser);
			} else {
				setUserType(null);
				setBackendUser(null);
			}

			setLoading(false);
		});

		return unsubscribe;
	}, []);

	const signInWithGoogle = async () => {
		const result = await signInWithPopup(auth, googleProvider);
		if (result.user) {
			await registerOrFetchUser(result.user);
		}
	};

	const logout = async () => {
		await signOut(auth);
		setUserType(null);
		setBackendUser(null);
	};

	const getIdToken = async () => {
		return user ? await user.getIdToken() : null;
	};

	return (
		<AuthContext.Provider value={{ user, userType, backendUser, loading, signInWithGoogle, logout, getIdToken }}>
			{children}
		</AuthContext.Provider>
	);
}

export function useAuth() {
	const context = useContext(AuthContext);
	if (!context) {
		throw new Error("useAuth deve ser usado dentro de um AuthProvider");
	}
	return context;
}
