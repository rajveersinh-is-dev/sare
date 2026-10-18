# Examples

Minimal working example: run SARE on a small graph.

## Files

- `demo.graph` — a small undirected edge list (1-based).
- `run_demo.ps1` (PowerShell) / `run_demo.sh` (POSIX) — run SARE + baselines and compare.

## Quick start

PowerShell:
```powershell
# build the Rust CLI (once)
cd ..\src\rs
cargo build --release

# run SARE and min-degree on the demo graph
..\..\target\release\sare.exe ..\examples\demo.graph sare 1.0 0.0
..\..\target\release\sare.exe ..\examples\demo.graph min-degree
```

Python reference (no build needed):
```sh
python ../src/python/sare_reference.py demo.graph sare
```

Expected: both return a valid ordering; on this small demo graph fill is 0.
