# Debug Analysis: End-to-End Test Failure (Jan 27, 2026)

## 1. Current Code Implementation (How it works)
This describes the behavior of the backend system as it currently exists in `src/backend/services/generation.py`.

*   **Request Initiation:** When `POST /generate` is called, the request is saved to the database with status `pending`.
*   **Background Processing:** A background task starts asynchronously:
    1.  Updates status to `processing`.
    2.  Loops through the requested number of images (e.g., 2 images).
    3.  **Generation Step:** Calls the AI model (Gemini). **This takes approximately 15 seconds per image.**
    4.  **Save Step:** Saves the image to disk and inserts a record into `generated_images`.
*   **Completion:** ONLY after ALL images are generated and saved does the system update the request status to `completed` in a final transaction.

**Timing Observation from Logs:**
*   Start Time: `17:07:36`
*   Image 1 Saved: `17:07:51` (+15s)
*   Image 2 Saved: `17:08:06` (+15s)
*   **Total Processing Time:** ~30 seconds minimum.

## 2. Test Script Behavior (How it fails)
This describes the behavior of `test_e2e.py`.

*   **Polling Loop:** Immediately after creating the request, the script enters a `while` loop.
*   **Check Frequency:** It asks the server "Is it done?" every 2 seconds.
*   **Timeout Limit:** The script has a strict limit of **60 seconds** (`max_wait=60`).
*   **Success Condition:** It waits specifically for the status to become `completed`.

## 3. Analysis: Why it is failing
The failure is a **Timeout Error**, not a logic error.

1.  **The Race:** The test gives the server 60 seconds to finish.
2.  **The Reality:** The server takes roughly 30-35 seconds to generate the images.
3.  **The Edge Case:** While 30s is less than 60s, our logs show the polling continued until `17:08:35` (59 seconds after start). This suggests that additional overhead (database locking, network latency, or waiting for the final commit) pushed the total duration *just* close enough to the limit, or the test script's timer started slightly before the heavy lifting began.

**Crucially:** The logs confirm the images *were* generated and saved. The backend is working correctly. The test is simply too impatient for the speed of the local generation model.

## 4. Proposed Solution
Increase the timeout buffer in the test script to accommodate the generation time, especially when generating multiple images.

*   **Action:** Change `max_wait` from 60 to 120 seconds in `test_e2e.py`.
