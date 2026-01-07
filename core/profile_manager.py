"""
Gerenciador de profiles (workspaces).
Permite salvar e carregar conjuntos de tasks.
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Profile:
    """Representa um profile (workspace) de tasks."""

    name: str
    description: str
    tasks: List[dict]  # Tasks serializadas
    created_at: str
    updated_at: str

    @property
    def task_count(self) -> int:
        """Número de tasks no profile."""
        return len(self.tasks)

    @property
    def window_names(self) -> List[str]:
        """Lista de nomes de janelas/processos únicos."""
        windows = set()
        for task in self.tasks:
            if task.get("window_method") == "process":
                windows.add(task.get("process_name", ""))
            else:
                title = task.get("window_title", "")
                # Pega apenas a primeira parte do título para display
                if title:
                    windows.add(title.split(" - ")[0][:20])
        return sorted(list(windows))

    def to_dict(self) -> dict:
        """Serializa para dicionário."""
        return {
            "name": self.name,
            "description": self.description,
            "tasks": self.tasks,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: dict) -> 'Profile':
        """Cria a partir de dicionário."""
        return Profile(
            name=data.get("name", "Sem nome"),
            description=data.get("description", ""),
            tasks=data.get("tasks", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )


class ProfileManager:
    """
    Gerencia profiles de tasks.

    Cada profile é salvo como um arquivo JSON separado no diretório de profiles.
    """

    def __init__(self, profiles_dir: Path):
        """
        Inicializa o gerenciador.

        Args:
            profiles_dir: Diretório onde os profiles serão salvos
        """
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> List[Profile]:
        """
        Lista todos os profiles disponíveis.

        Returns:
            Lista de objetos Profile ordenados por nome
        """
        profiles = []

        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profiles.append(Profile.from_dict(data))
            except Exception as e:
                print(f"Erro ao ler profile {file_path}: {e}")

        return sorted(profiles, key=lambda p: p.name.lower())

    def get_profile(self, name: str) -> Optional[Profile]:
        """
        Obtém um profile pelo nome.

        Args:
            name: Nome do profile

        Returns:
            Profile ou None se não encontrado
        """
        file_path = self._get_file_path(name)
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Profile.from_dict(data)
        except Exception as e:
            print(f"Erro ao ler profile {name}: {e}")
            return None

    def save_profile(self, name: str, tasks: List[dict], description: str = "") -> Profile:
        """
        Salva tasks como um novo profile ou atualiza existente.

        Args:
            name: Nome do profile
            tasks: Lista de tasks serializadas (dicts)
            description: Descrição opcional

        Returns:
            Profile criado/atualizado
        """
        now = datetime.now().isoformat()

        # Verifica se já existe
        existing = self.get_profile(name)
        if existing:
            profile = Profile(
                name=name,
                description=description or existing.description,
                tasks=tasks,
                created_at=existing.created_at,
                updated_at=now
            )
        else:
            profile = Profile(
                name=name,
                description=description,
                tasks=tasks,
                created_at=now,
                updated_at=now
            )

        # Salva arquivo
        file_path = self._get_file_path(name)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

        return profile

    def load_profile(self, name: str) -> List[dict]:
        """
        Carrega tasks de um profile.

        Args:
            name: Nome do profile

        Returns:
            Lista de tasks serializadas (dicts)

        Raises:
            FileNotFoundError: Se profile não existe
        """
        profile = self.get_profile(name)
        if not profile:
            raise FileNotFoundError(f"Profile '{name}' não encontrado")

        return profile.tasks

    def delete_profile(self, name: str) -> bool:
        """
        Remove um profile.

        Args:
            name: Nome do profile

        Returns:
            True se removido, False se não existia
        """
        file_path = self._get_file_path(name)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def rename_profile(self, old_name: str, new_name: str) -> Optional[Profile]:
        """
        Renomeia um profile.

        Args:
            old_name: Nome atual
            new_name: Novo nome

        Returns:
            Profile renomeado ou None se erro
        """
        profile = self.get_profile(old_name)
        if not profile:
            return None

        # Cria novo profile com novo nome
        new_profile = self.save_profile(
            new_name,
            profile.tasks,
            profile.description
        )
        new_profile = Profile(
            name=new_name,
            description=profile.description,
            tasks=profile.tasks,
            created_at=profile.created_at,
            updated_at=datetime.now().isoformat()
        )

        # Salva e remove antigo
        file_path = self._get_file_path(new_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_profile.to_dict(), f, indent=2, ensure_ascii=False)

        self.delete_profile(old_name)
        return new_profile

    def export_profile(self, name: str, export_path: Path) -> bool:
        """
        Exporta um profile para arquivo externo.

        Args:
            name: Nome do profile
            export_path: Caminho de destino

        Returns:
            True se exportado com sucesso
        """
        profile = self.get_profile(name)
        if not profile:
            return False

        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao exportar profile: {e}")
            return False

    def import_profile(self, import_path: Path, new_name: Optional[str] = None) -> Optional[Profile]:
        """
        Importa um profile de arquivo externo.

        Args:
            import_path: Caminho do arquivo a importar
            new_name: Nome opcional (usa nome do arquivo se não fornecido)

        Returns:
            Profile importado ou None se erro
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profile = Profile.from_dict(data)

            # Usa novo nome se fornecido
            if new_name:
                profile.name = new_name

            # Salva no diretório de profiles
            return self.save_profile(
                profile.name,
                profile.tasks,
                profile.description
            )

        except Exception as e:
            print(f"Erro ao importar profile: {e}")
            return None

    def duplicate_profile(self, name: str, new_name: str) -> Optional[Profile]:
        """
        Duplica um profile existente.

        Args:
            name: Nome do profile original
            new_name: Nome da cópia

        Returns:
            Novo profile ou None se erro
        """
        profile = self.get_profile(name)
        if not profile:
            return None

        return self.save_profile(
            new_name,
            profile.tasks.copy(),
            f"Cópia de {profile.name}"
        )

    def _get_file_path(self, name: str) -> Path:
        """Retorna caminho do arquivo para um profile."""
        # Sanitiza nome para uso como arquivo
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        safe_name = safe_name.replace(" ", "_")
        return self.profiles_dir / f"{safe_name}.json"

    def profile_exists(self, name: str) -> bool:
        """Verifica se um profile existe."""
        return self._get_file_path(name).exists()
