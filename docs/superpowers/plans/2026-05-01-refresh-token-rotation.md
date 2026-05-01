# Refresh Token Rotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist Microsoft OAuth `refresh_token` rotation whenever the token endpoint returns a replacement token.

**Architecture:** Keep the existing token acquisition flow in `main.py`. Add a focused helper that updates only the matching account's `refresh_token` in `ACCOUNTS_FILE` while preserving all other account metadata. Call it after a successful token response and before returning the `access_token`.

**Tech Stack:** Python, FastAPI, httpx, pytest.

---

### Task 1: Persist rotated refresh tokens

**Files:**
- Modify: `main.py`
- Create: `tests/test_refresh_token_rotation.py`

- [ ] **Step 1: Write the failing tests**

Create tests that patch `httpx.AsyncClient` and `ACCOUNTS_FILE`, then assert:
- returned `refresh_token` replaces the stored token for the same email;
- missing returned `refresh_token` leaves the stored token unchanged;
- unrelated metadata and other accounts are preserved.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_refresh_token_rotation.py -q`

Expected: tests fail because no helper persists rotated refresh tokens yet.

- [ ] **Step 3: Implement minimal code**

Add `persist_rotated_refresh_token(credentials, new_refresh_token)` in `main.py` near account persistence helpers. It should no-op for empty or unchanged tokens, reload `accounts.json` under the existing lock, update only `accounts[credentials.email]["refresh_token"]`, preserve other keys, and raise `HTTPException(500)` if the account no longer exists.

Call it from `get_access_token()` after validating `access_token`.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_refresh_token_rotation.py -q`

Expected: all focused tests pass.

- [ ] **Step 5: Run smoke verification**

Run: `python -m py_compile main.py`

Expected: command exits 0.

### Task 2: Publish and deploy

**Files:**
- Modify: Railway service source/configuration
- Create: GitHub repository under the authenticated user

- [ ] **Step 1: Push branch/repo to GitHub**

Create a user-owned repository and push the modified source.

- [ ] **Step 2: Point Railway at the GitHub repo**

Update the existing Railway service from Docker image deployment to GitHub repo deployment, preserving volume, domain, and environment variables.

- [ ] **Step 3: Verify production**

Check deployment status and call `/api/auth/state` on the configured domain.
