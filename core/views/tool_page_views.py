import io
import os
import tempfile
# ĐÃ XÓA: import pythoncom (Vì Linux không chạy được cái này)

from django.shortcuts import render
from django.http import FileResponse

# --- THƯ VIỆN XỬ LÝ ---
from pdf2docx import Converter  # Cho PDF -> Word
import mammoth                  # Cho Word -> HTML
from xhtml2pdf import pisa      # Cho HTML -> PDF

# --- FORM ---
from core.forms import PdfToWordForm, WordToPdfForm

# ==========================================
# 1. VIEW CHÍNH: DANH SÁCH CÔNG CỤ
# ==========================================
def tool_page(request):
    office_tools = [
        # --- CÁC TOOL ĐÃ CÓ CHỨC NĂNG THỰC ---
        {
            "name": "Chuyển đổi File", 
            "desc": "Chuyển đổi định dạng PDF sang DOCX và ngược lại.", 
            "icon": "file-text", 
            "get_absolute_url": "/tools/convert-document/",
            "is_new": True
        },
        # --- CÁC TOOL DỰ KIẾN ---
        {"name": "OCR Ảnh", "desc": "Lấy text từ hình ảnh", "icon": "scan-text", "get_absolute_url": "#"},
        {"name": "Nén Ảnh", "desc": "Giảm dung lượng nhanh", "icon": "image-minus", "get_absolute_url": "#"},
        {"name": "AI Assistant", "desc": "Chat với AI", "icon": "bot", "get_absolute_url": "#"},
        {"name": "Xóa Background", "desc": "Tách nền ảnh", "icon": "eraser", "get_absolute_url": "#"},
        {"name": "Tạo mã QR", "desc": "Tạo QR link, Wifi...", "icon": "qr-code", "get_absolute_url": "#"},
        {"name": "Ghi chú", "desc": "Note nhanh ý tưởng", "icon": "sticky-note", "get_absolute_url": "#"},
        {"name": "File Mẫu", "desc": "Hợp đồng, đơn từ...", "icon": "files", "get_absolute_url": "#"},
        {"name": "Download", "desc": "Bộ cài phần mềm", "icon": "download-cloud", "get_absolute_url": "#"},
        {"name": "Lương Net", "desc": "Tính Gross sang Net", "icon": "calculator", "get_absolute_url": "#"},
        {"name": "BHTN", "desc": "Bảo hiểm thất nghiệp", "icon": "landmark", "get_absolute_url": "#"},
        {"name": "Giờ Về", "desc": "Đếm ngược tan làm", "icon": "timer", "get_absolute_url": "#"},
    ]
    return render(request, "core/tool_page.html", {"all_tools": office_tools})


# ==========================================
# 2. VIEW XỬ LÝ CHUYỂN ĐỔI (LINUX COMPATIBLE)
# ==========================================
def tool_convert_unified(request):
    form_pdf = PdfToWordForm()
    form_word = WordToPdfForm()
    active_tab = 'pdf-to-word'

    if request.method == 'POST':
        
        # -------------------------------------
        # CASE A: PDF SANG WORD
        # -------------------------------------
        if 'submit_pdf_to_word' in request.POST:
            active_tab = 'pdf-to-word'
            form_pdf = PdfToWordForm(request.POST, request.FILES)
            
            if form_pdf.is_valid():
                try:
                    pdf_file = request.FILES['file']
                    # Tạo file tạm PDF
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                        for chunk in pdf_file.chunks():
                            temp_pdf.write(chunk)
                        temp_pdf_path = temp_pdf.name
                    
                    temp_docx_path = temp_pdf_path.replace('.pdf', '.docx')
                    
                    # Chuyển đổi
                    cv = Converter(temp_pdf_path)
                    cv.convert(temp_docx_path, start=0, end=None)
                    cv.close()

                    # Đọc file kết quả vào RAM
                    return_buffer = io.BytesIO()
                    with open(temp_docx_path, 'rb') as f:
                        return_buffer.write(f.read())
                    return_buffer.seek(0)

                    # Dọn dẹp file rác
                    os.remove(temp_pdf_path)
                    os.remove(temp_docx_path)

                    return FileResponse(return_buffer, as_attachment=True, filename=f"{pdf_file.name.replace('.pdf', '')}_converted.docx")
                except Exception as e:
                    form_pdf.add_error(None, f"Lỗi: {str(e)}")

        # -------------------------------------
        # CASE B: WORD SANG PDF (Dùng Mammoth + Xhtml2pdf cho Linux)
        # -------------------------------------
        elif 'submit_word_to_pdf' in request.POST:
            active_tab = 'word-to-pdf'
            form_word = WordToPdfForm(request.POST, request.FILES)
            
            if form_word.is_valid():
                try:
                    word_file = request.FILES['file']
                    
                    # B1: Đọc file Word -> Chuyển thành HTML
                    result = mammoth.convert_to_html(word_file)
                    html_content = result.value
                    
                    # B2: Thêm CSS cơ bản
                    full_html = f"""
                    <html>
                    <head>
                        <style>
                            @page {{ size: A4; margin: 2cm; }}
                            body {{ font-family: sans-serif; font-size: 12pt; line-height: 1.5; }}
                            p {{ margin-bottom: 10px; }}
                            table {{ border-collapse: collapse; width: 100%; }}
                            td, th {{ border: 1px solid black; padding: 5px; }}
                        </style>
                    </head>
                    <body>
                        {html_content}
                    </body>
                    </html>
                    """

                    # B3: Chuyển HTML -> PDF
                    pdf_buffer = io.BytesIO()
                    pisa_status = pisa.CreatePDF(io.BytesIO(full_html.encode("utf-8")), dest=pdf_buffer)

                    if pisa_status.err:
                        form_word.add_error(None, "Lỗi khi tạo PDF từ nội dung Word.")
                    else:
                        pdf_buffer.seek(0)
                        original_name = word_file.name.rsplit('.', 1)[0]
                        return FileResponse(pdf_buffer, as_attachment=True, filename=f"{original_name}_converted.pdf")

                except Exception as e:
                    form_word.add_error(None, f"Lỗi xử lý: {str(e)}")

    context = {
        'form_pdf': form_pdf,
        'form_word': form_word,
        'active_tab': active_tab
    }
    return render(request, 'core/tools/convert_combined.html', context)