from django.shortcuts import render
from django.views.generic import *

class HomePageView(TemplateView):
    template_name = "homePage.html"

class DesenvolvedoresPageView(TemplateView):
    template_name = "desenvolvedoresPage.html"
