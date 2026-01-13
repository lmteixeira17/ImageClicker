# ImageClicker – AI Agent Instructions (PyQt6)

Concise guidance for coding agents to be productive in this repo.

## Big Picture
- **Two frontends**: CLI [iclick.py](iclick.py) and PyQt6 GUI [app_qt.py](app_qt.py) + [ui_qt](ui_qt/).
- **Core services**: Task orchestration in [core/task_manager.py](core/task_manager.py); image matching + “ghost clicks” in [core/image_matcher.py](core/image_matcher.py); window discovery (title/process) in [core/window_utils.py](core/window_utils.py); profiles in [core/profile_manager.py](core/profile_manager.py).
- **Why this structure**: GUI stays responsive while tasks run in threads; window-specific matching is faster/reliable; CLI keeps legacy full-screen flows and scripting.

## Recognition Engines
- **CLI fullscreen**: `pyautogui.locateOnScreen()` with confidence 0.9 for quick, global matches.
- **Window-specific (GUI/CLI)**: OpenCV `TM_CCOEFF_NORMED` with threshold 0.85; DPI-aware scaling; “ghost click” via `PostMessage` without moving cursor.
- See `find_and_click()` in [core/image_matcher.py](core/image_matcher.py) and `find_and_click_window()` in [iclick.py](iclick.py).

## Tasks: Parallel Execution
- Dataclass `Task` in [core/task_manager.py](core/task_manager.py) includes: `window_method` (`title`/`process`), `process_name`, `title_filter`, `window_index`, `threshold`, `repeat/interval`, `action`, and `task_type` (`simple` or `prompt_handler` with `options`).
- Persistence: [tasks.json](tasks.json) stores array of serialized tasks; `TaskManager.save_tasks()/load_tasks()` handle I/O.
- Concurrency: one thread per enabled task via `ThreadPoolExecutor`; stop via `threading.Event`; callbacks `on_log`/`on_status_update`/`on_execution` marshal updates.

## Window Targeting
- Title patterns with wildcards in [core/window_utils.py](core/window_utils.py): `Chrome*`, `*YouTube*`, `*- Notepad`, exact/contains.
- Process-based selection: pick windows by executable (e.g. `Code.exe`) with optional `title_filter` and `window_index`.

## GUI Structure (PyQt6)
- Entry: [app_qt.py](app_qt.py) calls `ui_qt/main_window.run()`.
- Pages: Dashboard, Tasks, Templates, Prompts, Settings in [ui_qt/pages](ui_qt/pages/); Sidebar and panels in [ui_qt/components](ui_qt/components/).
- Capture overlay: [ui_qt/components/capture_overlay.py](ui_qt/components/capture_overlay.py) covers all monitors, suggests template names via EasyOCR, saves PNGs to [images/](images/).
- The GUI wires `TaskManager` and uses signals for thread-safe logs.

## Developer Workflows
- CLI examples:
  - `python iclick.py capture btn_save`
  - `python iclick.py click btn_save` or `python iclick.py click btn_save --window "Chrome*"`
  - `python iclick.py run login_sequence`
  - `python iclick.py tasks` (parallel from tasks.json)
- GUI entry: `python app_qt.py` (or use `ImageClicker.bat`).
- Hardcoded paths: only CLI has absolute paths in [iclick.py](iclick.py) (`BASE_DIR`, `IMAGES_DIR`, `SCRIPTS_DIR`, `TASKS_FILE`). Update if moving the project.

## Project Conventions
- Templates: PNGs in [images/](images/) named by element/process; overlay suggests names including DPI (e.g., `Save_Chrome_125DPI.png`).
- Thresholds: default 0.85 for OpenCV; configurable per task (`Task.threshold`).
- Ghost clicks: prefer window messages over cursor moves to avoid focus stealing.
- Keep tasks small and specific; use scripts for multi-step flows.

## Integration Points
- Tasks → Window selection via `find_all_windows_*` → `image_matcher` executes match + click → status/log callbacks update UI.
- Prompt handlers: detect any option visible, then click `selected_option`.
- Profiles: [core/profile_manager.py](core/profile_manager.py) saves/loads sets of tasks to [data/profiles](data/profiles/).

## Safety & Pitfalls
- CLI safety: `pyautogui.PAUSE=0.5`, `FAILSAFE=True` (move to top-left to abort).
- DPI/Theme changes can stale templates; recapture with overlay or lower threshold cautiously.
- Multi-monitor: overlay and window screenshots consider virtual screen; coordinates can be negative.
- Thread safety: don’t mutate `TaskManager.tasks` while running; use provided methods.

## Where To Look
- Core logic: [core/task_manager.py](core/task_manager.py), [core/image_matcher.py](core/image_matcher.py), [core/window_utils.py](core/window_utils.py).
- GUI wiring: [ui_qt/main_window.py](ui_qt/main_window.py), [ui_qt/pages/tasks.py](ui_qt/pages/tasks.py).
- CLI flows: [iclick.py](iclick.py).

If any section is unclear or missing (e.g., specific page behaviors), tell me what to expand and I’ll refine these instructions.
