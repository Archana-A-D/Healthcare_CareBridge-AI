from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage


def health_check(request):
    return JsonResponse({
        "status": "success",
        "message": "CareBridge AI backend is running"
    })


@csrf_exempt
@require_POST
def upload_pdf(request):
    uploaded_file = request.FILES.get('file')

    if not uploaded_file:
        return JsonResponse(
            {"error": "No file uploaded"},
            status=400
        )

    if not uploaded_file.name.lower().endswith('.pdf'):
        return JsonResponse(
            {"error": "Only PDF files are allowed"},
            status=400
        )

    if uploaded_file.content_type != 'application/pdf':
        return JsonResponse(
            {"error": "Invalid file type"},
            status=400
        )

    fs = FileSystemStorage()
    filename = fs.save(uploaded_file.name, uploaded_file)

    return JsonResponse({
        "status": "success",
        "message": "PDF uploaded successfully",
        "filename": filename
    })