## 介绍URLconf 的基础内容

在 Django 中，网页和其他内容都是从视图派生而来。 视图是 Python 函数或类，它们接收 Web 请求并返回 Web 响应。 这些响应可以是 HTML 网页、重定向、404 错误、XML 文档、图像等等。

为每个视图设置URL以访问。为了将 URL 和视图关联起来，Django 使用了 'URLconfs' 来配置。URLconf 将 URL 模式映射到视图。

### 添加更多视图

向 polls/views.py 里添加更多视图：

    ```python
    def detail(request, question_id):
        return HttpResponse("You're looking at question %s." % question_id)

    def results(request, question_id):
        response = "You're looking at the results of question %s."
        return HttpResponse(response % question_id)

    def vote(request, question_id):
        return HttpResponse("You're voting on question %s." % question_id)
    ```

把这些新视图添加进 polls.urls 模块里，只要添加几个 url() 函数调用就行：

    ```python
    from django.urls import path

    from . import views

    urlpatterns = [
        # ex: /polls/
        path("", views.index, name="index"),
        # ex: /polls/5/
        path("<int:question_id>/", views.detail, name="detail"),
        # ex: /polls/5/results/
        path("<int:question_id>/results/", views.results, name="results"),
        # ex: /polls/5/vote/
        path("<int:question_id>/vote/", views.vote, name="vote"),
    ]
    ```

Django会根据 ROOT_URLCONF 设置来查找 URLconf 模块。 在本例中，ROOT_URLCONF 设置为 djangotutorial.urls，因此 Django 会在 djangotutorial/urls.py 文件中找到名urlpatterns 的变量并按顺序遍历这些模式。

访问：http://127.000.1:8000/polls/34/
这会是一个正则匹配的过程，Django 会从上到下依次检查每个模式，直到找到第一个匹配的模式为止。 在找到匹配项 'polls/' 之后，它会剥离匹配的文本（"polls/"），然后将剩余的文本 -- "34/" -- 发送给 'polls.urls' 的URL 配置以进行进一步处理。

### 一个完整的视图

每个视图必须要做的只有两件事：返回一个包含被请求页面内容的 HttpResponse 对象，或者抛出一个异常，比如 Http404 。 （以及其它附加内容）

Django自带的数据库API让你可以轻松地从数据库中获取数据。 下面是一个使用 Django 数据库 API 的例子，展示数据库里以发布日期排序的最近 5 个投票问题，用空格分割：

    ```python
    from django.http import HttpResponse
    from .models import Question

    def index(request):
        latest_question_list = Question.objects.order_by("-pub_date")[:5]
        output = ", ".join([q.question_text for q in latest_question_list])
        return HttpResponse(output)
    ```

接着创建可以被视图调用的模版。在polls目录下创建templates/polls目录

项目的 **TEMPLATES** 配置项描述了 Django 如何载入和渲染模板。默认的设置文件设置了 DjangoTemplates 后端，并将 **APP_DIRS** 设置成了 True。这一选项将会让 DjangoTemplates 在每个 INSTALLED_APPS 文件夹中寻找 "templates" 子目录。

编写 templates/polls/index.html 文件，会跳转（href）：

    ```html
    {% if latest_question_list %}
        <ul>
        {% for question in latest_question_list %}
            <li><a href="/polls/{{ question.id }}/">{{ question.question_text }}</a></li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No polls are available.</p>
    {% endif %}
    ```

然后，更新一下 polls/views.py 里的 index 视图来使用模板，有许多方法可以使用模版，这里使用一个快捷函数 render()，包含了加载模版和返回HttpResponse对象：

    ```python
    from django.shortcuts import render

    from .models import Question


    def index(request):
        latest_question_list = Question.objects.order_by("-pub_date")[:5]
        context = {"latest_question_list": latest_question_list}
        return render(request, "polls/index.html", context)
    ```

    ```python
    """
    render接受三个参数：
        - request：传入的请求对象。
        - template_name：要使用的模板的名称。
        - context（可选）：一个字典，包含传递给模板的数据。
    """
    ```

### 抛出404错误
同样的，有许多方法实现，这里使用一个快捷函数 get_object_or_404()，它接受一个 Django 模型类和任意数量的关键字参数，然后它尝试获取对象，如果没有找到就抛出 Http404 错误：

    ```python
    from django.shortcuts import get_object_or_404, render
    from .models import Question
    def detail(request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        return render(request, "polls/detail.html", {"question": question})
    ```

    ```python
    """
    get_object_or_404()，它接受
        - 一个 Django 模型类
        - 任意数量的关键字参数，用于传给get()方法以查找对象。如果对象存在，返回该对象；否则抛出 Http404 错误。  
    """
    ```

创建 templates/polls/detail.html 文件：

    ```html
    <h1>{{ question.question_text }}</h1>
    <ul>
    {% for choice in question.choice_set.all %}
        <li>{{ choice.choice_text }}</li>
    {% endfor %}
    </ul>
    ```

####  模板语言简介
    模板系统统一使用点符号来访问变量的属性。在示例 {{ question.question_text }} 中，首先 Django 尝试对 question 对象使用字典查找（也就是使用 obj.get(str) 操作），如果失败了就尝试属性查找（也就是 obj.str 操作），结果是成功了。如果这一操作也失败的话，将会尝试列表查找（也就是 obj[int] 操作）。

    在 {% for %} 循环中发生的函数调用：question.choice_set.all 被解释为 Python 代码 question.choice_set.all() ，将会返回一个可迭代的 Choice 对象，这一对象可以在 {% for %} 标签内部使用。

### 去除模版中的硬编码URL
在 polls/index.html 里编写投票链接时，链接是硬编码的：
    ``` html
    <li><a href="/polls/{{ question.id }}/">{{ question.question_text }}</a></li>
    ```
由于在 polls.urls 模块中的 path() 函数中定义了 name 参数，因此可以通过使用 {% url %} 模板标签来消除对 url 配置中定义的特定 URL 路径的依赖：
    ``` html
    <li><a href="{% url 'detail' question.id %}">{{ question.question_text }}</a></li>
    ```

这里的 'detail' 是在 polls/urls.py 中为相应的 path() 函数定义的 name 参数。 question.id 是传递给 URL 模式的参数。

### 为URL添加命名空间
一个项目里可能会有好几个应用，它们可能会有相同的视图名称（例如A应用有index视图，B应用也有index视图）。这就会导致使用 {% url %} 模板标签时出现歧义。为了解决这个问题，可以为每个应用添加一个命名空间。

为 polls应用添加命名空间，在polls/urls.py 文件的开头添加 app_name 变量：

    ``` python
    from django.urls import path

    from . import views

    app_name = "polls"
    urlpatterns = [
        path("", views.index, name="index"),
        path("<int:question_id>/", views.detail, name="detail"),
        path("<int:question_id>/results/", views.results, name="results"),
        path("<int:question_id>/vote/", views.vote, name="vote"),
    ]
    ```
编辑 templates/polls/index.html 文件中的链接跳转部分，使用 {%url 命名空间：视图名%} 的格式：

    ``` html
    <li><a href="{% url 'polls:detail' question.id %}">{{ question.question_text }}</a></li>
    ``` 