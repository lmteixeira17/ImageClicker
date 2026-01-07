"""
Rastreador de estatísticas de execução de tasks.
Persiste estatísticas em JSON para análise e dashboard.
"""

import json
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TaskStats:
    """Estatísticas de uma task individual."""

    total_executions: int = 0
    successful_clicks: int = 0
    failed_matches: int = 0
    total_match_time_ms: float = 0.0
    last_execution: Optional[str] = None
    hourly_executions: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def success_rate(self) -> float:
        """Taxa de sucesso (0.0 a 1.0)."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_clicks / self.total_executions

    @property
    def avg_match_time_ms(self) -> float:
        """Tempo médio de match em milissegundos."""
        if self.total_executions == 0:
            return 0.0
        return self.total_match_time_ms / self.total_executions

    def to_dict(self) -> dict:
        """Serializa para dicionário."""
        return {
            "total_executions": self.total_executions,
            "successful_clicks": self.successful_clicks,
            "failed_matches": self.failed_matches,
            "total_match_time_ms": self.total_match_time_ms,
            "last_execution": self.last_execution,
            "hourly_executions": dict(self.hourly_executions)
        }

    @staticmethod
    def from_dict(data: dict) -> 'TaskStats':
        """Cria a partir de dicionário."""
        stats = TaskStats(
            total_executions=data.get("total_executions", 0),
            successful_clicks=data.get("successful_clicks", 0),
            failed_matches=data.get("failed_matches", 0),
            total_match_time_ms=data.get("total_match_time_ms", 0.0),
            last_execution=data.get("last_execution")
        )
        hourly = data.get("hourly_executions", {})
        stats.hourly_executions = defaultdict(int, {int(k): v for k, v in hourly.items()})
        return stats


class StatsTracker:
    """
    Rastreia estatísticas de execução de tasks.

    Armazena:
    - Total de execuções por task
    - Taxa de sucesso
    - Tempo médio de match
    - Distribuição por hora (últimas 24h)
    """

    def __init__(self, stats_file: Path):
        """
        Inicializa o rastreador.

        Args:
            stats_file: Caminho para arquivo JSON de persistência
        """
        self.stats_file = stats_file
        self._stats: Dict[int, TaskStats] = {}
        self._global_stats = TaskStats()
        self._lock = threading.Lock()
        self._load()

    def record_execution(self, task_id: int, success: bool, match_time_ms: float):
        """
        Registra uma execução de task.

        Args:
            task_id: ID da task
            success: Se o clique foi bem-sucedido
            match_time_ms: Tempo de match em milissegundos
        """
        with self._lock:
            # Estatísticas da task
            if task_id not in self._stats:
                self._stats[task_id] = TaskStats()

            stats = self._stats[task_id]
            stats.total_executions += 1
            stats.total_match_time_ms += match_time_ms
            stats.last_execution = datetime.now().isoformat()

            if success:
                stats.successful_clicks += 1
            else:
                stats.failed_matches += 1

            # Distribuição por hora
            hour = datetime.now().hour
            stats.hourly_executions[hour] += 1

            # Estatísticas globais
            self._global_stats.total_executions += 1
            self._global_stats.total_match_time_ms += match_time_ms
            if success:
                self._global_stats.successful_clicks += 1
            else:
                self._global_stats.failed_matches += 1
            self._global_stats.hourly_executions[hour] += 1
            self._global_stats.last_execution = stats.last_execution

        # Auto-save a cada 10 execuções
        if self._global_stats.total_executions % 10 == 0:
            self.save()

    def get_task_stats(self, task_id: int) -> TaskStats:
        """Retorna estatísticas de uma task específica."""
        with self._lock:
            return self._stats.get(task_id, TaskStats())

    def get_global_stats(self) -> dict:
        """
        Retorna estatísticas globais agregadas.

        Returns:
            Dict com: total_executions, success_rate, avg_match_time_ms, active_tasks
        """
        with self._lock:
            return {
                "total_executions": self._global_stats.total_executions,
                "successful_clicks": self._global_stats.successful_clicks,
                "failed_matches": self._global_stats.failed_matches,
                "success_rate": self._global_stats.success_rate,
                "avg_match_time_ms": self._global_stats.avg_match_time_ms,
                "active_tasks": len(self._stats),
                "last_execution": self._global_stats.last_execution
            }

    def get_hourly_distribution(self, hours: int = 24) -> Dict[int, int]:
        """
        Retorna distribuição de execuções por hora.

        Args:
            hours: Número de horas para retornar (padrão: 24)

        Returns:
            Dict mapeando hora (0-23) para número de execuções
        """
        with self._lock:
            current_hour = datetime.now().hour
            distribution = {}

            for i in range(hours):
                hour = (current_hour - i) % 24
                distribution[hour] = self._global_stats.hourly_executions.get(hour, 0)

            return distribution

    def get_recent_executions(self, limit: int = 10) -> List[dict]:
        """
        Retorna as execuções mais recentes.

        Args:
            limit: Número máximo de execuções a retornar

        Returns:
            Lista de dicts com informações das execuções
        """
        with self._lock:
            recent = []
            for task_id, stats in self._stats.items():
                if stats.last_execution:
                    recent.append({
                        "task_id": task_id,
                        "last_execution": stats.last_execution,
                        "success_rate": stats.success_rate,
                        "total": stats.total_executions
                    })

            # Ordena por última execução (mais recente primeiro)
            recent.sort(key=lambda x: x["last_execution"], reverse=True)
            return recent[:limit]

    def clear_stats(self, task_id: Optional[int] = None):
        """
        Limpa estatísticas.

        Args:
            task_id: Se fornecido, limpa apenas esta task. Senão, limpa todas.
        """
        with self._lock:
            if task_id is not None:
                if task_id in self._stats:
                    del self._stats[task_id]
            else:
                self._stats.clear()
                self._global_stats = TaskStats()
        self.save()

    def save(self):
        """Salva estatísticas em arquivo JSON."""
        with self._lock:
            data = {
                "global": self._global_stats.to_dict(),
                "tasks": {str(k): v.to_dict() for k, v in self._stats.items()}
            }

        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estatísticas: {e}")

    def _load(self):
        """Carrega estatísticas de arquivo JSON."""
        if not self.stats_file.exists():
            return

        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                if "global" in data:
                    self._global_stats = TaskStats.from_dict(data["global"])

                if "tasks" in data:
                    for task_id_str, task_data in data["tasks"].items():
                        self._stats[int(task_id_str)] = TaskStats.from_dict(task_data)

        except Exception as e:
            print(f"Erro ao carregar estatísticas: {e}")


def format_time_ago(iso_timestamp: str) -> str:
    """
    Formata timestamp ISO para "X min atrás", "X horas atrás", etc.

    Args:
        iso_timestamp: Timestamp em formato ISO

    Returns:
        String formatada
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()
        diff = now - dt

        if diff < timedelta(minutes=1):
            return "agora"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"{mins} min atrás"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h atrás"
        else:
            days = diff.days
            return f"{days}d atrás"
    except Exception:
        return "desconhecido"
