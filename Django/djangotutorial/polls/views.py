from django.shortcuts import render

from django.http import HttpResponse
from .models import Question
# 用于导入html模板
from django.template import loader

# 按照日期降序获取最近的5个问题
def index (request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    '''
    下面这是一种方法，显示导入tenplate，loader模块后的用法
    然后return的时候用HTTPResponse来使得返回的内容是HTTPResponse对象（Django硬性要求）
    '''
    # template = loader.get_template('polls/index.html')
    # context = {"latest_question_list": latest_question_list}
    # return HttpResponse(template.render(context,request)) # Django要求输出是一个HttpResponse对象。
    '''
    另一种简洁的方法是用Django提供的render()快捷函数
    它会自动加载模板，填充上下文，并返回一个HttpResponse对象
    '''
    context = {"latest_question_list": latest_question_list}
    return render(request, "polls/index.html", context)

# 这是Django的一个视图函数示例。
# 为了能够成功访问这个视图，你需要在项目的polls/urls.py文件中配置相应的URL路由。
# 另外，还需要在mysite/urls.py文件中包含polls应用的URL配置。


from django.http import Http404
# 接下去，再创建几个视图（或者叫做函数），他们接受参数
def detail(request,question_id):
    '''
    完整的常见流程是，Django试图得到一个对象，如果找不到就抛出404错误
    这里的Question.objects.get(pk=question_id)是Django的ORM查询语句
    它试图从数据库中获取主键为question_id的Question对象
    '''
    # try:
    #     question = Question.objects.get(pk=question_id)
    # except Question.DoesNotExist:
    #     raise Http404("Question does not exist")
    # return render(request, "polls/detail.html", {"question": question})

    '''
    类似的，有一个简介的写法，使用Django提供的get_object_or_404快捷函数
    '''
    from django.shortcuts import get_object_or_404
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": question})

def results(request, question_id):
    from django.shortcuts import get_object_or_404
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})

def vote(request, question_id):

    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from django.shortcuts import get_object_or_404
    from .models import Choice, Question

    question = get_object_or_404(Question, pk=question_id)
    try:
        # request.POST['choice'] 以字符串形式返回选择的 Choice 的 ID
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
        # 如果在 request.POST['choice'] 数据中没有提供 choice ， POST 将引发一个 KeyError 
    except (KeyError, Choice.DoesNotExist):
        # 代码检查 KeyError ，如果没有给出 choice 将重新显示 Question 表单和一个错误信息。
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        from django.db.models import F

        selected_choice.votes = F("votes") + 1 # 指示数据库 将投票数增加 1。
        selected_choice.save()

        # 成功处理 POST 数据后，总是返回一个 HttpResponseRedirect 对象。
        # 这样可以防止用户点击“后退”按钮时浏览器会重新提交表单数据。
        # reverse() 函数避免了我们在视图函数中硬编码 URL
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
        #reverse() 调用将返回一个这样的字符串： '/polls/3/results/' ，

# 创建完视图后，要在url里加入对应的路由