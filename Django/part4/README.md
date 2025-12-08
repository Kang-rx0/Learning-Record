## 介绍表单处理和精简代码

### 编写一个简单的表单

编辑 polls/detail.html 文件，添加一个表单（HTML <form> 元素），
- 在Question的每一个Choice前添加一个单选按钮；按钮的value属性对应Choice的ID。
- 每个单选按钮的 name 是 "choice"。
- 当有人选择一个单选按钮并提交表单提交时，它将发送一个 POST 数据 choice= choice的ID 

```html
    <form action="{% url 'polls:vote' question.id %}" method="post">
    {% csrf_token %}
    <fieldset>
        <legend><h1>{{ question.question_text }}</h1></legend>
        {% if error_message %}<p><strong>{{ error_message }}</strong></p>{% endif %}
        {% for choice in question.choice_set.all %}
            <input type="radio" name="choice" id="choice{{ forloop.counter }}" value="{{ choice.id }}">
            <label for="choice{{ forloop.counter }}">{{ choice.choice_text }}</label><br>
        {% endfor %}
    </fieldset>
    <input type="submit" value="Vote">
    </form>
```

完善投票功能的实现（polls/views.py的vote()函数）

```python
    from django.db.models import F
    from django.http import HttpResponse, HttpResponseRedirect
    from django.shortcuts import get_object_or_404, render
    from django.urls import reverse

    from .models import Choice, Question

    def vote(request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        try:
            selected_choice = question.choice_set.get(pk=request.POST["choice"])
        except (KeyError, Choice.DoesNotExist):
            # 如果post的值（选项号）不存在，重新显示Question的投票表单
            return render(
                request,
                "polls/detail.html",
                {
                    "question": question,
                    "error_message": "You didn't select a choice.",
                },
            )
        else:
            # F("votes") + 1 指示数据库 将投票数增加 1。
            selected_choice.votes = F("votes") + 1
            selected_choice.save()
            # 成功处理 POST 数据后始终返回 HttpResponseRedirect。重定向到指定url
            # 这里面使用了 reverse() 函数来避免在视图函数中硬编码 URL。只需提供 URL 模式的名称和所需的参数args，Django 会帮你生成正确的 URL。
            # 例如这里reverse返回 "/polls/question.id/results/"
            # 如果用户点击“后退”按钮，这可以防止数据被重复post。
            return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
```

当有人对 Question 进行投票后， vote() 视图将请求重定向到 Question 的结果界面。因此要重新编写 results() 视图函数，以便它使用 render() 来显示结果页面，而不是直接返回一个 HttpResponse 对象。

```python
def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})
```

创建对应的results.html模板文件

```html 
    <h1>{{ question.question_text }}</h1>

    <ul>
    {% for choice in question.choice_set.all %}
        <li>{{ choice.choice_text }} -- {{ choice.votes }} vote{{ choice.votes|pluralize }}</li>
    {% endfor %}
    </ul>

    <a href="{% url 'polls:detail' question.id %}">Vote again?</a>
```

### 通用视图，减少冗余代码

detail() 和 results() 视图函数都使用了相同的代码来获取 Question 对象并处理 404 错误。index()函数也有类似性。因此不同视图函数中存在重复的代码

Django 提供了通用视图（generic views）来帮助减少这种冗余代码 (from django.views import generic)。

通用视图常用于解决基本的网络开发中的一个常见情况：根据 URL 中的参数从数据库中获取数据、载入模板文件然后返回渲染后的模板。

例如，ListView 和 DetailView 通用视图分别抽象了 "显示对象列表" 和 "显示特定类型对象的详细页面" 的概念。

将投票应用转换成使用通用视图系统，这样可以删除许多我们的代码。仅仅需要做以下几步来完成转换：

1. 转换 URLconf。

2. 删除一些旧的、不再需要的视图。

3. 基于 Django 的通用视图引入新的视图。

- 首先，编辑 polls/urls.py 文件，修改 URL 模式以使用通用视图而不是自定义视图函数。

    ```python
    from django.urls import path

    from . import views

    app_name = "polls"
    urlpatterns = [
        path("", views.IndexView.as_view(), name="index"),
        path("<int:pk>/", views.DetailView.as_view(), name="detail"),
        path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
        path("<int:question_id>/vote/", views.vote, name="vote"),
    ]
    ```

    第二和第三个模式的路径字符串中匹配的模式名称已从 <question_id> 更改为 <pk>。这是因为将使用 DetailView 通用视图来替换我们的 detail() 和 results() 视图，它**期望从 URL 中捕获的主键值被称为 "pk"**。

- 接下来，编辑 polls/views.py 文件，删除 index()、detail() 和 results() 视图函数，并添加基于通用视图的新视图类。

    ```python
    from django.db.models import F
    from django.http import HttpResponseRedirect
    from django.shortcuts import get_object_or_404, render
    from django.urls import reverse
    from django.views import generic

    from .models import Choice, Question


    class IndexView(generic.ListView):
        template_name = "polls/index.html"
        context_object_name = "latest_question_list"

        def get_queryset(self):
            """Return the last five published questions."""
            return Question.objects.order_by("-pub_date")[:5]


    class DetailView(generic.DetailView):
        model = Question
        template_name = "polls/detail.html"


    class ResultsView(generic.DetailView):
        model = Question
        template_name = "polls/results.html"


    def vote(request, question_id):
        # 不变.
    ...
    ```

每个通用视图都需要知道它将要操作的模型。可以**使用 model 属性来**提供这个信息（在这个示例中，对于 DetailView 和 ResultsView，是 model = Question），或者**通过定义 get_queryset() 方法**来实现（如 IndexView 中所示）。

默认情况下，通用视图 DetailView 使用一个叫做 <app name>/<model name>_detail.html 的模板。 也可以通过 template_name 属性来指定自定义模板名称。

类似地，ListView 使用一个叫做 <app name>/<model name>_list.html 的默认模板；这里使用 template_name 来告诉 ListView 使用创建的已经存在的 "polls/index.html" 模板。

Django的通用视图会根据传入的模型自动生成一个上下文变量，默认是模型的小写名称（如传入Question模型，命名为question），并将变量自动传给template。 （对于ListView，默认的上下文变量名称是 小写名称_list）

也可以通过 context_object_name 属性来指定自定义的上下文变量名称（如 IndexView 中所示，将其设置为 "latest_question_list"）。

    *这里的上下文变量指的是 context变量，作为view和template之间的桥梁，传递数据，一般是字典。*