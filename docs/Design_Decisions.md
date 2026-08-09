# Design Decisions
This document will briefy go over the design decisions

## 1. Usage Of pytest library
As this project sopuse to simulate a testing enviormant the desition to use pytest was basic as it lets us focuse on the testing without the need to invent the wheel from zero.

Pytest is a robust framework that let us log and save wanted result with an easy way to add function to run before / after / around tests as needed. in addition with a minimal addition we can add connection to a database to save.

In general in python we can and should use common libararis to help new developers to join the project faster without the need to go over the full stuck to make small changes.  

## 2. Limeted usage of AI (for none documintation popuess)
As this is a test to simulate work that can't be done remotly / needs to be secure, I used AI at a minimal rate (mostly for the MD files and low level debug) as AI like claude / copilot sends the code remotly witch i think avoids the purpose of the exersice

## 3. Naming and Typing
Even so python does not need hard typing i think it makes it easer to edit code that was not touched for a long time and for debuging

## 4. Logging
As the code and the ametters ar working on "remote" servers we need to use logging instead of print to avoid writing over each other. it also help for debuging finding problems by spliting logs to multiple levels.

## 5. Result manager
A combined result object makes it easere to plan for the futer and is the bread and butter of OOP code.

This is why i split the results to 3 main classes
### 5.1. ResultManager
Used for saving and general manipulation of results (plots).
If i had a more robust plots i would have split the ploting into another class, but as the plots are more and sould be more spasific per tests it isnt usualy needed.

### 5.2. Sampler
Used for sampeling in a loop with a function. can be used as a parent for spetializations.
i used it for sampeling to enshure common and sampeling function between tests

### 5.2. SamplerResult
A general result class. can be used the more spetialzied NumericSamplerResult for multiple numeric result, but if i was testing a string answer from a server or a boolean sample if i am connected to a server i could use a child of SamplerResult for cummon functionality.

### 5.4. Futere development
If i had more tests to create / plot i would move the ploting to the result class and add common result plots like hist / scatter / cumulitive and more. and make a plot results for `ResultManager` that runs the same plot on all results in a list (currently implemented in `ResultManager:plot_results`)