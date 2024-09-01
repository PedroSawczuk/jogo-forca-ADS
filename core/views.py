from django.shortcuts import render
from django.views.generic import *

class HomePageView(TemplateView):
    template_name = "homePage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Verificar se o usuário está autenticado e pertence ao grupo "professores"
        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context

class DesenvolvedoresPageView(TemplateView):
    template_name = "desenvolvedoresPage.html"
