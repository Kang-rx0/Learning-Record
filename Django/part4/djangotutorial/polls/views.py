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
        """返回最近发布的五个问卷"""
        return Question.objects.order_by("-pub_date")[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

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

