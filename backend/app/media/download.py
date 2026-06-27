"""
Descarga de grabaciones remotas a disco local.

Acepta CUALQUIER URL de grabación (archivo directo .mp4/.mp3/…, o enlace de
Google Drive — donde viven las grabaciones de Google Meet) y la baja a un
archivo local para que el pipeline la procese igual que una subida.

- Normaliza los enlaces de Drive a su forma de descarga directa (`uc?export=
  download&id=…&confirm=t`), lo que también salta el interstitial de virus-scan
  de archivos grandes.
- NO descarga URLs de sala de Meet en vivo (`meet.google.com/abc-defg-hij`):
  esas no son grabaciones. La grabación de Meet se guarda en Drive — usa ESE
  enlace (o el de "Grabaciones de Meet").
"""
from __future__ import annotations

import os
import re
import uuid
from urllib.parse import parse_qs, urlparse

import httpx

# Carpeta donde caen las grabaciones (subidas y descargadas).
UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

_EXT_BY_MIME = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
}

_DRIVE_HOSTS = {"drive.google.com", "docs.google.com"}


def is_remote_url(ref: str | None) -> bool:
    return bool(ref) and ref.lower().startswith(("http://", "https://"))


def _drive_file_id(url: str) -> str | None:
    """Extrae el file id de las variantes de enlace de Google Drive."""
    parsed = urlparse(url)
    if parsed.netloc not in _DRIVE_HOSTS:
        return None
    # .../file/d/<id>/view
    m = re.search(r"/file/d/([A-Za-z0-9_-]+)", parsed.path)
    if m:
        return m.group(1)
    # .../uc?id=<id> | .../open?id=<id>
    qs = parse_qs(parsed.query)
    if qs.get("id"):
        return qs["id"][0]
    return None


def normalize_media_url(url: str) -> str:
    """Convierte un enlace de Drive a su URL de descarga directa; el resto se deja igual."""
    file_id = _drive_file_id(url)
    if file_id:
        return (
            "https://drive.google.com/uc?export=download"
            f"&id={file_id}&confirm=t"
        )
    return url


def _guess_ext(headers: httpx.Headers, url: str) -> str:
    """Deduce la extensión del archivo desde headers o, en su defecto, la URL."""
    cd = headers.get("content-disposition", "")
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd)
    if m:
        ext = os.path.splitext(m.group(1))[1]
        if ext:
            return ext
    ctype = headers.get("content-type", "").split(";")[0].strip().lower()
    if ctype in _EXT_BY_MIME:
        return _EXT_BY_MIME[ctype]
    ext = os.path.splitext(urlparse(url).path)[1]
    if ext and len(ext) <= 5:
        return ext
    return ".mp4"


def _download_drive(file_id: str, dest_dir: str) -> str:
    """Descarga un archivo de Google Drive usando gdown (maneja confirmación y virus-scan)."""
    try:
        import gdown  # type: ignore
    except ImportError:
        raise RuntimeError(
            "Instala gdown para descargar desde Google Drive: pip install gdown"
        )
    import warnings
    dest_path = os.path.join(dest_dir, f"{uuid.uuid4()}.mp4")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = gdown.download(id=file_id, output=dest_path, quiet=False)
    if not result or not os.path.exists(result) or os.path.getsize(result) == 0:
        raise RuntimeError(
            "No se pudo descargar el archivo de Drive. Verifica que el enlace "
            "tenga acceso 'Cualquiera con el enlace'."
        )
    return result


def download_recording(
    url: str,
    dest_dir: str | None = None,
    *,
    timeout: float = 600.0,
) -> str:
    """
    Descarga `url` a un archivo local en `dest_dir` y devuelve la ruta.

    Lanza RuntimeError con mensaje claro si la descarga falla.
    Para Google Drive usa gdown (maneja confirmación automáticamente).
    """
    dest_dir = dest_dir or UPLOADS_DIR
    os.makedirs(dest_dir, exist_ok=True)

    file_id = _drive_file_id(url)
    if file_id:
        return _download_drive(file_id, dest_dir)

    path: str | None = None
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                ctype = resp.headers.get("content-type", "").lower()
                if "text/html" in ctype:
                    raise RuntimeError(
                        "La URL devolvió una página HTML, no un archivo. "
                        "Sube el archivo directamente o usa un enlace de descarga directa."
                    )
                ext = _guess_ext(resp.headers, url)
                path = os.path.join(dest_dir, f"{uuid.uuid4()}{ext}")
                with open(path, "wb") as out:
                    for chunk in resp.iter_bytes(chunk_size=1 << 16):
                        out.write(chunk)
    except httpx.HTTPError as e:
        raise RuntimeError(f"No se pudo descargar la grabación: {e}") from e

    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        if path and os.path.exists(path):
            os.remove(path)
        raise RuntimeError("La descarga quedó vacía (0 bytes).")
    return path
