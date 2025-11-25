from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# --- Custom Manager ---
class StudentManager(BaseUserManager):
    def create_user(self, admission_no, password=None, **extra_fields):
        if not admission_no:
            raise ValueError("Admission number is required")
        student = self.model(admission_no=admission_no, **extra_fields)
        student.set_password(password)
        student.save(using=self._db)
        return student

    def create_superuser(self, admission_no, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(admission_no, password, **extra_fields)

class ClassLevel(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class Student(AbstractBaseUser, PermissionsMixin):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.SET_NULL, null=True, blank=True)
    admission_no = models.CharField(max_length=20, unique=True)  # login username
    First_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100, blank=True, null=True)
    form = models.CharField(max_length=20)
    
    image = models.ImageField(upload_to='profile/', blank=True, null=True)
    parent_no = models.CharField(max_length=15)
    gender = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)

    # Required fields for AbstractBaseUser + PermissionsMixin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # admin access
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'admission_no'
    REQUIRED_FIELDS = ['First_name', 'surname']

    objects = StudentManager()

    def __str__(self):
        return f"{self.First_name} {self.surname} ({self.admission_no})"

from django.core.exceptions import ValidationError

def validate_excel(value):
    if not value.name.endswith(('.xlsx', '.xls')):
        raise ValidationError('Only Excel files (.xlsx or .xls) are allowed.')

class Exam(models.Model):
    term = models.CharField(max_length=10, choices=[
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ])
    year = models.PositiveIntegerField()
    exam_name = models.CharField(max_length=100)
    upload_results = models.FileField(
        upload_to='exam_results/',
        validators=[validate_excel],
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.exam_name} - {self.term} {self.year}"



class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    marks = models.FloatField()
    subject_position = models.IntegerField(null=True, blank=True)
    mean_marks = models.FloatField(null=True, blank=True)
    grade = models.CharField(max_length=5, blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.surname} - {self.subject} ({self.marks})"
 
class ExamSummary(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    total_marks = models.FloatField(null=True, blank=True)
    mean_marks = models.FloatField(null=True, blank=True)
    overall_position = models.PositiveIntegerField(null=True, blank=True)
    points = models.FloatField(null=True, blank=True)
    mean_grade = models.CharField(max_length=5, null=True, blank=True)
   
class Finance(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    

    def save(self, *args, **kwargs):
        # Automatically calculate balance before saving
        self.balance = self.total_fees - self.amount_paid
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.First_name} - Balance: {self.balance}"
    
class Payment(models.Model):
    finance = models.ForeignKey(Finance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, choices=[
        ("cash", "Cash"),
        ("mpesa", "M-Pesa"),
        ("bank", "Bank Transfer"),
    ])

    def __str__(self):
        return f"{self.finance.student.First_name} - {self.amount} on {self.date.date()}" 
    
class Reporting(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    date_reported = models.DateTimeField(auto_now_add=True)
    has_reported = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.term} - {self.has_reported}"



class Subject(models.Model):
    name = models.CharField(max_length=100)
    class_level = models.ForeignKey(ClassLevel, null=True,blank=True,on_delete=models.CASCADE)
    lessons_per_week = models.IntegerField(default=5,null=True,blank=True)

    def __str__(self):
        return self.name
class StudentSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

import uuid

class ExamCard(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)

    def __str__(self):
        return f"{self.student} - {self.term}"

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        
    ]

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='Other'
    )

    

    def __str__(self):
        return self.name
class Room(models.Model):
    name = models.CharField(max_length=50)   
    is_special = models.BooleanField(default=False)

    def __str__(self):
        return self.name
class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_room = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)  # optional

    def __str__(self):
        return f"{self.teacher} - {self.subject} - {self.class_room}"
    
class TimetableSlot(models.Model):
    DAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    class_room = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)

    day = models.CharField(max_length=10, choices=DAYS)
    start_time = models.TimeField()   # NEW
    end_time = models.TimeField()     # NEW

    class Meta:
        unique_together = [
            ("class_room", "day", "start_time"),  # class conflict
            ("teacher", "day", "start_time"),     # teacher conflict
            ("room", "day", "start_time"),        # room conflict
        ]

    def __str__(self):
        return f"{self.class_room} - {self.day} {self.start_time}-{self.end_time}: {self.subject}"
    
class Parent(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    name = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.name}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    sent_to_all = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self) :
        return f"{self.title}"
    
class AnnouncementStatus(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], default='pending')
    error = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('announcement', 'parent')
    
class FeeCategory(models.Model):
    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    term = models.CharField(max_length=20, choices=TERM_CHOICES,null=True,blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        # Auto-calculate total before saving
        self.total = self.amount  # or any formula you want
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.amount})"
