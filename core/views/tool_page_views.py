import io
import os
import tempfile
# ĐÃ XÓA: import pythoncom (Vì Linux không chạy được cái này)
from spire.doc import Document, FileFormat
from django.shortcuts import render
from django.http import FileResponse

# --- THƯ VIỆN XỬ LÝ ---
from pdf2docx import Converter  # Cho PDF -> Word

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
                temp_docx_path = ""
                temp_pdf_path = ""
                try:
                    word_file = request.FILES['file']
                    
                    # 1. Tạo file tạm để Spire đọc
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
                        for chunk in word_file.chunks():
                            temp_docx.write(chunk)
                        temp_docx_path = temp_docx.name
                    
                    temp_pdf_path = temp_docx_path.replace('.docx', '.pdf')
                    
                    # 2. Xử lý chuyển đổi bằng Spire.Doc
                    # Create a Document object
                    document = Document()
                    # Load the Word document
                    document.LoadFromFile(temp_docx_path)
                    # Save to PDF
                    document.SaveToFile(temp_pdf_path, FileFormat.PDF)
                    document.Close()

                    # 3. Trả file về cho người dùng
                    return_buffer = io.BytesIO()
                    with open(temp_pdf_path, 'rb') as f:
                        return_buffer.write(f.read())
                    return_buffer.seek(0)

                    # Dọn dẹp
                    os.remove(temp_docx_path)
                    os.remove(temp_pdf_path)

                    original_name = word_file.name.rsplit('.', 1)[0]
                    return FileResponse(return_buffer, as_attachment=True, filename=f"{original_name}_converted.pdf")

                except Exception as e:
                    # Dọn dẹp nếu lỗi
                    if os.path.exists(temp_docx_path): os.remove(temp_docx_path)
                    if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)
                    form_word.add_error(None, f"Lỗi chuyển đổi: {str(e)}")

    context = {
        'form_pdf': form_pdf,
        'form_word': form_word,
        'active_tab': active_tab
    }
    return render(request, 'core/tools/convert_combined.html', context)