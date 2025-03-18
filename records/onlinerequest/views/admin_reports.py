from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.conf import settings
from docxtpl import DocxTemplate
import os
from ..models import ReportTemplate, Purpose
from datetime import datetime
import io
import tempfile
from django.utils.text import slugify

def admin_reports(request):
    templates = ReportTemplate.objects.all()
    return render(request, 'admin/admin_reports.html', {'templates': templates})

def admin_report_form(request, template_id):
    template = get_object_or_404(ReportTemplate, id=template_id)
    purposes = Purpose.objects.filter(active=True)
    return render(request, 'admin/report_form.html', {
        'template': template,
        'purposes': purposes
    })

def admin_generate_report_pdf(request, template_id):
    if request.method != 'POST':
        return redirect('admin_report_form', template_id=template_id)
    
    template = get_object_or_404(ReportTemplate, id=template_id)
    
    # Get form data
    field_mapping = {
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'middle_name': request.POST.get('middle_name', ''),
        'full_name': f"{request.POST.get('first_name', '')} {request.POST.get('middle_name', '')} {request.POST.get('last_name', '')}",
        'contact_no': request.POST.get('contact_no', ''),
        'entry_year_from': request.POST.get('entry_year_from', ''),
        'entry_year_to': request.POST.get('entry_year_to', ''),
        'course': request.POST.get('course', ''),
        'student_number': request.POST.get('student_number', ''),
        'email': request.POST.get('email', ''),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'purpose': request.POST.get('purpose', '')
    }
    
    try:
        # Setup directories
        generated_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'generated')
        os.makedirs(generated_dir, exist_ok=True)
        
        # Ensure proper filename with extension
        safe_name = slugify(template.name)
        if not safe_name:  # In case slugify removes all characters
            safe_name = "report"
        
        docx_path = os.path.join(generated_dir, f"{safe_name}.docx")
        output_filename = f"{safe_name}.docx"  # Explicit filename for download
        
        # Process document using docxtpl for better template handling
        doc_template = DocxTemplate(template.template_file.path)
        doc_template.render(field_mapping)
        doc_template.save(docx_path)
        
        # Serve the DOCX with explicit content disposition header
        response = FileResponse(
            open(docx_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Set explicit Content-Disposition header
        response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
        
        # Add file cleanup after streaming
        response._resource_closers.append(lambda: os.remove(docx_path))
        
        return response
                
    except Exception as e:
        raise Http404(f"Error generating document: {str(e)}")
