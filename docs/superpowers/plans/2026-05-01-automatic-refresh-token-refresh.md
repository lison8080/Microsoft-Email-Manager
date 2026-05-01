# Automatic Refresh Token Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automatic weekly refresh-token validation/rotation, a manual refresh button, and per-account refresh-token timestamps.

**Architecture:** Extend `main.py` with a refresh-token task state that reuses existing account credential validation and rotated-token persistence. Store refresh-token metadata in `account_health.json` records so existing account listing can expose it. Update `static/index.html` to trigger the refresh task, poll status, and display checked/rotated times per account.

**Tech Stack:** Python, FastAPI, asyncio, pytest, vanilla HTML/JS.

---

### Task 1: Back-end refresh-token metadata and task runner

**Files:**
- Modify: `main.py`
- Modify: `tests/test_refresh_token_rotation.py`

- [ ] **Step 1: Write failing tests**

Add tests for:
- rotated token persistence stores `refresh_token_checked_at` and `refresh_token_rotated_at`;
- successful token check without token rotation stores checked time but leaves rotated time unchanged;
- account list includes refresh-token metadata;
- `start_refresh_token_check()` returns an existing running task instead of starting a duplicate.

- [ ] **Step 2: Run tests and verify expected failures**

Run: `/tmp/mem-src/.conda-env/bin/python -m pytest tests/test_refresh_token_rotation.py -q`

- [ ] **Step 3: Implement metadata helpers**

Add functions to update account health records with:
- `refresh_token_status`
- `refresh_token_summary`
- `refresh_token_checked_at`
- `refresh_token_rotated_at`

Update `persist_rotated_refresh_token()` to return `True` when rotation is persisted and `False` otherwise.

- [ ] **Step 4: Implement task runner and API**

Add:
- `refresh_token_check_state`
- `run_refresh_token_check_task()`
- `start_refresh_token_check()`
- `POST /accounts/refresh-tokens`
- `GET /accounts/refresh-tokens`

- [ ] **Step 5: Implement automatic scheduler**

Add environment variables:
- `AUTO_REFRESH_TOKENS_ENABLED`
- `AUTO_REFRESH_TOKENS_INTERVAL_HOURS`
- `AUTO_REFRESH_TOKENS_INITIAL_DELAY_SECONDS`
- `AUTO_REFRESH_TOKENS_ACCOUNT_DELAY_SECONDS`

Start the scheduler in FastAPI `lifespan()` and cancel it on shutdown.

### Task 2: Front-end manual button and timestamps

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add button**

Add a button next to “检查账户健康”:

```html
<button class="btn btn-secondary btn-sm" onclick="refreshAccountTokens()" id="accountTokenRefreshBtn">
    <span></span>
    刷新 Refresh Token
</button>
```

- [ ] **Step 2: Add JS polling function**

Add:
- `waitForRefreshTokenCheck(taskId)`
- `refreshAccountTokens()`

Reuse the existing progress bar helpers.

- [ ] **Step 3: Display per-account timestamps**

In account cards, show:
- `Refresh Token 检查`
- `Refresh Token 更新`

Use existing date formatting helpers if available; otherwise add a small display helper.

### Task 3: Verify and deploy

**Files:**
- GitHub repo `lison8080/Microsoft-Email-Manager`
- Railway service `microsoft-email-manager`

- [ ] **Step 1: Verify locally**

Run:
- `/tmp/mem-src/.conda-env/bin/python -m pytest tests/test_refresh_token_rotation.py -q`
- `/tmp/mem-src/.conda-env/bin/python -m py_compile main.py`

- [ ] **Step 2: Commit and push**

Commit and push to `main`.

- [ ] **Step 3: Wait for Railway deployment**

Confirm latest deployment source repo is `lison8080/Microsoft-Email-Manager` and status is `SUCCESS`.

- [ ] **Step 4: Verify production endpoints**

Call:
- `GET https://outlook.lison88.top/api/auth/state`
- `GET https://outlook.lison88.top/accounts/refresh-tokens` with authentication unavailable locally may be skipped if it requires browser session; deployment status is sufficient for API load verification.
