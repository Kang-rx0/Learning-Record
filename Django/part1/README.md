Django使用MTC架构，Model-Template-Controller；

Model：定义数据库里的表结构和字段
Template：负责页面展示（HTML）
Controller：负责业务逻辑处理，视图函数 （接受请求，处理数据，返回响应）

### 下载
```
python -m pip install Django
```

### 创建项目
```
mkdir djangotutorial
django-admin startproject mysite djangotutorial
```

### 验证Django是否正常
```
cd djangotutorial   
py manage.py runserver
```
会对更改自动更新（类似--reload）

### 在项目内创建应用
**使用 py manage.py startapp**, 会创建出一个 polls 目录，里面包含应用的基本文件
```
py manage.py startapp polls
```

### 第一个view
在 polls/views.py 中添加view
```python
from django.http import HttpResponse
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
```

- 为了能够访问这个view，需要将它和一个URL关联起来。在polls文件夹下创建urls.py文件，并添加以下代码
    ```python
    from django.urls import path

    from . import views

    urlpatterns = [
        path("", views.index, name="index"),
    ]
    ```
- 然后需要在项目的主urls.py中包含这个应用的urls。在 djangotutorial/urls.py 中使用**include**函数包含polls应用的urls
    ```python
    from django.contrib import admin
    from django.urls import include, path

    urlpatterns = [
        path("polls/", include("polls.urls")),
        path("admin/", admin.site.urls),
    ]
    ```
    ```python
    """
    path函数至少需要两个参数：
        - view：视图函数或类
        - route：URL模式字符串
    还可以指定一个可选的name参数，用于给URL模式命名，方便在模板和视图中引用该URL。
    """"
    ```

启动服务器，访问 http://127.0.0.1:8000/polls/ ，会看到 "Hello, world. You're at the polls index." 的页面显示。

