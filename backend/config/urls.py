"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from api.views import ai_job_status, enqueue_ai_job, enqueue_upload_job, enqueue_translation_job, health_check, upload_pdf, ask_question, translate_summary, usage

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/upload/', upload_pdf),
    path('api/upload-jobs/', enqueue_upload_job),
    path('api/agent/query/', ask_question),
    path('api/agent/jobs/', enqueue_ai_job),
    path('api/translation-jobs/', enqueue_translation_job),
    path('api/agent/jobs/<uuid:job_id>/', ai_job_status),
    path('api/agent/usage/', usage),
    path('api/discharge-summaries/<uuid:summary_id>/ask/', ask_question),
    path('api/discharge-summaries/<uuid:summary_id>/translate/', translate_summary),
]
