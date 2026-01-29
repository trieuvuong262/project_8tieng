# core/forms.py
from django import forms

# ==========================================
# 2. FORM PDF SANG WORD
# ==========================================
class PdfToWordForm(forms.Form):
    file = forms.FileField(
        label='Chọn file PDF',
        widget=forms.ClearableFileInput(attrs={
            # Style màu Đỏ (Red) cho khác biệt với tool ảnh
            'class': 'block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-600 file:text-white hover:file:bg-red-700 cursor-pointer',
            'accept': '.pdf'
        })
    )
    
class WordToPdfForm(forms.Form):
    file = forms.FileField(
        label='Chọn file Word',
        widget=forms.ClearableFileInput(attrs={
            # Style màu Xanh đậm (Blue)
            'class': 'block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer',
            'accept': '.doc,.docx'
        })
    )