# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Lean 4 beginner/example project using Lake build system. Lean toolchain: `leanprover/lean4:v4.15.0` (specified in `lean-toolchain`).

## Common Commands

```bash
# Build
lake build

# Run the executable
lake exe hello

# Interpret without compiling
lake env lean --run Main.lean

# Clean build artifacts
lake clean

# Update dependencies
lake update
```

## Architecture

The project has two modules:

- **`Main.lean`** — executable entry point. Contains `def main : IO Unit`. Imports `Hello` and prints `s!"Hello, {hello}!"`.
- **`Hello.lean`** — library root module. Re-exports `Hello.Basic` via `import Hello.Basic`.
- **`Hello/Basic.lean`** — defines `hello : String := "world"`.

To add a new module: create `Hello/<Name>.lean`, then add `import Hello.<Name>` to `Hello.lean`.

## Build Configuration

`lakefile.toml` defines:
- `defaultTargets = ["hello"]`
- `[[lean_lib]] name = "Hello"` (rooted at `Hello.lean`)
- `[[lean_exe]] name = "hello", root = "Main"` (entry at `Main.lean`)

## CI

GitHub Actions workflow at `.github/workflows/lean-action.yml` runs `leanprover/lean-action@v1` on push/PR. It reads `lean-toolchain` to install the correct Lean version automatically.
