Mail CD (Python)
================

A build orchestration tool built for developers with enterprise adoption in-mind.
To minimize CI/CD vendor lock-in, but still maintianing the in-source pipeline file, we need to keep the in-source pipeline file as thin and abstract as possible.  The primary focus is building the project, leaving business logic to another layer.

Let's get started on building your first pipeline, we can discuss more on the principles later...
Just remember, the pipeline should focus as much as it can on what needs to happen, not how.

# Install

## Pre-requirements

1. Windows 10+
2. Docker Desktop

This tool currently depends on 'Docker Desktop' to be installed.
It is used to build and run both Windows and Linux containers.

> **Note:** Linux support coming soon, but will only be able to use Linux containers.

## Virtual Environment

### From Source

Install the application from source into a Python virtual environment:

```sh
git clone https://github.com/mrdalrymple/mailbox.git
python -m venv .venv
.venv/Scripts/activate
python -m pip install ./mailbox
```

### From pypi

*Not available yet.*


# Tutorial

We're going to create a project that builds in a container; that container's image will be made from a Dockerfile.
Sounds standard right?  Let's see what it looks like...

## Creating The Pipeline File

1. Create a project directory

    ```sh
    mkdir myproject
    cd myproject
    ```

2. Create a Dockerfile for the project

    **File:** ./Dockerfile
    ```Dockerfile
    FROM ubuntu:latest
    ```

3. Create a file in the root of your project named: pipeline.yml

4. Add your first stage to the pipeline (using yml syntax)

    **File:** ./pipeline.yml
    ```yaml
    stages:
      mycompile:
    ```
    >**Note**: `stages` is a keyword, `mycompile` is a user-defined name of the stage.

This stage we're writing needs a place to execute from...

5. Set the `node` of the stage to be from our Dockerfile

    **File:** ./pipeline.yml
    ```yaml
    stages:
      mycompile:
        node:
          containerfile: "Dockerfile"
    ```

    > **Note**: `node` and `containerfile` are both keywords, while "Dockerfile" is the relative filepath to the Dockerfile for our project.

Our project needs to run some build commands, let's fake it for now...

6. Add a step to *"build"* our *"project"*

    **File:** ./pipeline.yml
    ```yaml
    stages:
      mycompile:
        node:
          containerfile: "Dockerfile"
        steps:
          - echo fake program > myprogram.exe
    ```

    > **Note:** `steps` is a keyword, everthing in the list under it will be executed in order.

## Running The Pipeline

Open a terminal that has mailbox installed and run this build command from the root of your project:


```sh
mb build
```

Output:
```sh
(.venv) myproject>mb build
========== STAGES ==========
> Starting Stage: mycompile
Container not found, building 'linux:Dockerfile' (00731df6dccbd8bd8a617fc2a8424e9bee47025a)
mycompile> echo fake program > myprogram.exe
?=0
=============================
```

What just happened?  Well, this is roughly what happened:

* We noticed that the Dockerfile hasn't been built yet, so we built that.
  * As long as the Dockerfile isn't changed, we won't rebuild it again
* We started up the image that corresponds to the Dockerfile
* We attached to the running container
* We went through the list of steps and ran then one-by-one.

> **Pro-Tip:** Closed your terminal but want to look at the build logs? Try running `mb logs` in your project root.
> For this example, try: `mb logs build/mycompile`

So we now have our super useful program built, now we want to package it up so we can easily share it!

## Package The Product

Right now we just have an "executable", but we will have more things eventually.  Let's start now with creating the package of our project:

1. Add an `outbox` section to our stage

    **File:** ./pipeline.yml
    ```yaml
    stages:
    // ...
    outbox:
    ```

    > **Note:** This is where we will define packages we want to make.

2. Add a package for our project that contains our executable at the root of the package

    **File:** ./pipeline.yml
    ```yaml
    stages:
      mycompile:
        node:
          containerfile: "Dockerfile"
        steps:
          - echo fake program > myprogram.exe
    outbox:
      myproject:
        - "*.exe -> /"
    ```

## Saving The Pipeline

Now that we have something working, here is a good point to save our current state.
Check-in both the 'pipeline.yaml' and 'Dockerfile' files into your source control.
Going forward, any new feature to your project that requires an update to how it's built, or the container it's built in should be checked-in commit that enables that new feature.

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
