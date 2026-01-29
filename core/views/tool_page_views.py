import io
import os
import tempfile
import pythoncom # Thư viện hỗ trợ Windows COM
from django.shortcuts import render
from django.http import FileResponse
from pdf2docx import Converter
from docx2pdf import convert as convert_word_to_pdf # Đổi tên để tránh nhầm lẫn

# Import các Form (Nhớ thêm WordToPdfForm)
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
            "icon": "file-text", # Icon mới cho hợp
            "get_absolute_url": "/tools/convert-document/", # Link tới hàm tool_pdf_to_word
            "is_new": True
        },

        # --- CÁC TOOL DỰ KIẾN (CHƯA CÓ CODE XỬ LÝ) ---
        # Để tạm dấu # ở url để bấm vào không bị lỗi 404
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


def tool_convert_unified(request):
    # Khởi tạo form mặc định
    form_pdf = PdfToWordForm()
    form_word = WordToPdfForm()
    
    # Biến để điều khiển Tab nào đang mở (mặc định là pdf-to-word)
    active_tab = 'pdf-to-word' 

    if request.method == 'POST':
        # --- TRƯỜNG HỢP 1: XỬ LÝ PDF -> WORD ---
        if 'submit_pdf_to_word' in request.POST:
            active_tab = 'pdf-to-word'
            form_pdf = PdfToWordForm(request.POST, request.FILES)
            
            if form_pdf.is_valid():
                try:
                    pdf_file = request.FILES['file']
                    # 1. Tạo file tạm
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                        for chunk in pdf_file.chunks():
                            temp_pdf.write(chunk)
                        temp_pdf_path = temp_pdf.name
                    
                    temp_docx_path = temp_pdf_path.replace('.pdf', '.docx')
                    
                    # 2. Convert
                    cv = Converter(temp_pdf_path)
                    cv.convert(temp_docx_path, start=0, end=None)
                    cv.close()

                    # 3. Trả file
                    return_buffer = io.BytesIO()
                    with open(temp_docx_path, 'rb') as f:
                        return_buffer.write(f.read())
                    return_buffer.seek(0)

                    # Dọn dẹp
                    os.remove(temp_pdf_path)
                    os.remove(temp_docx_path)

                    return FileResponse(return_buffer, as_attachment=True, filename=f"{pdf_file.name.replace('.pdf', '')}_converted.docx")
                
                except Exception as e:
                    form_pdf.add_error(None, f"Lỗi: {str(e)}")

        # --- TRƯỜNG HỢP 2: XỬ LÝ WORD -> PDF ---
        elif 'submit_word_to_pdf' in request.POST:
            active_tab = 'word-to-pdf'
            form_word = WordToPdfForm(request.POST, request.FILES)
            
            if form_word.is_valid():
                try:
                    word_file = request.FILES['file']
                    # 1. Tạo file tạm
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
                        for chunk in word_file.chunks():
                            temp_docx.write(chunk)
                        temp_docx_path = temp_docx.name
                    
                    temp_pdf_path = temp_docx_path.replace('.docx', '.pdf')

                    # 2. Convert (Dùng COM cho Windows)
                    pythoncom.CoInitialize()
                    convert_word_to_pdf(temp_docx_path, temp_pdf_path)
                    
                    # 3. Trả file
                    return_buffer = io.BytesIO()
                    with open(temp_pdf_path, 'rb') as f:
                        return_buffer.write(f.read())
                    return_buffer.seek(0)

                    # Dọn dẹp
                    try:
                        os.remove(temp_docx_path)
                        os.remove(temp_pdf_path)
                    except: pass

                    return FileResponse(return_buffer, as_attachment=True, filename=f"{word_file.name.rsplit('.', 1)[0]}_converted.pdf")

                except Exception as e:
                    form_word.add_error(None, f"Lỗi: {str(e)}")
                finally:
                    pythoncom.CoUninitialize()

    # Cập nhật lại danh sách công cụ trong hàm tool_page() để trỏ về URL mới này
    # ... (Bạn tự cập nhật hàm tool_page nhé) ...

    context = {
        'form_pdf': form_pdf,
        'form_word': form_word,
        'active_tab': active_tab
    }
    return render(request, 'core/tools/convert_combined.html', context)