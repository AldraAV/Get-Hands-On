
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from pypdf import PdfReader, PdfWriter
from enum import Enum

class SplitMode(Enum):
    ALL = "all"           # 1 archivo por página
    RANGE = "range"       # Páginas X a Y
    SPECIFIC = "specific" # Páginas [1,3,5,...]
    CHUNKS = "chunks"     # Cada N páginas

def split_pdf(
    input_file: Path,
    output_dir: Path,
    mode: SplitMode = SplitMode.ALL,
    page_range: Tuple[int, int] = None,
    pages: List[int] = None,
    chunk_size: int = None,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:

    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(input_file))
    total = len(reader.pages)
    generated = []

    if log_cb: log_cb(f"📄 {input_file.name} → {total} páginas")

    if mode == SplitMode.ALL:
        for i in range(total):
            w = PdfWriter()
            w.add_page(reader.pages[i])
            out = output_dir / f"{input_file.stem}_p{i+1}.pdf"
            with open(out, 'wb') as f: w.write(f)
            generated.append(out)
            if progress_cb: progress_cb(int((i+1)/total*100))

    elif mode == SplitMode.RANGE:
        start, end = page_range
        w = PdfWriter()
        for i in range(start-1, min(end, total)):
            w.add_page(reader.pages[i])
        out = output_dir / f"{input_file.stem}_p{start}-{end}.pdf"
        with open(out, 'wb') as f: w.write(f)
        generated.append(out)
        if progress_cb: progress_cb(100)

    elif mode == SplitMode.SPECIFIC:
        for idx, pn in enumerate(pages):
            if 1 <= pn <= total:
                w = PdfWriter()
                w.add_page(reader.pages[pn-1])
                out = output_dir / f"{input_file.stem}_p{pn}.pdf"
                with open(out, 'wb') as f: w.write(f)
                generated.append(out)
            if progress_cb: progress_cb(int((idx+1)/len(pages)*100))

    elif mode == SplitMode.CHUNKS:
        chunk_num = 0
        for i in range(0, total, chunk_size):
            chunk_num += 1
            w = PdfWriter()
            end = min(i + chunk_size, total)
            for j in range(i, end): w.add_page(reader.pages[j])
            out = output_dir / f"{input_file.stem}_chunk{chunk_num}.pdf"
            with open(out, 'wb') as f: w.write(f)
            generated.append(out)
            if progress_cb: progress_cb(int(end/total*100))

    if log_cb: log_cb(f"✓ {len(generated)} archivos generados en {output_dir}")
    return generated

def merge_pdfs(
    input_files: List[Path],
    output_file: Path,
    page_selection: dict = None,
    progress_cb: Callable = None,
    log_cb: Callable = None
) -> List[Path]:

    writer = PdfWriter()
    total = len(input_files)

    for idx, pdf in enumerate(input_files):
        reader = PdfReader(str(pdf))
        sel = page_selection.get(pdf) if page_selection else None

        if sel:
            for pn in sel:
                if 1 <= pn <= len(reader.pages):
                    writer.add_page(reader.pages[pn-1])
        else:
            for page in reader.pages:
                writer.add_page(page)

        if log_cb: log_cb(f"  + {pdf.name}")
        if progress_cb: progress_cb(int((idx+1)/total*100))

    # Asegurar extensión
    if output_file.suffix.lower() != '.pdf':
        output_file = output_file.with_suffix('.pdf')

    with open(output_file, 'wb') as f: writer.write(f)
    if log_cb: log_cb(f"✓ Unido: {output_file.name}")
    return [output_file]

def rotate_pages(
    input_file: Path,
    output_file: Path,
    pages: List[int],
    angle: int = 90,
    log_cb: Callable = None
) -> List[Path]:
    """Rota las páginas especificadas (1-indexed) por el ángulo dado (90, 180, 270)."""
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    
    # Copiar todas las páginas, rotando las seleccionadas
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        if page_num in pages:
            # Rotar (acumulativo con rotación existente)
            page.rotate(angle)
        writer.add_page(page)
        
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(f"↻ Rotadas {len(pages)} páginas en {output_file.name}")
    return [output_file]

def extract_pages(
    input_file: Path,
    output_file: Path,
    pages: List[int],
    log_cb: Callable = None
) -> List[Path]:
    """Extrae las páginas seleccionadas a un nuevo PDF."""
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    
    # Ordenar páginas para mantener orden del documento original? 
    # O mantener orden de selección? Usualmente orden del documento.
    sorted_pages = sorted(pages)
    
    for pn in sorted_pages:
        if 1 <= pn <= len(reader.pages):
            writer.add_page(reader.pages[pn-1])
            
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(f"📄 Extraídas {len(pages)} páginas a {output_file.name}")
    return [output_file]

def delete_pages(
    input_file: Path,
    output_file: Path,
    pages_to_delete: List[int],
    log_cb: Callable = None
) -> List[Path]:
    """Elimina las páginas seleccionadas del PDF."""
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    
    deleted_count = 0
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        if page_num not in pages_to_delete:
            writer.add_page(page)
        else:
            deleted_count += 1
            
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(f"🗑️ Eliminadas {deleted_count} páginas. Nuevo archivo: {output_file.name}")
    return [output_file]

def duplicate_pages(
    input_file: Path,
    output_file: Path,
    pages_to_duplicate: List[int],
    log_cb: Callable = None
) -> List[Path]:
    """Duplica las páginas seleccionadas y las inserta inmediatamente después de la original."""
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    
    # Sort to handle order correctly? Actually we iterate through original document
    # and if page 'i' is in duplication list, we add it twice.
    
    dup_count = 0
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        writer.add_page(page)
        
        if page_num in pages_to_duplicate:
            writer.add_page(page) # Add duplicate
            dup_count += 1
            
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(f"📑 Duplicadas {dup_count} páginas. Total: {len(writer.pages)}")
    return [output_file]

def insert_blank_page(
    input_file: Path,
    output_file: Path,
    after_page: int,
    log_cb: Callable = None
) -> List[Path]:
    """Inserta una página en blanco después de la página especificada (0 para inicio)."""
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    
    if after_page == 0:
        writer.add_blank_page()
        
    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        if (i + 1) == after_page:
            writer.add_blank_page()
            
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(f"⬜ Página en blanco insertada después de la {after_page}")
    return [output_file]

def move_page(
    input_file: Path,
    output_file: Path,
    page_num: int,
    direction: str, # "left", "right"
    log_cb: Callable = None
) -> List[Path]:
    """Mueve una página hacia la izquierda (anterior) o derecha (siguiente)."""
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    pages = list(reader.pages)
    total = len(pages)
    idx = page_num - 1
    
    if direction == "left" and idx > 0:
        # Swap with previous
        pages[idx], pages[idx-1] = pages[idx-1], pages[idx]
        msg = f"⬅ Movalida página {page_num} a {page_num-1}"
    elif direction == "right" and idx < total - 1:
        # Swap with next
        pages[idx], pages[idx+1] = pages[idx+1], pages[idx]
        msg = f"➡ Movida página {page_num} a {page_num+1}"
    else:
        # No change
        for p in pages: writer.add_page(p)
        with open(output_file, 'wb') as f: writer.write(f)
        return [output_file] # Return same, no op
        
    for p in pages:
        writer.add_page(p)
        
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(msg)
    return [output_file]

def reorder_pages(
    input_file: Path,
    output_file: Path,
    new_order: List[int], # 1-based indices in desired order
    log_cb: Callable = None
) -> List[Path]:
    """Crea un nuevo PDF con las páginas en el orden especificado.
    
    Args:
        new_order: Lista de números de página (1-based) en el orden deseado.
                   Ej: [2, 1, 3] para intercambiar pág 1 y 2.
    """
    
    reader = PdfReader(str(input_file))
    writer = PdfWriter()
    
    # Validar índices con el total de páginas
    total_pages = len(reader.pages)
    
    for page_num in new_order:
        if 1 <= page_num <= total_pages:
            writer.add_page(reader.pages[page_num - 1])
            
    with open(output_file, 'wb') as f: writer.write(f)
    
    if log_cb: log_cb(f"🔀 Páginas reordenadas. Nuevo archivo: {output_file.name}")
    return [output_file]
