# Rollback Procedures & Safeguards: X-Ray Execution Agent

## 1. General Rollback Strategy
Every phase maintains distinct git commits or file backups. If a phase fails verification or violates any anti-vibe-coding constraints, changes must be rolled back immediately before proceeding.

## 2. Phase-by-Phase Rollback Runbook

### Phase 1: Scaffolding Rollback
* **Trigger:** Incorrect directory structure or faulty documentation templates.
* **Commands:**
  ```powershell
  # Remove scaffolded files
  Remove-Item -Path "./*.md" -Force
  ```

### Phase 2: Core Tracer (`tracer.py`) Rollback
* **Trigger:** Tracer causes memory leaks, fails step count limits, or breaks standard execution.
* **Commands:**
  ```powershell
  # Remove tracer implementation and test suite
  Remove-Item -Path "./tracer.py" -Force
  Remove-Item -Path "./test_tracer.py" -Force
  ```

### Phase 3: Backend API Server (`app.py`) Rollback
* **Trigger:** Server fails health checks, route conflicts, or dependency crashes.
* **Commands:**
  ```powershell
  # Terminate background server process if running
  Get-Process -Name "python" | Where-Object { $_.CommandLine -like "*app.py*" } | Stop-Process
  Remove-Item -Path "./app.py" -Force
  Remove-Item -Path "./test_app.py" -Force
  ```

### Phase 4: Static UI & Legal Pages Rollback
* **Trigger:** UI violations detected (e.g., accidental gradient, rounded button, or emoji inclusion).
* **Commands:**
  ```powershell
  Remove-Item -Path "./static" -Recurse -Force
  Remove-Item -Path "./templates" -Recurse -Force
  ```

### Phase 5: Frontend Logic & Visualizer Rollback
* **Trigger:** Timeline desynchronization, DOM rendering memory leak, or broken pointers.
* **Commands:**
  ```powershell
  git checkout HEAD -- static/js/
  ```

## 3. Emergency Safe Mode
If a runtime error occurs during testing:
1. Halt any running background server tasks (`manage_task` or process kill).
2. Inspect log outputs and note exact stack traces in `Bug.md`.
3. Re-run unit tests on the isolated module before restoring integration.
