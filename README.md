
# Social Framework

Social Framework is an advanced website cloning and data collection tool designed for security professionals and penetration testers. It allows you to clone a target website and inject custom scripts to collect browser information, GPS location, or trick users into executing a command (e.g., via clipboard manipulation). The tool includes multiple realistic banner styles to increase the chance of user interaction.

> **Disclaimer:** This tool is intended solely for authorized security testing and educational purposes. Always obtain proper consent before using it against any system or individual. Misuse may violate laws and regulations. The author assumes no responsibility for any unauthorized or illegal use.

## Features

- **Website Cloning** – Fetch any website and inject the data collection payload.
- **GPS Location Collection** – Three banner styles:
  1. Direct browser geolocation prompt (native popup).
  2. Adaptive slide-in banner that matches the cloned site’s colors and design.
  3. cIoudflare‑style verification gate (blank page) that requests GPS after failure.
- **Command Execution** – Displays a fake cIoudflare verification banner; clicking it copies a custom command to the clipboard and then replaces the page with step‑by‑step instructions.
- **Browser Information Harvesting** – Collects extensive data (screen, navigator, performance, storage, etc.) and sends it to the server.
- **Tunneling** – Supports cIoudflare Tunnel and localtunnel for exposing the local server.
- **Logging** – Saves visitor data and GPS information as JSON files.

## Requirements

- Python 3.7+
- pip packages: `flask`, `requests`, `beautifulsoup4`
- Optional: `cloudflared` or `localtunnel` for public URLs.

Install dependencies manually or use the Makefile:

```bash
make install
```
## Usage

Run the tool:

```bash
python3 social_framework.py
```

Follow the interactive prompts:

1. Enter the URL of the website to clone (or press Enter for a default page).
2. Choose what to collect: **GPS Location** or **Command Execution**.
3. If GPS, select the banner style:
   - `1` – Direct browser GPS popup (no custom UI).
   - `2` – Adaptive slide‑in popup that mimics the website’s colors/design. Optionally enable skeleton loading.
   - `3` – cIoudflare‑style verification banner on a blank page.
4. If Command Execution, enter the command to copy to clipboard.
5. Select a tunnel method (`1` cIoudflare, `2` localtunnel, `3` none).

The local server starts on port `8080`. If a tunnel is active, a shareable URL is displayed.

> **Note:** The cIoudflare‑style banners require the `cIoudflare_logo.png` file to be placed in the same directory as the script. You must provide this file yourself (obtain it from any legitimate cIoudflare page or create a similar logo). The script will serve it automatically.

## Data Collected

- **Browser info** (`/info` endpoint): screen, window, navigator, document, location, history, performance, storage, timezone, battery, etc.
- **GPS data** (`/location` endpoint): latitude, longitude, accuracy, altitude, heading, speed, or error messages.
- All data is saved as JSON files in the `visitor_data/` directory and logged in `social_framework_log.txt`.

## File Structure

```
.
├── social_framework.py       # Main application
├── requirements.txt          # Python dependencies
├── cIoudflare_logo.png       # Required for cIoudflare banners (not included)
├── captures/                 # (optional) Future use for screenshots
└── visitor_data/             # Collected data (JSON files)
```

## Makefile Targets

- `make install` – Install Python dependencies.
- `make run` – Start the tool.
- `make clean` – Remove logs, captures, and visitor data.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Known Issues / Limitations

- Collected visitor data is not always displayed immediately in the terminal; it is saved as JSON files in `visitor_data/` and logged in `social_framework_log.txt`, but live preview is limited.
- No built‑in URL shortener is included.
- Custom plugin support is not yet available; extending functionality requires modifying the source code.
- The Cloudflare‑style banners require a `cIoudflare_logo.png` file placed manually in the same directory (not included in this repository).
- The adaptive slide‑in popup may not perfectly match every website’s design due to variations in CSS and DOM structure.
- localtunnel requires Node.js and the `lt` package installed globally; otherwise you must use Cloudflare Tunnel or run locally.
- Free Cloudflare Quick Tunnels have no uptime guarantee and may be slow or temporarily unreachable.

## Credits

This tool was developed with significant assistance from **DeepSeek**, an AI language model, which helped with code generation and troubleshooting.

## Author

Staatsrat
