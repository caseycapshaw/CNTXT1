# Building the "Capture to KB" iOS Shortcut

Two Shortcuts, sharing the same backend: one for the Share Sheet (text/URL/
image), one for dictation. Both POST to `https://capture.<domain>/capture`.

You'll need, from the Cloudflare Access "KB capture" service token (shown
once when you create it — if you lost it, regenerate in Zero Trust → Access → Service Auth
and update the Shortcut):

- **Client ID** (looks like `xxxxxxxx.access`)
- **Client Secret** (long hex string)

---

## Shortcut 1 — "Capture to KB" (Share Sheet: text, URL, or image)

1. Open the **Shortcuts** app → tap **+** to create a new shortcut.
2. Tap the shortcut's settings (ⓘ icon) → **Show in Share Sheet** → turn on.
   Under **Share Sheet Types**, enable **Text**, **URLs**, and **Images**.
3. Rename it (tap the name at top): `Capture to KB`.
4. Add action **"Get Details of Images"** — skip this for now, we'll branch.
   Actually simplest approach: add action **"If"** to branch on input type:
   - Add action **If** → Input: `Shortcut Input` → Condition:
     `Is Image` → and a second **If** for `Is URL` — Shortcuts infers this
     automatically if you instead use the simpler pattern below.
   - **Simpler pattern (recommended):** don't branch — just always build a
     multipart request, since `Get Contents of URL` can send a mix of text
     fields and one optional file:
5. Add action **"Get Type of Content"** (optional, for your own reference) —
   or skip straight to building the request:
6. Add action **"Text"** — set its content to `Shortcut Input` if the input
   type is text, or leave it and instead use **"If"** to set separate
   variables. Concretely, do this:
   - Add **If** → `Shortcut Input` `Is Image`.
     - **Then:** Add **"Get Contents of URL"**:
       - URL: `https://capture.<domain>/capture`
       - Method: `POST`
       - Headers:
         - `CF-Access-Client-Id`: `<your Client ID>`
         - `CF-Access-Client-Secret`: `<your Client Secret>`
       - Request Body: **Form** (multipart)
         - Add field `image` → type **File** → value `Shortcut Input`
         - Add field `source` → type **Text** → value `iphone-shortcut`
         - Add field `kind` → type **Text** → value `photo`
     - **Otherwise:** Add **"Get Contents of URL"**:
       - URL: `https://capture.<domain>/capture`
       - Method: `POST`
       - Headers:
         - `Content-Type`: `application/json`
         - `CF-Access-Client-Id`: `<your Client ID>`
         - `CF-Access-Client-Secret`: `<your Client Secret>`
       - Request Body: **JSON**
         - `text` → `Shortcut Input` (as text) — Shortcuts auto-detects
           if the input is a URL vs plain text; for URLs, also set:
         - `url` → `Shortcut Input`
         - `source` → `iphone-shortcut`
         - `kind` → `url` (if the input is a URL) or `note` (if it's text)
   - End If.
7. Add action **"Get Dictionary Value"** on the response, key `path`, then
   **"Show Notification"** with text `Captured: ` + that value, so you get
   confirmation.
8. Test: select some text anywhere → Share → Capture to KB. Check that a new
   file appeared in `raw/` in the vault.

### Notes

- Shortcuts' "Get Contents of URL" JSON body builder lets you add
  dictionary key/value rows directly — set each row's type (Text) and value
  (variable). No need to hand-write JSON.
- If Shortcuts complains about mixing File + Text fields in one Form body,
  build the image path as its own action group (step 6's "Then" branch) so
  it never mixes with the JSON branch.

---

## Shortcut 2 — "Dictate to KB" (voice capture, no Share Sheet needed)

1. Create a new shortcut, name it `Dictate to KB`.
2. Add action **"Dictate Text"** — Language: your default; Stop Listening:
   "After Pause" is easiest for a short note.
3. Add action **"Get Contents of URL"**:
   - URL: `https://capture.<domain>/capture`
   - Method: `POST`
   - Headers:
     - `Content-Type`: `application/json`
     - `CF-Access-Client-Id`: `<your Client ID>`
     - `CF-Access-Client-Secret`: `<your Client Secret>`
   - Request Body: **JSON**
     - `text` → `Dictated Text` (the variable from step 2)
     - `source` → `iphone-shortcut`
     - `kind` → `voice`
4. Add **"Show Notification"** confirming the `path` from the response, as
   above.
5. (Optional) Add this shortcut to your Home Screen, Lock Screen widget, or
   give it a Siri phrase ("Hey Siri, dictate to KB") via the shortcut's
   settings (ⓘ) → **Add to Siri**.

---

## Testing without the tunnel (LAN fallback)

If you're on the same network/VPN as the machine running capture-api
and don't want to go through Cloudflare, swap the headers for:

- `Authorization`: `Bearer <capture-token>` (the value you stored
  with `set-secret capture-token`)

and point the URL at the LAN/VPN address instead of
`capture.<domain>`.
