Mail CD (Python)
================

This is a build orchestration tool.


# Principles

## Clarity over Performance
When it comes to understanding a complex workflow versus making that workflow fast, prefer human understandability.
People come and go from projects, the next people need to be able to quickly understand what was currently done to be able to adjust to what is needed to be done.
Performance is still important, but areas for optimization must be found without hurting the clarity of the workflow.

## Infrastructure By ID (IBID)
Things like credentials, urls, servernames, etc. (which are just strings) should not be hard-coded into the in-source configuration files.  These items should be referenced by an ID and the build tool should be able to replace them based on the supplied environment.
The intent is to enable different environments like development, staging, production, etc. that teams may need to use, so that changes can be tested without having to change the in-source configuration files before deploying.
The intent is also to provide a best-effort backwards compatability as external resources change, so developers can go back in time and build something older, even though the infrastructure they're currently using has changed.

## Run Local
A developer should have the ability to run the workflow from their local setup should they want to do so.  They should not have to push their code to another system and have to debug their workflow remotely.

## In-source Builds Source
The configuration files that are checked into a source repository should be for producing the binaries and reports local to that repository.  Any items in the workflow that do not require actions directly related to the code being built should not end up in the configuration files checked in to that repository.
Information about dependent jobs that should be kicked off down the line, or before should not be checked into it's configuration files.
These items should be handled by a higher-level orchestration.
The intent is to be able to be more agile as processes in an organization change, that should be seperate from the steps it takes to compile and scan source code.

## Standardization
The in-source workflow configuration files should be written in a generic, easily parsable format, that others can easily write programs to interpret them and execute occordingly.
These in-source config files should not be tied to a particular program, locking people into that program for the forseeable future due to the required amount of resources to switch to a competitor.
