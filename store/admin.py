from django.contrib import admin
from.models import Student,Subject,Exam,Result,Finance,Payment,Reporting,ClassLevel,StudentSubject, ExamCard,Teacher,Room,TimetableSlot,TeacherSubject,Parent,Announcement,FeeCategory,AnnouncementStatus,ExamSummary
# Register your models here.

admin.site.register(Parent)
admin.site.register(Subject)
admin.site.register(Exam)
admin.site.register(Reporting)
admin.site.register(ClassLevel)
admin.site.register(StudentSubject)
admin.site.register(ExamCard)
admin.site.register(Room)
admin.site.register(TimetableSlot)
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'marks', 'grade','exam','subject_position','mean_marks')
    search_fields = ('student__admission_no',)
    list_filter = ('exam__exam_name', 'exam__term', 'exam__year')

@admin.register(ExamSummary)
class ExamSummaryAdmin(admin.ModelAdmin):
    list_display = ('student','points','overall_position','total_marks','mean_grade')
    search_fields = ('student__admission_no',)
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('First_name', 'surname', 'class_level', 'admission_no')
    search_fields = ('admission_no',)

@admin.register(Payment)
class PaymentAdminAdmin(admin.ModelAdmin):
    list_display = ('student_name','amount', 'method', 'date')
    search_fields = ('finance__student__admission_no',) 
    def student_name(self, obj):
        return f"{obj.finance.student.First_name} {obj.finance.student.surname}"
    student_name.short_description = "Student"
    
@admin.register(TeacherSubject)
class TeacherSubject(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'class_room', 'room')
    search_fields = ('teacher__name','subject__name') 

@admin.register(Teacher)
class Teacher(admin.ModelAdmin):
    list_display = ('name','phone_number','email','gender')
    search_fields = ('name',) 
    

@admin.register(Finance)
class Finance(admin.ModelAdmin):
    list_display = ('student','total_fees','amount_paid', 'balance')
    search_fields = ('student__admission_no',) 

@admin.register(FeeCategory)
class FeeCategory(admin.ModelAdmin):
    list_display = ('name','amount','total','term')
    search_fields = ('name',) 

from .utils import send_at_sms, format_phone 
from django.contrib import admin, messages


@admin.action(description="Send selected announcement to all parents")
def send_announcement_to_all(modeladmin, request, queryset):
    for announcement in queryset:
        if announcement.sent_to_all:
            messages.warning(request, f"{announcement.title} has already been sent.")
            continue
        
        parents = Parent.objects.all()

        if not parents.exists():
            messages.error(request, "No parents found. Add parent records first.")
            continue
        
        for parent in parents:

            status_obj, created = AnnouncementStatus.objects.get_or_create(
                announcement=announcement,
                parent=parent
            )

            # Skip if phone is missing
            if not parent.phone:
                status_obj.status = 'failed'
                status_obj.error = 'No phone number'
                status_obj.save()
                continue

            # Send SMS
            result = send_at_sms(format_phone(parent.phone), f"{announcement.title}:\n{announcement.content}")

            # Check if AT returned success
            if result.get("status") == "sent":
                status_obj.status = "sent"
                status_obj.error = ""
            else:
                status_obj.status = "failed"
                status_obj.error = result.get("error", "Unknown error")

            status_obj.save()
        
        announcement.sent_to_all = True
        announcement.save()

        messages.success(request, f"Announcement '{announcement.title}' sent to all parents.")


class AnnouncementStatusInline(admin.TabularInline):
    model = AnnouncementStatus
    extra = 0
    readonly_fields = ('parent', 'status', 'error')


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'sent_to_all')
    actions = [send_announcement_to_all]
    inlines = [AnnouncementStatusInline]


admin.site.register(Announcement, AnnouncementAdmin)

