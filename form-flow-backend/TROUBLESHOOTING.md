
# Troubleshooting "TargetClosedError"

If you are seeing `TargetClosedError`, it usually means the browser process crashed or was killed by the OS.

## Quick Fixes

1.  **Re-install Playwright Browsers**:
    ```powershell
    cd form-flow-backend
    playwright install chromium
    ```

2.  **Install System Dependencies** (If on Linux/WSL):
    ```bash
    playwright install-deps
    ```

3.  **Check Memory**:
    Ensure your system has at least 2GB of free RAM.

4.  **Disable Antivirus (Temporary)**:
    Sometimes AV blocks the headless browser process.

## Environment Variables
The latest update removes `--single-process` which improves stability but uses slightly more RAM. If you are on a very low RAM machine (1GB or less), you might need to increase swap space.
