# toolbox
[![CI Actions Status](https://github.com/perftool-incubator/toolbox/workflows/crucible-ci/badge.svg)](https://github.com/perftool-incubator/toolbox/actions)

The toolbox project contains shared code libraries and utilities used across the [crucible](https://github.com/perftool-incubator/crucible) family of [subprojects](https://github.com/perftool-incubator). Nearly every benchmark, tool, and core component depends on toolbox.

## Usage

Consumer projects access toolbox via the `TOOLBOX_HOME` environment variable:

```bash
# Bash
source "${TOOLBOX_HOME}/bash/library/bench-base"

# Perl
use lib "$ENV{'TOOLBOX_HOME'}/perl";
use toolbox::json;

# Python
sys.path.append(os.path.join(os.environ['TOOLBOX_HOME'], 'python'))
from toolbox.json import load_json_file
```

## Libraries

### [bash/](bash/)
- `library/bench-base` — Shared benchmark shell functions: error handling (`exit_error`), diagnostic dumps (`dump_runtime`), software prerequisite validation, CPU scheduler balance control (cgroup v1 and v2), clocksource validation

### [perl/](perl/)
Perl modules under the `toolbox::` namespace:
- `json.pm` — JSON file I/O with automatic XZ compression, schema validation via JSON::Validator
- `logging.pm` — Debug/info/error logging with caller tracking and robust output retry logic
- `metrics.pm` — Time-series metric recording with sample consolidation, writes XZ-compressed CSV
- `cpu.pm` — CPU topology extraction from sysfs (packages, cores, dies, threads)
- `jsonsettings.pm` — Dot-notation queries into nested JSON structures
- `run.pm` — Shell command execution with stdout capture

### [python/](python/)
Python modules under the `toolbox` package:
- `json.py` — JSON file loading with optional LZMA decompression, schema validation
- `jsonsettings.py` — Dot-notation JSON queries (parallel to Perl version)
- `metrics.py` — Time-series metric recording with sample consolidation (parallel to Perl version)
- `system_cpu_topology.py` — CPU topology discovery from sysfs with NUMA, SMT, and die awareness

## Utilities

Scripts in [bin/](bin/) provide command-line access to library functions:
- `cpumask.py` — Convert between CPU list, bitmask, and hexmask formats
- `get-cpu-range.py` — Convert comma-separated CPU list to range notation
- `get-cpus-ordered.py` — Order CPUs by topology (NUMA, SMT handling)
- `get-json-settings.py`, `get-json-settings.pl` — Extract values from JSON files using dot-notation queries
- `json-validator.py` — Validate JSON files against schemas
- `timestamper.py` — Prefix stdin lines with UTC timestamps

## Container Image

`workshop.json` declares Perl CPAN dependencies that are installed into the crucible controller container image at build time.
