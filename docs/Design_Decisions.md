# Design Decisions
This document will briefly go over the design decisions

## 1. Usage of pytest library
As this project is supposed to simulate a testing environment, the decision to use pytest was basic as it lets us focus on the testing without the need to reinvent the wheel from zero.

Pytest is a robust framework that lets us log and save wanted results, with an easy way to add functions to run before / after / around tests as needed. In addition, with a minimal addition we can add a connection to a database to save to.

In general in Python we can and should use common libraries to help new developers join the project faster without the need to go over the full stack to make small changes.

## 2. Configuration driven testing
All the settings that a tester may want to change without touching code live in [`config/config.yaml`](../config/config.yaml) — the sampling defaults, the ammeter ports and commands, the plot defaults and the result folder name. It is loaded once in [`conftest.py:40`](../src/tests/conftest.py#L40) and handed to the fixtures, so a test never reads the file itself.

The sampling values are only defaults. The [`make_sampler`](../src/tests/conftest.py#L132) factory fixture lets each test override just the values it cares about, so the yaml stays the "normal" run and the parametrization stays in the test.

I kept the ammeter ports and commands in the yaml as well so the documentation, the emulator and the client can not drift apart — this was one of the bugs in the supplied code (see section 12).

## 3. Sampling and timing precision
The spec asks for precise timing, so [`Sampler.sample`](../src/utils/result_manager.py#L190) does not sleep a fixed period between samples. It measures how long the device call took and sleeps only the remainder of the period. This way a slow device eats into its own slot instead of pushing every following sample later and later.

`Sampler` supports two modes — a fixed number of measurements or a total duration — and `measurements_count` wins when both are set. Both are on the same dataclass so a test only has to pass what it wants.

Every sample is stored with the time it was taken relative to the start of the run ([`add_sample`](../src/utils/result_manager.py#L50)), so the real sampling rate can always be checked after the fact instead of being assumed.

## 4. Sampling several ammeters at the same time
For comparing devices it is not enough to sample them one after the other, they have to be sampled over the same time window. [`Sampler.sample_many`](../src/utils/result_manager.py#L215) runs one sampling loop per device in a thread pool and returns the results keyed by name.

Threads and not processes because the work is IO bound.

This is what [`test_ammeters_at_same_time_stability`](../src/tests/test_ammeter.py#L108) is built on.

## 5. Result and sampling architecture
A combined result object makes it easier to plan for the future and is the bread and butter of OOP code.

This is why I split the results into 3 main classes
### 5.1. ResultManager
Used for saving and general manipulation of results (plots). See [`result_manager.py:243`](../src/utils/result_manager.py#L243).
If I had more robust plots I would have split the plotting into another class, but as the plots are and should be more specific per test, it isn't usually needed.

### 5.2. Sampler
Used for sampling in a loop with a function. Can be used as a parent for specializations.
I used it for sampling to ensure a common sampling function between tests.

### 5.3. SamplerResult
A general result class. The more specialized NumericSamplerResult can be used for multiple numeric results, but if I was testing a string answer from a server, or a boolean sample of whether I am connected to a server, I could use a child of SamplerResult for common functionality.

### 5.4. Future development
If I had more tests to create / plot I would move the plotting to the result class and add common result plots like hist / scatter / cumulative and more, and make a plot results for `ResultManager` that runs the same plot on all results in a list (currently implemented in `ResultManager:plot_results`).

## 6. Result reporting
A summary is needed twice — once for a human reading the log, and once for a machine reading the archive. Writing them separately is how the two slowly stop agreeing.

So [`_get_summary_body`](../src/utils/result_manager.py#L99) returns the metrics as plain data, and both [`get_summary`](../src/utils/result_manager.py#L53) (text) and [`get_summary_json`](../src/utils/result_manager.py#L75) (json) are rendered from it. A subclass that adds a metric gets it in both formats for free.

## 7. Result identification and archiving
Every run gets its own folder, named with a timestamp or with whatever `--rsf` was given ([`pytest_configure`](../src/tests/conftest.py#L39)), and inside it every test gets a subfolder named after its full test id ([`conftest.py:162`](../src/tests/conftest.py#L162)). That way a parametrized case is identified by its own name and two runs can never overwrite each other.

The pytest log is redirected into the same run folder, so the log and the data of a run always travel together. `--compact-result` zips the whole run at the end of the session ([`global_teardown`](../src/tests/conftest.py#L172)) so a run can be attached to a bug report as one file.

## 8. Error handling
The ammeter fixtures assert the type of what they are given ([`conftest.py:105`](../src/tests/conftest.py#L105)) so a wrong `parametrize` fails immediately with a clear message instead of failing later inside the sampling loop. [`AmmeterManager.get`](../src/utils/utils.py#L21) waits for the port to actually listen and raises a `RuntimeError` with the ammeter name if it never comes up, instead of letting the first read fail with a confusing connection error.

The client raises on an empty answer rather than returning `None` ([`client.py:19`](../Ammeters/client.py#L19)), because a missing measurement is a test failure and should not be able to reach the statistics as a silent hole.

## 9. Accuracy assessment - why it is precision and not accuracy
The spec asks to determine relative accuracy and identify the most reliable device. On this rig that is not measurable, and I would rather write that down than produce a number that looks like an answer.

The three emulators each draw their own random values from their own distribution — [Greenlee](../Ammeters/Greenlee_Ammeter.py) 0.01–100 A, [ENTES](../Ammeters/Entes_Ammeter.py) 5–200 A, [CIRCUTOR](../Ammeters/Circutor_Ammeter.py) 0.001–0.1 A. They are not measuring a shared current, so there is no true value to be accurate against and the readings can not be compared directly.

What can be measured is precision — spread, coefficient of variation, run to run stability. That is what the comparison test should report, and it is what the remaining `#TODO` in [`test_ammeter.py:134`](../src/tests/test_ammeter.py#L134) is for.

## 10. Naming and Typing
Even though Python does not need hard typing, I think it makes it easier to edit code that was not touched for a long time and for debugging.

## 11. Logging
As the code and the ammeters are working on "remote" servers we need to use logging instead of print to avoid writing over each other. It also helps for debugging and finding problems by splitting logs into multiple levels.

## 12. Fixes to the supplied code
The exercise asks to fix the errors in the given code and explain the fixes.

| # | Problem | Fix |
|---|---|---|
| 1 | [`main.py`](../main.py) started the emulators on ports 5001 / 5002 / 5003, but the README and the config say 5000 / 5001 / 5002, so nothing could connect where the documentation said it should | The ports are read from [`config.yaml`](../config/config.yaml) ([`main.py:21`](../main.py#L21)) so there is one source of truth |
| 2 | The measurement requests in `main.py` were commented out as "shouldn't work". The commands used (`b'MEASURE_GREENLEE'`) are not what the server compares against (`b'MEASURE_GREENLEE -get_measurement'`), so the server matched nothing, answered nothing, and the client waited forever in `recv` | The requests now pass `ammeter.get_current_command`, which is exactly the byte string the server checks ([`main.py:31`](../main.py#L31)) |

## 13. Limited usage of AI (for non-documentation purposes)
As this is a test to simulate work that can't be done remotely / needs to be secure, I used AI at a minimal rate (mostly for the MD files and low level debug) as AI like Claude / Copilot sends the code remotely, which I think defeats the purpose of the exercise.
