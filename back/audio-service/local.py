"""
Script de Teste Local - Audio Speaker Diarization
"""
import os
import torch
from pyannote.audio import Pipeline
import json
from pathlib import Path

class MockConfig:
    HUGGINGFACE_TOKEN = "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"
    USE_GPU = True

config = MockConfig()

class AudioDiarizationAnalyzer:
    """Analyzes audio files for speaker diarization (Versão de Teste)"""

    def __init__(self):
        self.pipeline = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize pyannote.audio pipeline (VERSÃO ESTÁVEL)"""
        print(" Inicializando Pipeline...")
        try:
            if not config.HUGGINGFACE_TOKEN or config.HUGGINGFACE_TOKEN == "SEU_TOKEN_HUGGINGFACE_AQUI":
                print(" ERRO: Configure o HUGGINGFACE_TOKEN.")
                return
            
            try:
                from huggingface_hub import login
                login(token=config.HUGGINGFACE_TOKEN)
                print(" Login no Hugging Face realizado.")
            except ImportError:
                pass

            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=config.HUGGINGFACE_TOKEN 
            )

            if config.USE_GPU and torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                print(" Usando GPU")
            else:
                print("ℹ Usando CPU")
                
            print(" Pipeline carregado!")

        except Exception as e:
            print(f" Falha fatal: {e}")
            print("EXECUTE NO TERMINAL: pip install huggingface_hub==0.25.2")
            self.pipeline = None

    def analyze_audio(self, audio_path: Path):
        """
        Versão simplificada sem banco de dados
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if not self.pipeline:
            raise RuntimeError("Pipeline não inicializado.")

        try:
            print(f" Iniciando análise do arquivo: {audio_path.name}")

            diarization = self.pipeline(str(audio_path))

            speaker_timeline = []
            speakers_set = set()

            print("\n--- Timeline Detectada ---")
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                duration = turn.end - turn.start
                print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker={speaker}")
                
                speaker_timeline.append({
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "duration": float(duration),
                    "speaker": speaker
                })
                speakers_set.add(speaker)

            total_speakers = len(speakers_set)
            
            return {
                "status": "completed",
                "total_speakers": total_speakers,
                "speakers_list": list(speakers_set)
            }

        except Exception as e:
            print(f" Erro durante a análise: {e}")
            raise

if __name__ == "__main__":
    analyzer = AudioDiarizationAnalyzer()

    arquivo_teste = Path("teste.wav")

    if analyzer.pipeline:
        if arquivo_teste.exists():
            try:
                resultado = analyzer.analyze_audio(arquivo_teste)
                print("\n" + "="*30)
                print("RESULTADO FINAL:")
                print(json.dumps(resultado, indent=2))
                print("="*30)
            except Exception as e:
                print("Falha na execução.")
        else:
            print(f"\n Arquivo de áudio não encontrado: {arquivo_teste}")
            print("Crie um arquivo de áudio ou altere o caminho na variável 'arquivo_teste' no final do script.")
