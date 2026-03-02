import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Play } from "lucide-react";
import "../css/FazerProva.css";

interface Questao {
    id: number;
    titulo: string;
    descricao: string;
    exemplo_input1: string;
    exemplo_output1: string;
    exemplo_input2: string | null;
    exemplo_output2: string | null;
    peso: number;
    prova_id: number;
}

// Mock de uma questão para UI
const mockQuestao: Questao = {
    id: 1,
    titulo: "Soma de Dois Números",
    descricao: "Escreva uma função que receba dois números como entrada e retorne sua soma.",
    exemplo_input1: "2, 3",
    exemplo_output1: "5",
    exemplo_input2: "-1, 1",
    exemplo_output2: "0",
    peso: 10,
    prova_id: 1,
};

export default function FazerProva() {
    const { prova_id: _prova_id } = useParams<{ prova_id: string }>();
    const navigate = useNavigate();

    const [questoes] = useState<Questao[]>([mockQuestao]);
    const [currentQuestaoIndex] = useState(0);
    const [codigo, setCodigo] = useState("");
    const [output, setOutput] = useState("Clique em 'Executar' para ver o resultado do seu código.");
    const [running, setRunning] = useState(false);

    const currentQuestao = questoes[currentQuestaoIndex];

    const handleRunCode = async () => {
        setRunning(true);
        setOutput("Executando...");
        // Simula uma chamada de API para executar o código
        await new Promise(resolve => setTimeout(resolve, 1500));
        setOutput(`Saída para o input "${currentQuestao.exemplo_input1}":\n> 5`);
        setRunning(false);
    };

    return (
        <div className="exam-container">
            <header className="exam-header">
                <div className="exam-info">
                    <h2>{"Carregando prova..."}</h2>
                </div>
                <div className="exam-timer">29:59</div>
                <button className="btn-finish" onClick={() => navigate('/dashboard/aluno')}>Finalizar Prova</button>
            </header>

            <div className="workspace">
                {/* Painel da Questão */}
                <div className="question-panel">
                    <div className="question-content">
                        <h1 className="question-title">{currentQuestao.titulo}</h1>
                        <p className="question-desc">{currentQuestao.descricao}</p>
                        
                        <div className="examples-box">
                            <span className="example-label">Exemplo 1</span>
                            <pre className="code-block">Input: {currentQuestao.exemplo_input1}</pre>
                            <pre className="code-block">Output: {currentQuestao.exemplo_output1}</pre>
                        </div>

                        {currentQuestao.exemplo_input2 &&
                            <div className="examples-box">
                                <span className="example-label">Exemplo 2</span>
                                <pre className="code-block">Input: {currentQuestao.exemplo_input2}</pre>
                                <pre className="code-block">Output: {currentQuestao.exemplo_output2}</pre>
                            </div>
                        }
                    </div>
                    <div className="question-nav">
                        <button className="btn-nav" disabled={currentQuestaoIndex === 0}>
                            <ArrowLeft size={16}/> Anterior
                        </button>
                        <span>Questão {currentQuestaoIndex + 1} de {questoes.length}</span>
                        <button className="btn-nav" disabled={currentQuestaoIndex === questoes.length - 1}>
                            Próxima <ArrowRight size={16}/>
                        </button>
                    </div>
                </div>

                {/* Painel do Editor */}
                <div className="editor-panel">
                    <div className="code-editor-container">
                        <textarea
                            className="code-textarea"
                            value={codigo}
                            onChange={(e) => setCodigo(e.target.value)}
                            placeholder="Escreva seu código aqui..."
                        />
                    </div>
                    <div className="output-panel">
                        <div className="output-header">
                            <span>Saída</span>
                            <button className="btn-run" onClick={handleRunCode} disabled={running}>
                                <Play size={12}/> {running ? "Executando..." : "Executar"}
                            </button>
                        </div>
                        <pre className="output-content">{output}</pre>
                    </div>
                </div>
            </div>
        </div>
    );
}
