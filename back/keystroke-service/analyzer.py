import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import zscore
from datetime import datetime, timedelta
import os
import sys
from collections import Counter
from report_generator import ReportGenerator
import io

class KeyloggerAnalyzer:
    def __init__(self, json_file):
        self.json_file = json_file
        self.data = None
        self.load_data()
        
    def load_data(self):
        """Carrega os dados do arquivo JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar o arquivo: {e}")
            sys.exit(1)
    
    def calculate_typing_metrics(self):
        """Calcula métricas de digitação"""
        valid_events = [event for event in self.data if 'hold_time' in event and event['hold_time'] is not None]
        
        if not valid_events:
            return {
                "hold_time_avg": 0,
                "hold_time_std": 0,
                "flight_time_avg": 0,
                "flight_time_std": 0,
                "total_events": 0
            }
        
        hold_times = [event['hold_time'] for event in valid_events if event['hold_time'] is not None]
        flight_times = [event['flight_time'] for event in valid_events if event['flight_time'] is not None]
        
        hold_time_avg = np.mean(hold_times) if hold_times else 0
        hold_time_std = np.std(hold_times) if hold_times else 0
        flight_time_avg = np.mean(flight_times) if flight_times else 0
        flight_time_std = np.std(flight_times) if flight_times else 0
        
        return {
            "hold_time_avg": round(hold_time_avg, 3),
            "hold_time_std": round(hold_time_std, 3),
            "flight_time_avg": round(flight_time_avg, 3),
            "flight_time_std": round(flight_time_std, 3),
            "total_events": len(valid_events)
        }
    
    def analyze_suspicious_commands(self):
        """Analisa a frequência de comandos suspeitos e sua distância de Manhattan"""
        suspicious_commands = ["paste", "copy", "cut", "backspace", "cursor_movement"]
        
        command_counts = Counter()
        command_sequences = []
        current_sequence = []
        
        for event in self.data:
            if event.get('command_type') in suspicious_commands:
                current_sequence.append(event)
                command_counts[event['command_type']] += 1
            elif current_sequence:
                command_sequences.append(current_sequence)
                current_sequence = []
        
        if current_sequence:
            command_sequences.append(current_sequence)
        
        manhattan_distances = []
        for sequence in command_sequences:
            if len(sequence) > 1:
                distance = self._calculate_sequence_manhattan(sequence)
                manhattan_distances.append(distance)
        
        total_commands = sum(command_counts.values())
        total_events = len(self.data)
        suspicious_percentage = (total_commands / total_events * 100) if total_events > 0 else 0
        
        avg_manhattan = sum(manhattan_distances) / len(manhattan_distances) if manhattan_distances else 0
        
        return {
            "command_counts": dict(command_counts),
            "suspicious_percentage": round(suspicious_percentage, 2),
            "total_commands": total_commands,
            "avg_manhattan_distance": round(avg_manhattan, 2),
            "command_sequences": len(command_sequences)
        }
    
    def _calculate_sequence_manhattan(self, sequence):
        """Calcula a distância de Manhattan para uma sequência de comandos"""
        if len(sequence) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_event = sequence[i + 1]

            try:
                t1 = datetime.strptime(current['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                t2 = datetime.strptime(next_event['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            except Exception:
                continue  # Pula se o timestamp for inválido

            time_diff = abs((t2 - t1).total_seconds())
            hold_diff = abs((next_event.get('hold_time') or 0) - (current.get('hold_time') or 0))
            flight_diff = abs((next_event.get('flight_time') or 0) - (current.get('flight_time') or 0))

            total_distance += time_diff + hold_diff + flight_diff

        return total_distance

    
    def calculate_manhattan_distance(self):
        """Calcula a distância de Manhattan para avaliar o padrão comportamental"""
        app_events = {}
        for event in self.data:
            app = event.get('application', 'Unknown')
            if app not in app_events:
                app_events[app] = []
            app_events[app].append(event)
        
        app_metrics = {}
        for app, events in app_events.items():
            if len(events) >= 2:
                start_time = datetime.strptime(events[0]['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                end_time = datetime.strptime(events[-1]['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                duration = (end_time - start_time).total_seconds()
                
                typing_rate = len(events) / duration if duration > 0 else 0
                
                suspicious_count = sum(1 for e in events if e.get('command_type') in ["paste", "copy", "cut"])
                suspicious_ratio = suspicious_count / len(events) if len(events) > 0 else 0
                
                app_metrics[app] = {
                    "duration": round(duration, 2),
                    "typing_rate": round(typing_rate, 2),
                    "suspicious_ratio": round(suspicious_ratio, 2),
                    "event_count": len(events)
                }
        
        return app_metrics

    def calculate_outlier_count(self, threshold=3.0):
        """Conta quantos tempos de digitação são outliers com base no Z-score"""
        hold_times = np.array([event['hold_time'] for event in self.data if 'hold_time' in event and event['hold_time'] is not None])
        flight_times = np.array([event['flight_time'] for event in self.data if 'flight_time' in event and event['flight_time'] is not None])
        
        outliers = {
            "hold_time_outliers": 0,
            "flight_time_outliers": 0
        }

        if len(hold_times) > 1:
            hold_z = zscore(hold_times)
            outliers["hold_time_outliers"] = int(np.sum(np.abs(hold_z) > threshold))

        if len(flight_times) > 1:
            flight_z = zscore(flight_times)
            outliers["flight_time_outliers"] = int(np.sum(np.abs(flight_z) > threshold))

        return outliers


    def _format_key(self, key):
        """Formata a tecla para exibição legível"""
        if isinstance(key, str) and not key.startswith('Key.'):
            if key.lower() in ['c', 'v', 'x']:
                return f'[{key.upper()}]'
            return key
        
        if isinstance(key, str) and key.startswith('Key.'):
            key = key[4:]
            
            special_keys = {
                'space': ' ',
                'enter': '  ↵  ',
                'tab': '  →|  ',
                'backspace': '  |←  ',
                'delete': '  del  ',
                'up': '  ↑  ',
                'down': '  ↓  ',
                'left': '  ←  ',
                'right': '  →  ',
                'shift': '',
                'shift_r': '',
                'shift_l': '',
                'ctrl': '',
                'ctrl_l': '',
                'ctrl_r': '',
                'alt': '',
                'alt_l': '',
                'alt_r': '',
                'cmd': '',
                'cmd_l': '',
                'cmd_r': ''
            }
            return special_keys.get(key, '')
        
        return ''

    def analyze_text_segments(self):
        """Analisa os trechos de texto e comandos para identificar padrões de digitação"""
        segments = []
        current_segment = []
        current_text = []
        last_event_time = None
        segment_start_time = None
        last_was_ctrl = False
        
        typing_metrics = self.calculate_typing_metrics()
        base_hold_time = typing_metrics['hold_time_avg']
        base_flight_time = typing_metrics['flight_time_avg']
        
        segment_events = []
        
        for i, event in enumerate(self.data):
            current_time = datetime.strptime(event['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            
            if event.get('key') in ['Key.ctrl', 'Key.ctrl_l', 'Key.ctrl_r', 'Key.cmd', 'Key.cmd_l', 'Key.cmd_r']:
                last_was_ctrl = True
                continue
            
            if last_was_ctrl and event.get('key') in ['c', 'v', 'x']:
                if current_text:
                    is_suspicious = self._analyze_segment_manhattan(segment_events, base_hold_time, base_flight_time)
                    segments.append({
                        'type': 'typing',
                        'text': ''.join(current_text),
                        'start_time': segment_start_time,
                        'end_time': last_event_time,
                        'is_suspicious': is_suspicious
                    })
                    current_text = []
                    segment_events = []
                
                command_type = {'c': 'copy', 'v': 'paste', 'x': 'cut'}[event['key']]
                segments.append({
                    'type': 'command',
                    'command': command_type,
                    'time': event['timestamp']
                })
                
                last_was_ctrl = False
                continue
            
            last_was_ctrl = False
            
            if event.get('key'):
                if not current_text:
                    segment_start_time = current_time
                
                if last_event_time and (current_time - last_event_time).total_seconds() > 2.0:
                    if current_text:
                        is_suspicious = self._analyze_segment_manhattan(segment_events, base_hold_time, base_flight_time)
                        segments.append({
                            'type': 'typing',
                            'text': ''.join(current_text),
                            'start_time': segment_start_time,
                            'end_time': last_event_time,
                            'is_suspicious': is_suspicious
                        })
                        current_text = []
                        segment_events = []
                    segment_start_time = current_time
                
                formatted_key = self._format_key(event['key'])
                if formatted_key:
                    current_text.append(formatted_key)
                    segment_events.append(event)
                
                last_event_time = current_time
        
        if current_text:
            is_suspicious = self._analyze_segment_manhattan(segment_events, base_hold_time, base_flight_time)
            segments.append({
                'type': 'typing',
                'text': ''.join(current_text),
                'start_time': segment_start_time,
                'end_time': last_event_time,
                'is_suspicious': is_suspicious
            })
        
        return segments

    def _analyze_segment_manhattan(self, events, base_hold_time, base_flight_time):
        """Analisa um segmento de texto usando distância de Manhattan para determinar se é suspeito"""
        if len(events) < 2:
            return False
            
        hold_times = [event['hold_time'] for event in events if 'hold_time' in event and event['hold_time'] is not None]
        flight_times = [event['flight_time'] for event in events if 'flight_time' in event and event['flight_time'] is not None]
        
        if not hold_times or not flight_times:
            return False
            
        segment_hold_avg = np.mean(hold_times)
        segment_flight_avg = np.mean(flight_times)
        
        manhattan_distance = abs(segment_hold_avg - base_hold_time) + abs(segment_flight_avg - base_flight_time)
        
        threshold = (base_hold_time + base_flight_time) * 0.5
        
        return manhattan_distance > threshold
    
    def generate_report(self):
        """Gera um relatório completo da análise"""
        typing_metrics = self.calculate_typing_metrics()
        suspicious_analysis = self.analyze_suspicious_commands()
        manhattan_metrics = self.calculate_manhattan_distance()
        text_segments = self.analyze_text_segments()
        outlier_counts = self.calculate_outlier_count()

        total_typing_segments = sum(1 for seg in text_segments if seg["type"] == "typing")
        suspicious_typing_segments = sum(1 for seg in text_segments if seg["type"] == "typing" and seg.get("is_suspicious"))
        suspicious_typing_ratio = (suspicious_typing_segments / total_typing_segments * 100) if total_typing_segments > 0 else 0

        is_suspicious = False
        suspicious_reasons = []
        
        if suspicious_analysis["suspicious_percentage"] > 5 or suspicious_analysis["total_commands"] > 0:
            is_suspicious = True
            if suspicious_analysis["total_commands"] > 0:
                suspicious_reasons.append(f"Comandos suspeitos detectados: {suspicious_analysis['total_commands']} ({suspicious_analysis['suspicious_percentage']}%)")
                if suspicious_analysis["avg_manhattan_distance"] > 0:
                    suspicious_reasons.append(f"Distância de Manhattan média: {suspicious_analysis['avg_manhattan_distance']:.2f}")
        
        if typing_metrics["hold_time_std"] > 0.2 or typing_metrics["flight_time_std"] > 0.3:
            is_suspicious = True
            suspicious_reasons.append("Padrão de digitação irregular (alta variabilidade)")
        
        if len(manhattan_metrics) > 5:
            is_suspicious = True
            suspicious_reasons.append(f"Muitas aplicações diferentes utilizadas: {len(manhattan_metrics)}")
        
        if suspicious_typing_ratio > 30:
            is_suspicious = True
            suspicious_reasons.append(f"{suspicious_typing_segments} de {total_typing_segments} trechos de digitação marcados como suspeitos ({suspicious_typing_ratio:.2f}%)")

        if outlier_counts["hold_time_outliers"] > 5 or outlier_counts["flight_time_outliers"] > 5:
            is_suspicious = True
            suspicious_reasons.append(f"Outliers detectados: {outlier_counts['hold_time_outliers']} em hold time e {outlier_counts['flight_time_outliers']} em flight time")

        report = {
            "file_analyzed": self.json_file,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "typing_metrics": typing_metrics,
            "suspicious_commands": suspicious_analysis,
            "application_metrics": manhattan_metrics,
            "text_segments": text_segments,
            "is_suspicious": is_suspicious,
            "suspicious_typing_ratio": round(suspicious_typing_ratio, 2),
            "suspicious_reasons": suspicious_reasons,
            "outlier_counts": outlier_counts,
            "conclusion": "ATENÇÃO NECESSÁRIA" if is_suspicious else "COMPORTAMENTO NORMAL"
        }
        
        return report
    
    def plot_typing_patterns(self):
        """Gera gráfico de frequência de digitação ao longo do tempo"""
        timestamps = []
        for event in self.data:
            if 'timestamp' in event:
                try:
                    if isinstance(event['timestamp'], str):
                        try:
                            ts = datetime.strptime(event['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                ts = datetime.strptime(event['timestamp'], "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                ts = datetime.fromtimestamp(float(event['timestamp']))
                    else:
                        ts = datetime.fromtimestamp(float(event['timestamp']))
                    timestamps.append(ts.timestamp())
                except (ValueError, TypeError):
                    continue

        if not timestamps:
            return None
            
        start_time = datetime.fromtimestamp(min(timestamps))
        end_time = datetime.fromtimestamp(max(timestamps))
        
        total_duration = (end_time - start_time).total_seconds()
        
        if total_duration <= 300:  # 5 minutes or less
            window_size = 3  # 5 seconds
        elif total_duration <= 1800:  # 30 minutes or less
            window_size = 5  # 15 seconds
        elif total_duration <= 3600:  # 1 hour or less
            window_size = 10  # 30 seconds
        else:
            window_size = 60  # 1 minute
        
        time_windows = []
        current_time = start_time
        while current_time <= end_time:
            time_windows.append(current_time)
            current_time += timedelta(seconds=window_size)
        
        event_counts = []
        for i in range(len(time_windows) - 1):
            window_start = time_windows[i].timestamp()
            window_end = time_windows[i + 1].timestamp()
            count = sum(1 for ts in timestamps if window_start <= ts < window_end)
            event_counts.append(count)
        
        plt.figure(figsize=(15, 8))
        
        points = plt.plot(time_windows[:-1], event_counts, marker='o', linestyle='-', markersize=4, alpha=0.7)
        
        cmap = plt.cm.viridis
        norm = plt.Normalize(min(event_counts), max(event_counts))
        for i in range(len(event_counts)-1):
            plt.plot([time_windows[i], time_windows[i+1]], 
                    [event_counts[i], event_counts[i+1]], 
                    color=cmap(norm(event_counts[i])), 
                    linewidth=2)
        
        scatter = plt.scatter(time_windows[:-1], event_counts, 
                            c=event_counts, 
                            cmap=cmap, 
                            norm=norm,
                            s=50, 
                            alpha=0.6)
        
        plt.colorbar(scatter, label='Frequência de Digitação')
        
        plt.title('Frequência de Digitação ao Longo do Tempo', pad=20, fontsize=14)
        plt.xlabel('Tempo', labelpad=10, fontsize=12)
        plt.ylabel('Número de Teclas Digitadas', labelpad=10, fontsize=12)
        
        plt.gcf().autofmt_xdate()  # Rotate and align the tick labels
        plt.grid(True, linestyle='--', alpha=0.3)
        
        plt.margins(y=0.1)
        
        window_text = f"Janela de tempo: {window_size} segundos"
        plt.figtext(0.02, 0.02, window_text, fontsize=10, style='italic')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf

    def generate_pdf_report(self, report, output_file="analysis_report.pdf"):
        """Gera um relatório em PDF"""
        graph_data = self.plot_typing_patterns()
        report['graph_data'] = graph_data
        
        generator = ReportGenerator(report, output_file)
        return generator.generate_pdf()

def process_json_files(input_path, output_dir):
    """Processa arquivos JSON (seja um arquivo único ou um diretório com múltiplos arquivos)"""
    if not os.path.exists(input_path):
        print(f"Caminho não encontrado: {input_path}")
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório de saída criado: {output_dir}")
    
    if os.path.isfile(input_path):
        if input_path.endswith('.json'):
            json_files = [input_path]
            input_dir = os.path.dirname(input_path)
        else:
            print(f"O arquivo {input_path} não é um arquivo JSON")
            sys.exit(1)
    else:
        input_dir = input_path
        all_files = os.listdir(input_dir)
        json_files = [os.path.join(input_dir, f) for f in all_files 
                     if f.endswith('.json') and os.path.isfile(os.path.join(input_dir, f))]
    
    if not json_files:
        print(f"Nenhum arquivo JSON encontrado em: {input_path}")
        sys.exit(1)
    
    for json_file_path in json_files:
        try:
            json_file_name = os.path.basename(json_file_path)
            file_name_without_ext = os.path.splitext(json_file_name)[0]
            
            output_file = os.path.join(output_dir, f"{file_name_without_ext}_report.pdf")
            
            analyzer = KeyloggerAnalyzer(json_file_path)
            report = analyzer.generate_report()
            
            analyzer.generate_pdf_report(report, output_file)
                        
            if report['is_suspicious']:
                print("\nRazões para suspeita:")
                for reason in report['suspicious_reasons']:
                    print(f"- {reason}")
            
        except Exception as e:
            print(f"Erro ao processar o arquivo {json_file_name}: {e}")
            continue
    
def main():
    if len(sys.argv) < 2:
        print("Uso: python analyzer.py arquivo_ou_diretorio")
        print("     python analyzer.py arquivo.json")
        print("     python analyzer.py diretorio/")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = "output"
    
    process_json_files(input_path, output_dir)

if __name__ == "__main__":
    main()