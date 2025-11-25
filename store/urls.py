from django.urls import path
from . import views

urlpatterns = [
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
  
  
     
      

      
     
  

]
