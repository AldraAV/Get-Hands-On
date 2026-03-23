"""
Get Hands-On — PDF Security Engine
Encrypt/decrypt PDFs using pikepdf.
Password protection, permissions, and unlock.
"""

from pathlib import Path
from typing import List, Callable, Optional
import pikepdf


def encrypt_pdf(
    input_file: Path,
    output_file: Path,
    user_password: str = "",
    owner_password: Optional[str] = None,
    allow_printing: bool = True,
    allow_copying: bool = False,
    log_cb: Callable = None
) -> List[Path]:
    """Encrypt a PDF with password protection.
    
    Args:
        input_file: Source PDF
        output_file: Encrypted output
        user_password: Password required to open the PDF
        owner_password: Password for full permissions (defaults to user_password)
        allow_printing: Allow users to print
        allow_copying: Allow users to copy text
    """
    if not owner_password:
        owner_password = user_password

    if log_cb:
        log_cb(f"[LOCK] Protegiendo {input_file.name}...")

    pdf = pikepdf.open(str(input_file))

    permissions = pikepdf.Permissions(
        print_lowres=allow_printing,
        print_highres=allow_printing,
        extract=allow_copying,
        modify_annotation=False,
        modify_assembly=False,
        modify_form=False,
        modify_other=False,
        accessibility=True
    )

    encryption = pikepdf.Encryption(
        user=user_password,
        owner=owner_password,
        allow=permissions,
        aes=True,
        R=6  # AES-256
    )

    pdf.save(str(output_file), encryption=encryption)
    pdf.close()

    if log_cb:
        log_cb(f"[OK] PDF protegido: {output_file.name} (AES-256)")

    return [output_file]


def decrypt_pdf(
    input_file: Path,
    output_file: Path,
    password: str = "",
    log_cb: Callable = None
) -> List[Path]:
    """Remove password protection from a PDF.
    
    Args:
        input_file: Encrypted PDF
        output_file: Decrypted output
        password: Password to unlock (user or owner)
    """
    if log_cb:
        log_cb(f"[UNLOCK] Desbloqueando {input_file.name}...")

    try:
        pdf = pikepdf.open(str(input_file), password=password)
    except pikepdf.PasswordError:
        raise ValueError("Password incorrecto. No se pudo desbloquear el PDF.")

    # Save without encryption
    pdf.save(str(output_file))
    pdf.close()

    if log_cb:
        log_cb(f"[OK] PDF desbloqueado: {output_file.name}")

    return [output_file]


def is_encrypted(file_path: Path) -> bool:
    """Check if a PDF is password-protected."""
    try:
        pdf = pikepdf.open(str(file_path))
        pdf.close()
        return False
    except pikepdf.PasswordError:
        return True
    except Exception:
        return False
