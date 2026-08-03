"""Download consolidated regulation texts from EUR-Lex.

EUR-Lex documents are addressable by CELEX number:
    https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:<celex_id>

Known CELEX numbers for this project (verify against eur-lex.europa.eu before relying on
them — consolidated-text URLs and available languages change over time):
    AI Act (Regulation (EU) 2024/1689)      -> 32024R1689
    NIS2 Directive (Directive (EU) 2022/2555) -> 32022L2555
    CSRD (Directive (EU) 2022/2464)          -> 32022L2464

This script does not hardcode network calls to those URLs — fill in `REGULATIONS` below with
the exact URLs you've confirmed on eur-lex.europa.eu (HTML or PDF), then run.
"""

from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).parent / "regulations"

REGULATIONS: dict[str, str] = {
    # "ai_act.html": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689",
    # "nis2.html": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022L2555",
    # "csrd.html": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022L2464",
}


def download_all():
    OUTPUT_DIR.mkdir(exist_ok=True)
    if not REGULATIONS:
        print(
            "REGULATIONS is empty — confirm the exact EUR-Lex URLs for the AI Act, NIS2, and "
            "CSRD consolidated texts, then fill in the dict at the top of this file."
        )
        return

    for filename, url in REGULATIONS.items():
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        (OUTPUT_DIR / filename).write_bytes(response.content)
        print(f"Saved {filename}")


if __name__ == "__main__":
    download_all()
