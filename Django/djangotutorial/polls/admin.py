from django.contrib import admin

# Register your models here.
# 为了能在 Django 管理后台（http://127.0.0.1:8000/admin/）看到 Question 和 Choice 模型，
# 需要在这里注册它们。
from .models import Question, Choice

admin.site.register(Question)