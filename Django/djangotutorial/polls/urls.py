from django.urls import path
from . import views

app_name = 'polls'  # 告诉Django这个urls.py文件属于哪个应用, 也方便html模板中使用
urlpatterns = [
    # example: /polls/
    path('', views.index, name='index'), # 格式： path('url路径', 视图函数, name='路由名称')
# 带参数的路由的格式： path('url路径/<参数类型:参数名>/', 视图函数, name='路由名称')
# 尖括号用来 获得 参数，并将其作为关键字参数传递给视图函数。
    path('<int:question_id>/', views.detail, name='detail'),
    path('<int:question_id>/results/', views.results, name='results'),
    # example: /polls/5/vote/
    path('<int:question_id>/vote/', views.vote, name='vote'),
]