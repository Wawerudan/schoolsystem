"""
URL configuration for Dan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path ,include
from store import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path("report/", views.report_start_of_term, name="report"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("signup/", views.signup_view, name="signup"),
    path('', views.student_dashboard, name='student_dashboard'),
    path('studentchart/', views.student_chart, name="students-dashboard"),
    path('students-results/', views.results, name='students-results'),
    path('download-pdf/', views.download_pdf, name='download_pdf'),
    path('register/', views. register_subjects, name='register'),
    path("exam-card/", views.generate_exam_card, name="exam_card"),
    path('timetable/', views.class_timetable, name='class_timetable'),
    path("timetable/<int:class_id>/", views.class_timetable, name="view_timetable"),
    path("send-results/", views.send_results_view, name="send_results"),
    path('student-plot/', views.student_performance_plot, name='student_plot'),
 

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)