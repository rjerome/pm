# Scripts Scope

This directory contains helper scripts to run and stop the app across operating systems.

## Current State

- Start scripts for macOS, Windows, and Linux
- Stop scripts for macOS, Windows, and Linux
- Each script wraps the Docker Compose workflow for the current scaffolded app

## Working Guidance

- Prefer straightforward scripts over wrappers with hidden behavior
- Make script names and usage obvious
- Align the scripts with the documented local and Docker workflows
- Keep cross-platform behavior aligned when scripts change
