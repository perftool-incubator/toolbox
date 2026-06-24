# Toolbox - Shared Libraries

## Purpose
Toolbox provides shared libraries (Bash, Python) used across the entire crucible ecosystem. Nearly every benchmark, tool, and core component depends on it via the `TOOLBOX_HOME` environment variable.

## Structure
| Path | Language | Key Modules |
|------|----------|-------------|
| `bash/library/` | Bash | `bench-base` — shared benchmark shell functions |
| `python/toolbox/` | Python | `json.py`, `jsonsettings.py`, `messages.py`, `roadblock.py`, `metrics.py` (deprecated, use `cdm_metrics.py`), `cdm_metrics.py`, `logging.py`, `system_cpu_topology.py` |
| `bin/` | Python | CLI utilities (see below) |

## Utilities (`bin/`)
- `cpumask.py` — CPU mask manipulation
- `get-cpu-range.py`, `get-cpus-ordered.py` — CPU topology helpers
- `json-validator.py` — JSON schema validation
- `get-json-settings.py` — JSON settings extraction
- `timestamper.py` — Timestamp formatting

## Conventions
- Primary branch is `main`
- Other repos access toolbox via `$TOOLBOX_HOME` env var (e.g., `sys.path.append(Path(TOOLBOX_HOME) / "python")`)
- Changes here affect all downstream consumers — test broadly
- `workshop.json` declares build-time requirements for the controller image
- Python modules use `toolbox.` package
