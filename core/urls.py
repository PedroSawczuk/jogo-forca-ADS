from django.urls import *
from .views import *

urlpatterns = [
    path("", HomePageView.as_view(), name="homePage"),
    path("desenvolvedores", DesenvolvedoresPageView.as_view(), name="desenvolvedoresPage"),
]
