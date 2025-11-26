# 在 Django 里写一个数据库驱动的 Web 应用的第一步是定义模型
# 也就是数据库结构设计和附加的其它元数据 (每个字段的名字，长度，类型等)

from django.db import models

# 在这个投票应用中，需要创建两个模型：问题 Question 和选项 Choice。
# Question 模型包括问题描述和发布时间。
# Choice 模型有两个字段，选项描述和当前得票数。每个选项属于一个问题(外键).

class Question(models.Model):
    question_text = models.CharField(max_length=200)  # 问题文本，最大长度200字符
    pub_date = models.DateTimeField('date published')  # 发布时间，日期时间字段 
    
# __str__ 方法告诉Django在显示对象时应该显示什么内容。通常都会定义
# 没有 __str__ 时，对象通常显示为 Question object (1) 这样的占位。
# 定义后会显示成更有意义的文本，比如问题本身。
    def __str__(self):

        return self.question_text

    def was_published_recently(self):
        from django.utils import timezone
        import datetime
        return timezone.now() - datetime.timedelta(days=1) <= self.pub_date <= timezone.now()

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  # 外键，关联到 Question 模型
    choice_text = models.CharField(max_length=200)  # 选项文本，最大长度200字符
    votes = models.IntegerField(default=0)  # 得票数，整数类型，默认值0

    def __str__(self):

        return f"{self.choice_text} ({self.votes}票)"

# 模型定义给Django提供了相关的信息，有了这些信息，Django可以：

# 1. 为这个应用创建数据库 schema（生成 CREATE TABLE 语句）；

# 2. 创建可以与 Question 和 Choice 对象进行交互的 Python 数据库 API。

# ！！！！！ 但是首先得把 polls 应用安装到我们的项目里。
# 这需要在 mysite/settings.py 文件的 INSTALLED_APPS 列表中添加 'polls.apps.PollsConfig' 
# 具体添加什么，取决于PollsConfig类是在哪个文件。这一次是在app.py文件里定义的。

"""
    migrations 是 Django 用来跟踪模型更改并将这些更改应用到数据库 schema 的系统。
每当你对模型进行更改时，都需要创建一个新的迁移文件，迁移文件在 polls/migrations 目录下。
迁移文件包含了 需要在数据库里创建或者修改的模型（表）的信息。

    例如现在的迁移文件是migrations/0001_initial.py，它是通过运行python manage.py makemigrations polls 命令生成的。
里面包含了当前创建的两个模型（表）的信息 Question 和 Choice，包括它们的字段，主键，外键等。

    通过命令 python manage.py sqlmigrate polls 0001，
会输出Django认为针对这个迁移文件里的模型该使用的sql命令
并不是真的执行，更像是让你看看Django打算执行什么sql语句。

    要进行真正的数据库迁移，需要运行命令 python manage.py migrate
这个 migrate 命令选中所有还没有执行过的迁移并应用在数据库上,也就是将你对模型的更改同步到数据库结构上。
（Django 通过在数据库中创建一个特殊的表 django_migrations 来跟踪执行过哪些迁移)
"""


"""
!!!!!!!!!!!  总结  ！！！！！！！！！

    迁移是非常强大的功能，它能让你在开发过程中持续的改变数据库结构而不需要重新删除和创建表
它专注于使数据库平滑升级而不会丢失数据。

改变模型需要三步：

    1. 编辑 models.py 文件，改变模型。

    2. 运行 python manage.py makemigrations 为模型的改变生成迁移文件。

    3. 运行 python manage.py migrate 来应用数据库迁移。
"""