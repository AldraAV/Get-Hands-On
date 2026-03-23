"""
Get Hands-On — Batch Processing Engine
Apply any PDF operation to multiple files at once.
"""

from pathlib import Path
from typing import List, Callable, Any, Dict
from enum import Enum


class BatchOp(Enum):
    COMPRESS = "compress"
    TO_WORD = "to_word"
    TO_IMAGES = "to_images"
    ROTATE_ALL = "rotate_all"
    OCR = "ocr"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


def batch_apply(
    input_files: List[Path],
    operation: BatchOp,
    output_dir: Path,
    params: Dict[str, Any] = None,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:
    """Apply a single operation to multiple PDF files.
    
    Args:
        input_files: List of PDF paths to process
        operation: Which operation to apply
        output_dir: Directory for all output files
        params: Operation-specific parameters (quality, dpi, password, etc.)
        progress_cb: Called with (0-100) for overall progress
        log_cb: Called with status messages
    
    Returns:
        List of all generated output file paths
    """
    if params is None:
        params = {}

    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(input_files)
    all_results = []
    errors = []

    if log_cb:
        log_cb(f"[BATCH] Iniciando {operation.value} en {total} archivos...")

    for idx, file in enumerate(input_files):
        try:
            if log_cb:
                log_cb(f"  [{idx+1}/{total}] {file.name}")

            results = _run_single(file, operation, output_dir, params, log_cb)
            all_results.extend(results)

        except Exception as e:
            errors.append((file.name, str(e)))
            if log_cb:
                log_cb(f"  [ERROR] {file.name}: {e}")

        if progress_cb:
            progress_cb(int((idx + 1) / total * 100))

    if log_cb:
        ok = total - len(errors)
        log_cb(f"[BATCH] Completado: {ok}/{total} exitosos, {len(errors)} errores")

    return all_results


def _run_single(
    file: Path,
    operation: BatchOp,
    output_dir: Path,
    params: dict,
    log_cb: Callable = None
) -> List[Path]:
    """Execute a single operation on one file."""

    if operation == BatchOp.COMPRESS:
        from .converters import compress_pdf
        quality = params.get("quality", "medium")
        out = output_dir / f"{file.stem}_compressed.pdf"
        return compress_pdf(file, out, quality=quality, log_cb=log_cb)

    elif operation == BatchOp.TO_WORD:
        from .converters import pdf_to_word
        out = output_dir / f"{file.stem}.docx"
        return pdf_to_word(file, out, log_cb=log_cb)

    elif operation == BatchOp.TO_IMAGES:
        from .converters import pdf_to_images
        fmt = params.get("fmt", "png")
        dpi = params.get("dpi", 300)
        img_dir = output_dir / file.stem
        return pdf_to_images(file, img_dir, fmt=fmt, dpi=dpi, log_cb=log_cb)

    elif operation == BatchOp.ROTATE_ALL:
        from .pdf_ops import rotate_pages
        from pypdf import PdfReader
        angle = params.get("angle", 90)
        reader = PdfReader(str(file))
        all_pages = list(range(1, len(reader.pages) + 1))
        out = output_dir / f"{file.stem}_rotated.pdf"
        return rotate_pages(file, out, pages=all_pages, angle=angle, log_cb=log_cb)

    elif operation == BatchOp.OCR:
        from .converters import ocr_pdf
        lang = params.get("lang", "spa+eng")
        out = output_dir / f"{file.stem}_ocr.pdf"
        return ocr_pdf(file, out, lang=lang, log_cb=log_cb)

    elif operation == BatchOp.ENCRYPT:
        from .security import encrypt_pdf
        password = params.get("password", "")
        out = output_dir / f"{file.stem}_protected.pdf"
        return encrypt_pdf(file, out, user_password=password, log_cb=log_cb)

    elif operation == BatchOp.DECRYPT:
        from .security import decrypt_pdf
        password = params.get("password", "")
        out = output_dir / f"{file.stem}_unlocked.pdf"
        return decrypt_pdf(file, out, password=password, log_cb=log_cb)

    else:
        raise ValueError(f"Operacion no soportada: {operation}")
