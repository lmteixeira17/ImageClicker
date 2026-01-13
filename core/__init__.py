"""
ImageClicker Core Module
Lógica de negócio para automação de cliques baseada em imagem.
"""

from .window_utils import (
    get_windows,
    get_window_dpi_scale,
    find_window_by_title,
    find_window_by_process,
    get_windows_by_process,
    get_available_processes,
    is_window_minimized,
)

from .image_matcher import (
    find_and_click,
    check_template_visible,
    MATCH_THRESHOLD,
)

from .task_manager import Task, TaskManager

from .stats_tracker import StatsTracker, TaskStats

from .profile_manager import ProfileManager, Profile

__all__ = [
    # Window utils
    'get_windows',
    'get_window_dpi_scale',
    'find_window_by_title',
    'find_window_by_process',
    'get_windows_by_process',
    'get_available_processes',
    'is_window_minimized',
    # Image matcher
    'find_and_click',
    'check_template_visible',
    'MATCH_THRESHOLD',
    # Task manager
    'Task',
    'TaskManager',
    # Stats
    'StatsTracker',
    'TaskStats',
    # Profiles
    'ProfileManager',
    'Profile',
]
