"""Converte o GDD em PDF usando Chrome/Chromium ou LibreOffice."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "GDD_CTRL_REVOLT.html"
TARGET = ROOT / "docs" / "GDD_CTRL_REVOLT.pdf"


def find_browser() -> str | None:
    for executable in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(executable)
        if found:
            return found
    candidates = (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    )
    return next((str(path) for path in candidates if path.exists()), None)


def find_office() -> str | None:
    for executable in ("libreoffice", "soffice"):
        found = shutil.which(executable)
        if found:
            return found
    windows = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
    return str(windows) if windows.exists() else None


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ctrl-revolt-report-") as temp:
        browser = find_browser()
        if browser:
            profile = Path(temp) / "browser-profile"
            generated = Path(temp) / TARGET.name
            command = [
                browser, "--headless=new", "--no-sandbox", "--disable-gpu",
                f"--user-data-dir={profile}", f"--print-to-pdf={generated}",
                "--no-pdf-header-footer", SOURCE.resolve().as_uri(),
            ]
            result = subprocess.run(command, check=False, text=True, capture_output=True)
            if result.returncode == 0 and generated.exists():
                shutil.copyfile(generated, TARGET)
                print(f"PDF gerado: {TARGET}")
                return 0

        office = find_office()
        if not office:
            print("Chrome/Chromium e LibreOffice nao encontrados. Abra o HTML e use Imprimir > Salvar como PDF.")
            return 1
        command = [office, "--headless", "--convert-to", "pdf", "--outdir", temp, str(SOURCE)]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        generated = Path(temp) / f"{SOURCE.stem}.pdf"
        if result.returncode != 0 or not generated.exists():
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return result.returncode or 2
        shutil.copyfile(generated, TARGET)
    print(f"PDF gerado: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
