# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

学生成绩统计工具 — a student grade statistics tool for non-technical users (teachers).
Takes student names + scores, outputs max/min/average/median/std-dev/pass-rate/distribution/ranked list.
All UI is Chinese-language.

## Two entry points

| File | Role |
|------|------|
| `grade_stats.py` | Core engine + CLI (pure stdlib, zero deps) |
| `app.py` | Native GUI desktop app (customtkinter, with tkinter fallback) |

**Core logic must never be duplicated between these files.** `app.py` imports from `grade_stats.py` — if a statistic or import format changes, it belongs in `grade_stats.py`.

## Commands

```bash
# Run tests (all 32)
python -m pytest test_grade_stats.py -v

# Run CLI
python grade_stats.py --demo
python grade_stats.py --file data.csv

# Run GUI (dev)
python app.py

# Build distributable exe (Windows, no console)
build_exe.bat
# or manually:
python -m PyInstaller --onefile --noconsole --name "成绩统计工具" \
  --hidden-import customtkinter --hidden-import darkdetect \
  --hidden-import grade_stats --clean app.py
```

## Architecture

```
grade_stats.py          app.py
┌─────────────────┐    ┌──────────────────────┐
│ Student          │◄───│ imports grade_stats  │
│ StatsResult      │    │                      │
│ analyze()        │    │ SplashScreen (tk)    │
│ read_csv/json()  │    │ GradeStatsApp (ctk)  │
│ CLI (argparse)   │    │ PanedWindow layout   │
└─────────────────┘    └──────────────────────┘
```

### `grade_stats.py` internal sections
1. **数据模型** — `Student`, `StatsResult` dataclasses
2. **统计引擎** — `analyze(students, pass_line)` returns `StatsResult`
3. **单指标便捷函数** — `get_max_score()`, `get_min_score()`, `get_average_score()`
4. **格式化输出** — `print_report()` for CLI
5. **数据输入** — `collect_interactive()`, `read_csv()`, `read_json()`
6. **CLI** — argparse entry, `DEMO_STUDENTS` constant (8 records)

### `app.py` internal sections
- `SplashScreen` — tkinter Canvas-based animated loading window (progress bar + rotating tips)
- `GradeStatsApp` — main window with `tk.PanedWindow` split: left panel (input + student table) / right panel (stat cards + distribution bars + ranked list)
- Widget factory methods (`_frame`, `_btn`, `_entry`, `_slider`, `_card`) abstract ctk vs tk fallback
- Grid weights on stat cards for responsive layout; `_on_resize` with debouncing for font scaling

## Dependencies

- **Core (`grade_stats.py`):** Python stdlib only (`statistics`, `csv`, `json`, `argparse`, `dataclasses`)
- **GUI (`app.py`):** `customtkinter` + `darkdetect`; automatically falls back to bare `tkinter` if not installed
- **Build:** `pyinstaller`

## Encoding note

Windows GBK console cannot render emoji. Both files override stdout at entry:
```python
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```
The `--noconsole` PyInstaller build sidesteps this entirely.

## Test structure

`test_grade_stats.py` — 32 tests in 3 classes:
- `TestStatistics` — core math (average, max/min/ties, median, std-dev, pass-rate, distribution, empty)
- `TestFileInput` — CSV/JSON parsing (normal, no-header, invalid rows, out-of-range, BOM, malformed)
- `TestLegacyAPI` — standalone convenience functions still work

Tests use `tempfile.mkdtemp()` for file-based tests, no fixtures on disk.
