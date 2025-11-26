"""
URL configuration for mysite project.

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
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('polls/', include('polls.urls')), # 格式为：path('路由前缀/', include('应用名.urls'))
]
# http://localhost:8000/polls/ 就可以访问到polls应用中的视图函数了。
# 这是因为在polls里的urls.py中已经将根路径''映射到了views.index视图函数。

"""
    当有人请求你网站的页面，比如说，"/polls/34/"，
Django 会加载 mysite.urls Python 模块，因为它被setting.py里的 ROOT_URLCONF 设置指向。
它会找到名为 urlpatterns 的变量并按顺序遍历这些模式。
在找到匹配项 'polls/' 之后，它会剥离匹配的文本（"polls/"），
然后将剩余的文本 -- "34/" -- 发送给 'polls.urls' URL 配置以进行进一步处理。
"""
