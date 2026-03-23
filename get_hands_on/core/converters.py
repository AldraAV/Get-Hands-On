"""
Get Hands-On — Conversion Engine
PDF ↔ Word, PDF ↔ Images, Compression
All operations are local-first, no internet required.
"""

from pathlib import Path
from typing import List, Optional, Callable, Literal
import fitz  # pymupdf


def pdf_to_word(
    input_file: Path,
    output_file: Path,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:
    """Convert PDF to Word (.docx) with layout preservation.
    
    Uses pdf2docx for accurate table/paragraph/image extraction.
    """
    from pdf2docx import Converter

    if output_file.suffix.lower() != '.docx':
        output_file = output_file.with_suffix('.docx')

    if log_cb:
        log_cb(f"[W] Convirtiendo {input_file.name} -> Word...")

    cv = Converter(str(input_file))
    total_pages = len(cv.fitz_doc)

    if progress_cb:
        progress_cb(10)

    cv.convert(str(output_file))
    cv.close()

    if progress_cb:
        progress_cb(100)

    size_kb = output_file.stat().st_size / 1024
    if log_cb:
        log_cb(f"[OK] Word generado: {output_file.name} ({size_kb:.0f} KB, {total_pages} paginas)")

    return [output_file]


def pdf_to_images(
    input_file: Path,
    output_dir: Path,
    fmt: Literal["png", "jpg"] = "png",
    dpi: int = 300,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:
    """Convert each PDF page to an image (PNG or JPG).
    
    Uses pymupdf for high-quality rendering at configurable DPI.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(input_file))
    total = len(doc)
    generated = []

    if log_cb:
        log_cb(f"[IMG] Convirtiendo {input_file.name} -> {fmt.upper()} ({dpi} DPI)...")

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=matrix)

        ext = fmt.lower()
        out_path = output_dir / f"{input_file.stem}_p{i+1}.{ext}"

        if ext == "jpg":
            pix.save(str(out_path), output="jpeg")
        else:
            pix.save(str(out_path))

        generated.append(out_path)

        if progress_cb:
            progress_cb(int((i + 1) / total * 100))

    doc.close()

    if log_cb:
        log_cb(f"[OK] {len(generated)} imagenes generadas en {output_dir}")

    return generated


def images_to_pdf(
    image_files: List[Path],
    output_file: Path,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:
    """Combine multiple images into a single PDF.
    
    Uses img2pdf for lossless conversion (preserves original quality).
    Falls back to Pillow if img2pdf fails (e.g., with RGBA images).
    """
    import img2pdf
    from PIL import Image

    if output_file.suffix.lower() != '.pdf':
        output_file = output_file.with_suffix('.pdf')

    if log_cb:
        log_cb(f"[PDF] Combinando {len(image_files)} imagenes -> PDF...")

    # Prepare images: convert RGBA to RGB, validate formats
    prepared_paths = []
    temp_files = []

    for idx, img_path in enumerate(image_files):
        try:
            with Image.open(str(img_path)) as im:
                if im.mode == 'RGBA':
                    # img2pdf doesn't support RGBA, convert to RGB
                    rgb_im = Image.new('RGB', im.size, (255, 255, 255))
                    rgb_im.paste(im, mask=im.split()[3])
                    temp_path = img_path.parent / f"_temp_rgb_{img_path.stem}.png"
                    rgb_im.save(str(temp_path))
                    prepared_paths.append(str(temp_path))
                    temp_files.append(temp_path)
                else:
                    prepared_paths.append(str(img_path))
        except Exception as e:
            if log_cb:
                log_cb(f"⚠️ Saltando {img_path.name}: {e}")
            continue

        if progress_cb:
            progress_cb(int((idx + 1) / len(image_files) * 50))

    if not prepared_paths:
        raise ValueError("No se pudieron procesar las imágenes seleccionadas.")

    # Convert to PDF
    try:
        pdf_bytes = img2pdf.convert(prepared_paths)
        with open(str(output_file), 'wb') as f:
            f.write(pdf_bytes)
    except Exception:
        # Fallback: use Pillow directly
        images = []
        for p in prepared_paths:
            im = Image.open(p).convert('RGB')
            images.append(im)

        if images:
            images[0].save(
                str(output_file),
                save_all=True,
                append_images=images[1:],
                resolution=150
            )
            for im in images:
                im.close()

    # Cleanup temp files
    for tf in temp_files:
        try:
            tf.unlink()
        except OSError:
            pass

    if progress_cb:
        progress_cb(100)

    size_kb = output_file.stat().st_size / 1024
    if log_cb:
        log_cb(f"[OK] PDF generado: {output_file.name} ({size_kb:.0f} KB, {len(prepared_paths)} paginas)")

    return [output_file]


def compress_pdf(
    input_file: Path,
    output_file: Path,
    quality: Literal["low", "medium", "high"] = "medium",
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:
    """Compress a PDF by optimizing internal structure and images.
    
    Quality levels:
    - low: aggressive compression, smallest file
    - medium: balanced  
    - high: minimal compression, best quality
    """
    if log_cb:
        log_cb(f"[ZIP] Comprimiendo {input_file.name} (calidad: {quality})...")

    original_size = input_file.stat().st_size

    doc = fitz.open(str(input_file))
    total = len(doc)

    # For low/medium quality, re-encode images at lower quality
    if quality in ("low", "medium"):
        from PIL import Image
        import io

        jpeg_quality = {"low": 40, "medium": 65, "high": 85}[quality]

        for i, page in enumerate(doc):
            image_list = page.get_images(full=True)

            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    if not base_image or not base_image.get("image"):
                        continue

                    img = Image.open(io.BytesIO(base_image["image"]))
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')

                    # Downscale for low quality
                    if quality == "low":
                        w, h = img.size
                        img = img.resize((max(w // 2, 1), max(h // 2, 1)), Image.LANCZOS)

                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=jpeg_quality, optimize=True)
                    img.close()

                    # Replace image in document
                    new_img_bytes = buf.getvalue()
                    doc.update_stream(xref, new_img_bytes)
                except Exception:
                    continue

            if progress_cb:
                progress_cb(int((i + 1) / total * 90))

    # Save with garbage collection and deflation
    doc.save(
        str(output_file),
        garbage=4,
        deflate=True,
        clean=True
    )
    doc.close()

    if progress_cb:
        progress_cb(100)

    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100 if original_size > 0 else 0

    if log_cb:
        orig_kb = original_size / 1024
        new_kb = new_size / 1024
        log_cb(f"[OK] Comprimido: {orig_kb:.0f} KB -> {new_kb:.0f} KB ({reduction:.1f}% reduccion)")

    return [output_file]


def ocr_pdf(
    input_file: Path,
    output_file: Path,
    lang: str = "spa+eng",
    dpi: int = 300,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:
    """Apply OCR to a scanned PDF, producing a searchable PDF.
    
    Renders each page as image, runs Tesseract OCR, then creates
    a new PDF with selectable text overlay.
    
    Args:
        input_file: Scanned PDF (image-based pages)
        output_file: Output PDF with text layer
        lang: Tesseract language codes (e.g., 'spa', 'eng', 'spa+eng')
        dpi: Resolution for rendering pages before OCR
    
    Requires: tesseract installed on the system.
    """
    import pytesseract
    from PIL import Image
    import io

    if log_cb:
        log_cb(f"[OCR] Procesando {input_file.name} (idioma: {lang})...")

    doc = fitz.open(str(input_file))
    total = len(doc)

    # Create output PDF
    out_doc = fitz.open()

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        # Render page to image
        pix = page.get_pixmap(matrix=matrix)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # Run OCR — get text with bounding boxes
        try:
            ocr_data = pytesseract.image_to_data(
                img, lang=lang, output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract OCR no esta instalado o no se encuentra en el PATH. "
                "Por favor, descarga e instala Tesseract para Windows, luego reinicia la aplicación.\n"
                "(Revisa el README para mas info)"
            )
        except Exception as e:
            if "tesseract is not installed" in str(e).lower():
                raise RuntimeError("Tesseract OCR no esta instalado. Revisa el README para instrucciones.")
            raise

        # Create new page with same dimensions as original
        new_page = out_doc.new_page(
            width=page.rect.width,
            height=page.rect.height
        )

        # Insert original page image as background
        new_page.insert_image(new_page.rect, stream=img_data)

        # Overlay invisible text for searchability
        scale_x = page.rect.width / pix.width
        scale_y = page.rect.height / pix.height

        for j in range(len(ocr_data['text'])):
            text = ocr_data['text'][j].strip()
            if not text:
                continue

            conf = int(ocr_data['conf'][j]) if ocr_data['conf'][j] != '-1' else 0
            if conf < 30:
                continue

            x = ocr_data['left'][j] * scale_x
            y = ocr_data['top'][j] * scale_y
            w = ocr_data['width'][j] * scale_x
            h = ocr_data['height'][j] * scale_y

            # Insert invisible text (font size 1, opacity 0)
            font_size = max(h * 0.8, 1)
            try:
                new_page.insert_text(
                    (x, y + h),
                    text,
                    fontsize=font_size,
                    color=(1, 1, 1),  # White (invisible over white bg)
                    opacity=0.01      # Nearly invisible
                )
            except Exception:
                continue

        img.close()

        if progress_cb:
            progress_cb(int((i + 1) / total * 100))

        if log_cb and (i + 1) % 5 == 0:
            log_cb(f"  OCR pagina {i+1}/{total}")

    doc.close()

    out_doc.save(str(output_file), garbage=4, deflate=True)
    out_doc.close()

    if log_cb:
        size_kb = output_file.stat().st_size / 1024
        log_cb(f"[OK] OCR completado: {output_file.name} ({size_kb:.0f} KB, {total} paginas)")

    return [output_file]
