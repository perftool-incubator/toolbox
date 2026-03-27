# Toolbox - Shared Libraries

## Purpose
Toolbox provides shared libraries (Bash, Perl, Python) used across the entire crucible ecosystem. Nearly every benchmark, tool, and core component depends on it via the `TOOLBOX_HOME` environment variable.

## Structure
| Path | Language | Key Modules |
|------|----------|-------------|
| `bash/library/` | Bash | `bench-base` — shared benchmark shell functions |
| `perl/toolbox/` | Perl | `json.pm` (JSON I/O, auto-XZ on write, transparent decompress on read), `logging.pm`, `metrics.pm`, `cpu.pm` (topology), `jsonsettings.pm` (dot-notation queries), `run.pm` (shell command execution) |
| `python/toolbox/` | Python | `json.py`, `jsonsettings.py`, `metrics.py`, `system_cpu_topology.py` |
| `bin/` | Mixed | CLI utilities (see below) |

## Utilities (`bin/`)
- `cpumask.py` — CPU mask manipulation
- `get-cpu-range.py`, `get-cpus-ordered.py` — CPU topology helpers
- `json-validator.py` — JSON schema validation
- `get-json-settings.pl`, `get-json-settings.py` — JSON settings extraction
- `timestamper.py` — Timestamp formatting

## Conventions
- Primary branch is `main`
- Other repos access toolbox via `$TOOLBOX_HOME` env var (e.g., `use lib "$ENV{'TOOLBOX_HOME'}/perl"`)
- Changes here affect all downstream consumers — test broadly
- `workshop.json` declares build-time requirements for the controller image
- Perl modules use `toolbox::` namespace; Python modules use `toolbox.` package
