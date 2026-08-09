# Design Decisions
This document will briefly go over the design decisions

## 1. Usage of pytest library
As this project is supposed to simulate a testing environment, the decision to use pytest was basic as it lets us focus on the testing without the need to reinvent the wheel from zero.

Pytest is a robust framework that lets us log and save wanted results, with an easy way to add functions to run before / after / around tests as needed. In addition, with a minimal addition we can add a connection to a database to save to.

In general in Python we can and should use common libraries to help new developers join the project faster without the need to go over the full stack to make small changes.

## 2. Limited usage of AI (for non-documentation purposes)
As this is a test to simulate work that can't be done remotely / needs to be secure, I used AI at a minimal rate (mostly for the MD files and low level debug) as AI like Claude / Copilot sends the code remotely, which I think defeats the purpose of the exercise.

## 3. Naming and Typing
Even though Python does not need hard typing, I think it makes it easier to edit code that was not touched for a long time and for debugging.

## 4. Logging
As the code and the ammeters are working on "remote" servers we need to use logging instead of print to avoid writing over each other. It also helps for debugging and finding problems by splitting logs into multiple levels.

## 5. Result manager
A combined result object makes it easier to plan for the future and is the bread and butter of OOP code.

This is why I split the results into 3 main classes
### 5.1. ResultManager
Used for saving and general manipulation of results (plots).
If I had more robust plots I would have split the plotting into another class, but as the plots are and should be more specific per test, it isn't usually needed.

### 5.2. Sampler
Used for sampling in a loop with a function. Can be used as a parent for specializations.
I used it for sampling to ensure a common sampling function between tests.

### 5.3. SamplerResult
A general result class. The more specialized NumericSamplerResult can be used for multiple numeric results, but if I was testing a string answer from a server, or a boolean sample of whether I am connected to a server, I could use a child of SamplerResult for common functionality.

### 5.4. Future development
If I had more tests to create / plot I would move the plotting to the result class and add common result plots like hist / scatter / cumulative and more, and make a plot results for `ResultManager` that runs the same plot on all results in a list (currently implemented in `ResultManager:plot_results`).
