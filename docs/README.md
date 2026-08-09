# Ammeter Testing Framework

A configuration-driven test framework for current-measurement devices, built on pytest.
It samples three ammeter emulators (Greenlee, ENTES, CIRCUTOR), computes statistics over the
readings, and archives every run as CSV, JSON and plots under a unique run folder.

This document is the project deliverable
---

## 1. Requirements

- **Python 3.9+** — the code uses the walrus operator (3.8+) and PEP 585 builtin generics in
  runtime-evaluated annotations (3.9+). Developed and verified on **3.14.6**.
- No services, databases or hardware. The emulators are plain TCP servers on `localhost`.
- Ports **5000–5002** must be free.

## 2. Setup

`setup_env.py` creates a virtual environment and installs the dependencies:

```sh
python setup_env.py
```

Then activate it:

```sh
.\.venv\Scripts\Activate.ps1     # PowerShell
.venv\Scripts\activate.bat       # Windows cmd
source .venv/bin/activate        # Linux / macOS
```

## 3. Quick start

Start all three emulators and take one reading from each:

```sh
python main.py
```

Run the test suite:

```sh
pytest -s
```


## 4. Project structure

```
Ammeters/
  base_ammeter.py        Abstract base: TCP server loop + measurement contract
  Greenlee_Ammeter.py    Ohm's law emulator          (port 5000)
  Entes_Ammeter.py       Hall effect emulator        (port 5001)
  Circutor_Ammeter.py    Rogowski coil emulator      (port 5002)
  client.py              TCP client for reading a measurement
config/
  config.yaml            Sampling, ammeter, analysis and result settings
docs/                    Deliverable's Folder
  README.md              This document
src/
  tests/
    conftest.py          Fixtures, CLI options, result/log folder wiring
    test_ammeter.py      The test suite
  utils/
    result_manager.py    Sampler, SamplerResult, NumericSamplerResult, ResultManager
    utils.py             AmmeterManager, port helpers, generate_random_float
    config.py            YAML loader
    logger.py            Shared timestamp format
Exam/                    The original exercise specification
main.py                  Starts the emulators and takes one reading from each
pytest.ini               Log format, testpaths, marker registry
setup_env.py             Creates .venv and installs requirements
```


## 5. Configuration reference

All settings live in [config/config.yaml](../config/config.yaml).

| Key | Default | Effect |
|---|---|---|
| `testing.sampling.measurements_count` | `0` | Number of samples to take. Values < 1 disable this mode. **Takes priority over duration when both are set.** |
| `testing.sampling.total_duration_seconds` | `1` | How long to sample for. Values < 1 disable this mode. Used only when `measurements_count` is disabled. |
| `testing.sampling.sampling_frequency_hz` | `1` | Target sample rate. The sampler sleeps for the remainder of the period after each reading, so a slow device degrades the rate rather than accumulating drift. |
| `ammeters.<name>.port` | 5000–5002 | TCP port for the emulator |
| `analysis.visualization.enabled` | `false` | When true, every figure is shown interactively and **blocks the run until closed** |
| `analysis.visualization.plot_types` | `[line, scatter, hist]` | Currently unused; tests request kinds explicitly |
| `analysis.visualization.default_figure.figure_size` | `[8, 5]` | Figure size in inches, mapped to matplotlib's `figsize` |
| `analysis.visualization.default_figure.default_plot_type` | `line` | Plot kind used when a caller does not pass one |
| `result_management.folder_name` | `results` | Root folder for all run output |

Tests override the sampling values per-case through the `make_sampler` fixture; the YAML values
are the defaults for anything not overridden.

## 6. Running the tests

```sh
pytest                      # run everything
pytest -s                   # ... and stream logs to the console
```

Select by marker:

```sh
pytest -s -m greenlee       # only Greenlee tests
pytest -s -m stability      # the whole stability suite
pytest -s -m "not entes"    # everything except ENTES
```

Registered markers: `stability`, `greenlee`, `entes`, `circutor`.

Select by name or location:

```sh
# substring match on the test name
pytest -s -k "same_time"

# everything except substring match on the test name
pytest -s -k "not same_time"

# one file
pytest -s src/tests/test_ammeter.py

# one test all parameters
pytest -s src/tests/test_ammeter.py::test_greenlee_stability

# one case
pytest -s src/tests/test_ammeter.py::test_greenlee_stability[GreenleeAmmeter-10]
```

Framework options:

| Option | Type | Effect |
|---|---|---|
| `--result-subfolder NAME`, `--rsf NAME` | value | Write this run into `results/NAME/` instead of a timestamped folder. Useful for naming a run you intend to keep. |
| `--compact-result`, `--cr` | flag | After the session, archive the run folder to `results/NAME.zip`. Takes no argument. |

```sh
pytest -s --rsf MyRun --cr
```

## 7. Test inventory

32 cases, all marked `stability`.

| Test | Cases | What it does |
|---|---|---|
| `test_circutor_stability` | 2 | Samples CIRCUTOR for 10 s and 30 s; asserts `std <= STD_CUTOFF` |
| `test_entes_stability` | 2 | Same for ENTES |
| `test_greenlee_stability` | 2 | Same for Greenlee |
| `test_ammeter_stability` | 12 | All three devices × frequency {1, 30} Hz × duration {10, 30} s; saves results, plots all three kinds, asserts `std <= STD_CUTOFF` |
| `test_ammeter_stability_by_measurements_count` | 6 | All three devices × frequency {1, 20} Hz, fixed 100 measurements; exercises the count-based sampling mode and plots |
| `test_ammeters_at_same_time_stability` | 8 | Every 2- and 3-device combination × duration {10, 30} s, sampled **concurrently** via a thread pool; writes a combined `summary.json` and overlay plots |

A full run takes roughly **14 minutes**, almost entirely spent in the sampling sleeps.

## 8. Output layout

Every run gets its own folder — a UTC-style timestamp by default, or the `--rsf` name — and every
test gets a subfolder named after its full test id:

```
results/
└── 20260809_115517/
    ├── pytest.log
    ├── test_greenlee_stability_GreenleeAmmeter-10/
    │   ├── ammeter_result.csv          per-sample readings
    │   └── ammeter_result.json         statistics summary
    ├── test_ammeter_stability_GreenleeAmmeter-1-10/
    │   ├── ammeter_result.csv
    │   ├── ammeter_result.json
    │   ├── greenlee_line.png
    │   ├── greenlee_scatter.png
    │   └── greenlee_hist.png
    └── test_ammeters_at_same_time_stability_circutor-entes-10/
        ├── circutorResult.csv
        ├── circutorResult.json
        ├── entesResult.csv
        ├── entesResult.json
        ├── summary.json                both devices in one file
        ├── circutor_vs_entes_line.png
        ├── circutor_vs_entes_scatter.png
        └── circutor_vs_entes_hist.png
```

**CSV** — one row per sample:

| Index[#] | Time[s] | *(device name)* |
|---|---|---|
| 1 | 0.000089 | 0.073157 |
| 2 | 1.001312 | 0.015897 |

`Time[s]` is seconds since the first sample, from `time.perf_counter()`.

**JSON summary** — the same content as the logged text summary, in machine-readable form:

```json
{
  "sample_name": "entes",
  "sample_count": 10,
  "sample_types": ["<class 'float'>"],
  "max": 148.17597131549826,
  "min": 18.43144537876175,
  "mean": 64.79760928384465,
  "median": 53.16101539594701,
  "std_ddof0": 35.39819019225346
}
```

Text and JSON summaries are generated from one shared structure, so they can never disagree.

## 9. Dependencies

The spec asks for minimal external dependencies; these are the ones installed and why.

| Package | Why |
|---|---|
| `pytest` | Test runner — provides the fixture, parametrization and marker machinery the framework is built on |
| `pyyaml` | Reading `config.yaml` |
| `numpy` | Standard deviation with a `ddof` parameter |
| `pandas` | The `DataFrame` that backs both CSV export and plotting |
| `matplotlib` | Figure rendering and file output |
| `seaborn` | Concise overlay plotting of several results on one axis |
| `scipy` | **Declared but not currently imported** — intended for the statistical testing in the accuracy suite. Should be used or dropped. |
