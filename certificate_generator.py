# certificate_generator.py
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os
import tempfile
import traceback

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def truncate_hash(value, length=15):
    if not value or value in ["N/A", "Error"]:
        return value
    return (value[:length] + "...") if len(value) > length else value


def _create_transparent_watermark(logo_path, page_w, page_h, opacity=0.5, rotation=45):
    """Create a rotated, transparent watermark PNG using Pillow."""
    img = Image.open(logo_path).convert("RGBA")
    scale = max((page_w / img.width), (page_h / img.height)) * 1.2
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img = img.rotate(rotation, expand=True)

    r, g, b, a = img.split()
    a = a.point(lambda p: int(p * opacity))
    img.putalpha(a)

    bg = Image.new("RGBA", (int(round(page_w)), int(round(page_h))), (255, 255, 255, 0))
    x = (bg.width - img.width) // 2
    y = (bg.height - img.height) // 2
    bg.paste(img, (x, y), img)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
    os.close(tmp_fd)
    bg.save(tmp_path, format="PNG")
    return tmp_path


def generate_certificate(
    target,
    method,
    status,
    output_path=".",
    logo_path=None,
    opacity=0.25,
    rotation=45,
    wipe_start=None,
    wipe_end=None,
    hash_before=None,
    hash_after=None
):
    try:
        # Ensure absolute path for logo
        if logo_path is None:
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        logo_path = os.path.abspath(logo_path)

        if not os.path.isfile(logo_path):
            raise FileNotFoundError(f"❌ Logo not found at {logo_path}. Please place logo.png in assets/")

        print(f"[DEBUG] Using logo: {logo_path}")

        safe_name = "".join(ch for ch in (os.path.basename(target) or "target") if ch.isalnum() or ch in " _-").strip() or "target"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)
            final_path = os.path.join(output_path, f"certificate_{safe_name}_{timestamp}.pdf")
        else:
            base, ext = os.path.splitext(output_path)
            if ext.lower() == ".pdf":
                parent = os.path.dirname(base) or "."
                os.makedirs(parent, exist_ok=True)
                final_path = f"{base}_{timestamp}{ext}"
            else:
                os.makedirs(output_path, exist_ok=True)
                final_path = os.path.join(output_path, f"certificate_{safe_name}_{timestamp}.pdf")

        c = canvas.Canvas(final_path, pagesize=landscape(A4))
        width, height = landscape(A4)

        watermark_temp = None
        # --- Watermark ---
        try:
            if PIL_AVAILABLE:
                watermark_temp = _create_transparent_watermark(
                    logo_path, page_w=width, page_h=height,
                    opacity=opacity, rotation=rotation
                )
                c.drawImage(watermark_temp, 0, 0, width=width, height=height, mask='auto')
            else:
                try:
                    c.setFillAlpha(opacity)
                except Exception:
                    pass
                c.drawImage(logo_path, 0, 0, width=width, height=height, mask='auto')
        except Exception as e:
            print(f"[ERROR] Failed to draw watermark: {e}")
            traceback.print_exc()

        # Borders
        c.setStrokeColor(colors.HexColor("#0b3d91"))
        c.setLineWidth(6)
        c.rect(24, 24, width - 48, height - 48, stroke=1, fill=0)
        c.setStrokeColor(colors.HexColor("#dfe7f6"))
        c.setLineWidth(1.5)
        c.rect(48, 48, width - 96, height - 96, stroke=1, fill=0)

        # Small top-left logo
        try:
            c.drawImage(logo_path, 60, height - 170, width=110, height=110, mask='auto')
        except Exception:
            traceback.print_exc()

        # Title
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.HexColor("#0b3d91"))
        c.drawCentredString(width / 2, height - 100, "   Certificate of Secure Data Wiping")

        # Subtitle
        c.setFont("Helvetica-Oblique", 14)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2, height - 130, "This certifies that the following secure data erasure process was performed")

        # Target
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor("#b21f1f"))
        c.drawCentredString(width / 2, height - 200, safe_name)

        hash_before_display = truncate_hash(hash_before)
        hash_after_display = truncate_hash(hash_after)

        info_lines = [
            ("Wipe Method", method),
            ("Status", status),
            ("Wipe Start Time", wipe_start or "-"),
            ("Wipe End Time", wipe_end or "-"),
            ("Hash Before Wipe", hash_before_display or "-"),
            ("Hash After Wipe", hash_after_display or "-"),
            ("Certificate Issued", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]

        c.setFont("Helvetica", 14)
        y_pos = height - 240
        for label, value in info_lines:
            c.setFillColor(colors.black)
            c.drawString(180, y_pos, f"{label}:")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(360, y_pos, str(value))
            c.setFont("Helvetica", 14)
            y_pos -= 24

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.gray)
        c.drawCentredString(width / 2, 40, f"© {datetime.now().year} FormatX. All Rights Reserved.")
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, 26, "This certificate is digitally generated and does not require a physical signature.")

        c.save()

        if watermark_temp and os.path.exists(watermark_temp):
            try:
                os.remove(watermark_temp)
            except Exception:
                pass

        print(f"[certificate_generator] ✅ Certificate saved at: {final_path}")
        return final_path

    except Exception:
        traceback.print_exc()
        raise
