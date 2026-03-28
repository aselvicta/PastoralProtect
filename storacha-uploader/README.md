# Storacha Uploader Bridge

A minimal Node.js 18+ HTTP bridge for uploading canonical JSON files to Storacha using `@storacha/client` with email authentication. Returns a content CID after upload.

## Features

- Loads Storacha agent configuration (after login).
- `POST /upload`: Accepts base64-encoded JSON bytes, returns content CID.
- `GET /health`: Health check endpoint.
- `GET /debug/storacha`: Returns agent and space diagnostics (requires valid authorization).

## Setup

1. Install dependencies:
   ```bash
   cd storacha-uploader
   npm install
   ```

2. Configure shared secret (`STORACHA_UPLOADER_SECRET`) to match backend settings.

   - Option A (recommended): Create `storacha-uploader/.env` with:
     ```
     STORACHA_UPLOADER_SECRET=your-long-random-string
     PORT=8788
     ```
   - Option B: Set environment variables directly.

3. Login to Storacha:
   ```bash
   npm run login -- your@email.com
   ```
   Follow the email authentication flow.

## Running

Start the server:
```bash
npm start
```

## Environment Variables

- `STORACHA_UPLOADER_SECRET`: Required. Must match backend.
- `PORT`: Optional. Defaults to 8788.
- `STORACHA_SPACE_DID`: Optional. Force a specific space DID.

## Backend Integration

In `backend/.env`:
```
STORACHA_UPLOADER_URL=http://127.0.0.1:8788
STORACHA_UPLOADER_SECRET=your-long-random-string
```
Leave `WEB3_STORAGE_TOKEN` empty to use this bridge.

## Notes

- Storacha uploads are public by CID. Do not upload sensitive information in unencrypted JSON.
- For local/demo use without Storacha, leave uploader URL and secret empty; backend will use mock CIDs.

