# ImageClicker - AI Agent Instructions

## Architecture Overview

**Multi-window automation tool**: CLI ([iclick.py](iclick.py)) and GUI ([gui.py](gui.py)) support parallel task execution across multiple windows using different image recognition engines.

### Core Pattern: Task-Based Multi-Window Automation
1. **Tasks**: Each task binds a window pattern + template image + action type
2. **Parallel Execution**: Multiple tasks run simultaneously via `ThreadPoolExecutor`
3. **Window Targeting**: Tasks find windows by title pattern (wildcards supported)
4. **Persistence**: Tasks saved to `tasks.json` for reuse

### Critical Divergence: Two Recognition Engines

**CLI (pyautogui-based)** - Full screen mode:
- Uses `pyautogui.locateOnScreen()` with 0.9 confidence
- Searches entire screen space (slower but simpler)
- Best for single-window quick clicks

**GUI & CLI Window Mode (OpenCV-based)**:
- Uses `cv2.matchTemplate()` with TM_CCOEFF_NORMED and 0.85 threshold
- Targets specific HWND (window handle) - faster and more reliable
- Converts to grayscale for better performance
- See `find_and_click_window()` in [iclick.py](iclick.py#L52-L97) and `find_and_click()` in [gui.py](gui.py#L91-L144)

## Task System Architecture

### Task Data Structure ([gui.py](gui.py#L24-L52))
```python
@dataclass
class Task:
    id: int
    window_title: str      # Pattern like "Chrome*" or "*YouTube*"
    hwnd: Optional[int]    # Resolved at runtime
    image_name: str        # Template name (without .png)
    action: str            # click, double_click, right_click
    repeat: bool           # Loop continuously
    interval: float        # Seconds between repeats
    enabled: bool          # Can be toggled without removing
```

### Persistence Format (`tasks.json`)
```json
[
  {
    "id": 1,
    "window_title": "Chrome - *",
    "image_name": "accept_button",
    "action": "click",
    "repeat": true,
    "interval": 5.0,
    "enabled": true
  }
]
```

### Window Pattern Matching ([gui.py](gui.py#L68-L83))
- `"Chrome*"` → starts with "Chrome"
- `"*YouTube*"` → contains "YouTube"
- `"*- Notepad"` → ends with "- Notepad"
- `"Exact Title"` → exact match (case-insensitive)

## TaskManager Class ([gui.py](gui.py#L148-L232))

Central orchestrator for parallel execution:

```python
task_manager = TaskManager(on_status_update=callback, on_log=log_callback)
task_manager.add_task(window_title="App*", image_name="btn", action="click", repeat=True, interval=5)
task_manager.start()   # Spawns threads for each enabled task
task_manager.stop()    # Signals all threads to stop
```

**Threading Model:**
- Each task runs in its own thread via `ThreadPoolExecutor`
- `threading.Event` used for graceful shutdown signaling
- Status updates marshaled to main thread via callbacks
- Thread-safe task dictionary with `threading.Lock`

## Script System (Legacy Sequential)

JSON scripts in `scripts/` directory for sequential automation:

```json
{
  "actions": [
    {"type": "click", "image": "template_name", "wait": true, "required": true},
    {"type": "type", "text": "...", "interval": 0.05},
    {"type": "press", "key": "enter"},
    {"type": "hotkey", "keys": ["ctrl", "s"]},
    {"type": "wait", "seconds": 2},
    {"type": "wait_for", "image": "template_name", "timeout": 30}
  ]
}
```

**Note**: Scripts use pyautogui (full screen). For window-specific automation, use the Task system instead.

## Hardcoded Paths Pattern

**Critical**: Both files use absolute paths that must be updated together:
- [iclick.py](iclick.py#L36-L40): `BASE_DIR`, `IMAGES_DIR`, `SCRIPTS_DIR`, `TASKS_FILE`
- [gui.py](gui.py#L18-L20): `BASE_DIR`, `IMAGES_DIR`, `TASKS_FILE`

## GUI Tabs Structure

The GUI uses a `CTkTabview` with two tabs:

### 📋 Tasks Tab
- Add new tasks (window selection, image template, action type)
- Task list with enable/disable toggles
- Start/Stop all tasks buttons

### 🖼️ Images Tab (Gallery Manager)
Template image management with:
- **Thumbnail grid**: Visual 3-column grid of all captured templates
- **Preview panel**: Larger preview of selected image with dimensions
- **Actions**:
  - `🔍 Testar na Tela`: Uses pyautogui to locate template on screen (moves mouse to show location)
  - `✏️ Renomear`: Rename template file
  - `🗑️ Deletar`: Delete template (no confirmation dialog)
  - `📂 Abrir Pasta`: Opens images folder in Explorer

**Key methods** ([gui.py](gui.py)):
- `_build_images_tab()`: Creates gallery UI
- `_refresh_image_gallery()`: Rebuilds thumbnail grid
- `_create_thumbnail()`: Creates clickable thumbnail with hover effects
- `_select_gallery_image()`: Updates preview panel

## Development Commands

```bash
# CLI - Single operations
python iclick.py capture button_name              # Capture template
python iclick.py click button_name                # Click (full screen search)
python iclick.py click button_name --window "App*" # Click in specific window

# CLI - Multi-window parallel
python iclick.py tasks                            # Run all tasks from tasks.json
python iclick.py list                             # Show images, scripts, and tasks

# GUI
python gui.py                                     # Launch multi-task GUI
```

## Safety Mechanisms

From [iclick.py](iclick.py#L47-L48):
```python
pyautogui.PAUSE = 0.5      # Mandatory 0.5s pause between ALL actions
pyautogui.FAILSAFE = True  # Move mouse to (0,0) to emergency abort
```

**Stopping parallel tasks:**
- GUI: Click "Parar" button
- CLI: Press `Ctrl+C`

## Key Dependencies

- **pyautogui**: CLI automation engine + keyboard simulation
- **opencv-python (cv2)**: Window-specific image matching
- **pywin32 (win32gui/win32api)**: Windows-specific window enumeration and mouse control
- **customtkinter**: Modern dark-themed GUI framework
- **Pillow (PIL)**: Image capture and manipulation
- **concurrent.futures**: ThreadPoolExecutor for parallel tasks

**Windows-only**: `pywin32` makes this Windows-exclusive.

## Common Pitfalls

1. **Templates become stale**: Screen resolution, theme changes, or DPI scaling breaks matches
2. **Window not found**: Title changed or window closed - tasks will retry automatically if repeat=True
3. **Multiple matches**: First match is used - make templates more specific
4. **Thread safety**: Don't modify `task_manager.tasks` dict while tasks are running
5. **Runaway loops**: Tasks with repeat=True run forever until stopped

## When Adding Features

- **New action types**: Add to `run_script()` and document in scripts
- **Task properties**: Update `Task` dataclass, `to_dict()`, `from_dict()`, and GUI widgets
- **New window matching**: Modify `find_window_by_title()` in both files
- **GUI modifications**: Use `customtkinter` widgets for consistent theming
- **Thread operations**: Use locks and events for thread safety
