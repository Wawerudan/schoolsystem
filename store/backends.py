from django.contrib.auth.backends import ModelBackend
from .models import Student

class AdmissionNoBackend(ModelBackend):
    def authenticate(self, request, admission_no=None, password=None, **kwargs):
        try:
            student = Student.objects.get(admission_no=admission_no)
            if student.check_password(password):
                return student
        except Student.DoesNotExist:
            return None
        return None
