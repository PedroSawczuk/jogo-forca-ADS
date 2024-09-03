from django.shortcuts import render
from django.views.generic import *
from django.urls import reverse_lazy
from .models import *
from .forms import *

class HomePageView(TemplateView):
    template_name = "homePage.html"


    # função para verificar se o usuário é professor
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context

class DesenvolvedoresPageView(TemplateView):
    template_name = "desenvolvedoresPage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context

class ProfessorGeralPageView(TemplateView):
    template_name = "professor/paginaGeral.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context

class AdministrarTemasPageView(CreateView, ListView):
    model = Tema
    form_class = TemaForm
    template_name = 'professor/temasPage.html'
    success_url = reverse_lazy('administrarTemasPage')

    def get_queryset(self):
        return Tema.objects.filter(professor=self.request.user)

    def form_valid(self, form):
        form.instance.professor = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context

class EditarTemaPageView(UpdateView):
    model = Tema
    form_class = TemaForm
    template_name = 'professor/editarTemas.html'
    success_url = reverse_lazy('administrarTemasPage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context

class DeletarTemaPageView(DeleteView):
    model = Tema
    template_name = 'professor/confirmarExcluirTemas.html'
    success_url = reverse_lazy('administrarTemasPage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_professor'] = user.is_authenticated and user.groups.filter(name='professores').exists()

        return context