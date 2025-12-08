## 配置Model和数据库

### 数据库配置
dijangotut/settings.py 里面定义了项目的配置，包括数据库配置，中间件（MIDDLEWARE），已启用的应用（INSTALLED_APPS）等。   

将 TIME_ZONE 设置为当前所在的时区

- 应用
    Django默认包含 管理员站点，认证系统等应用

    默认开启的某些应用需要至少一个数据表，所以，在使用他们之前需要在数据库中创建一些表。请执行以下命令：
    ```cmd
    python manage.py migrate
    ```
    这个 migrate 命令查看 INSTALLED_APPS 配置，并根据 mysite/settings.py 文件中的数据库配置和提供的数据库迁移文件，**创建任何必要的数据库表**。

### 创建模型
模型定义了数据库表的结构（字段，属性，限制），以及元信息

在这个投票应用中，需要创建两个模型：问题 Question 和选项 Choice。
- Question 模型包括问题描述和发布时间。
- Choice 模型有两个字段，选项描述和当前得票数。每个选项属于一个问题。

编辑 polls/models.py：
    ```python
    from django.db import models

    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField("date published")

    class Choice(models.Model):
        question = models.ForeignKey(Question, on_delete=models.CASCADE)
        choice_text = models.CharField(max_length=200)
        votes = models.IntegerField(default=0)
    ```

ForeignKey定义了一个关系。这将告诉 Django，每个 Choice 对象都关联到一个 Question 对象。

模型代码能够让Django
- 创建对应的数据库schema（生成对应的生成语句，CREATE TABLE）
- 创建可以与 Question 和 Choice 对象进行交互的 Python 数据库 API（增删改查）

但在这之前，需要**将应用添加到 INSTALLED_APPS 列表中**，确切说是把**应用的配置类**添加进去。例如polls的配置类是在polls/apps.py中定义的PollsConfig类。

所以路径就是polls.apps.PollsConfig

    ```python 
    # djangotutorial/settings.py
    INSTALLED_APPS = [
        "polls.apps.PollsConfig",
        "django.contrib.admin",
        ...
    ]
    ```

接着运行
```cmd  
python manage.py makemigrations polls
```

通过运行 makemigrations 命令，Django 会检测你对模型文件的修改，并且把修改的部分储存为一次 迁移。 

迁移是指对数据库进行更改时（新添加模型，删除模型，修改字段等），Django 会存储这些变化，以便以后可以应用到数据库中。迁移文件存储在polls/migrations/0001_initial.py 里

可以通过sqlmigrate命令查看迁移文件对应的SQL语句，命令接受一个应用名和迁移名作为参数
```cmd
py manage.py sqlmigrate polls 0001
```

Django可以使用migrate命令执行这些迁移并且同步管理到数据库中
```cmd
py manage.py migrate
```

迁移是非常强大的功能，它能让你在开发过程中持续的改变数据库结构而不需要重新删除和创建表 - 它专注于使数据库平滑升级而不会丢失数据。三步：

- 编辑 models.py 文件，改变模型。

- 运行 python manage.py makemigrations 为模型的改变生成迁移文件。

- 运行 python manage.py migrate 来应用数据库迁移。


### API
Django为每个模型都提供了一个数据库API，可以用来查询和修改数据。

可以在Django shell中尝试交互这些API
```cmd
py manage.py shell
```

在数据库里的Question表有数据后，在shell输入 Question.objects.all() 会返回数据库中所有Question对象的列表。但是这回返回一个QuerySet对象（<QuerySet [<Question: Question object (1)>]>），不便于人类阅读

通过在模型Question里添加__str__方法，可以让Django在显示对象时使用更友好的字符串表示

    ```python
    class Question(models.Model):
        # ...
        def __str__(self):
            return self.question_text


    class Choice(models.Model):
        # ...
        def __str__(self):
            return self.choice_text
    ```

**给模型增加 __str__() 方法是很重要的，这不仅仅能给你在命令行里使用带来方便，Django 自动生成的 admin 里也使用这个方法来表示对象。**

再添加一个方法，判断问题是否在最近发布：

    ```python
    import datetime

    from django.db import models
    from django.utils import timezone

    class Question(models.Model):
        # ...
        def was_published_recently(self):
            return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
    ```

修改完后，重新启动一个shell （用exit()退出当前shell）

### 管理员界面
Django自带一个功能强大的管理员界面，可以用来创建，查看，更新和删除应用的数据。管理员界面是通过读取模型信息自动生成的。

- 创建一个能够登录到管理员界面的用户：
    ```cmd
    py manage.py createsuperuser
    ```
- 启动开发服务器
    ```cmd
    py manage.py runserver
    ```
- 访问 http://127.0.0.1:8000/admin/
    会根据 LANGUAGE_CODE 里设置的显示语言

    将会看到几种可编辑的内容：组和用户。它们是由 django.contrib.auth 提供的，这是 Django 开发的认证框架

- 向管理员页面添加应用（模型），编辑 polls/admin.py 文件：
    ```python
    from django.contrib import admin

    from .models import Question, Choice

    admin.site.register(Question)
    admin.site.register(Choice)
    ```

- 登录后可以对 Question 和 Choice 进行增删改查