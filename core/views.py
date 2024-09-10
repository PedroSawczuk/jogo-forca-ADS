from django.shortcuts import get_object_or_404, redirect
from django.views.generic import *
from django.urls import *
from .models import *
from .forms import *
import random
from django.http import HttpResponseRedirect, JsonResponse
import unicodedata
from .mixins import ProfessorContextMixin

class HomePageView(ProfessorContextMixin, TemplateView):
    template_name = "homePage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['temas'] = Tema.objects.all()
        return context

class TemaDetalhesView(ProfessorContextMixin, DetailView):
    model = Tema
    template_name = 'temaDetalhe.html'
    context_object_name = 'tema'

class DesenvolvedoresPageView(ProfessorContextMixin, TemplateView):
    template_name = "desenvolvedoresPage.html"

class ProfessorGeralPageView(ProfessorContextMixin, TemplateView):
    template_name = "professor/paginaGeral.html"

class AdministrarTemasPageView(ProfessorContextMixin, CreateView, ListView):
    model = Tema
    form_class = TemaForm
    template_name = 'professor/temas/temasPage.html'
    success_url = reverse_lazy('administrarTemasPage')

    def get_queryset(self):
        return Tema.objects.filter(professor=self.request.user)

    def form_valid(self, form):
        form.instance.professor = self.request.user
        return super().form_valid(form)

class EditarTemaPageView(ProfessorContextMixin, UpdateView):
    model = Tema
    form_class = TemaForm
    template_name = 'professor/temas/editarTemas.html'
    success_url = reverse_lazy('administrarTemasPage')

class DeletarTemaPageView(ProfessorContextMixin, DeleteView):
    model = Tema
    template_name = 'professor/temas/confirmarExcluirTemas.html'
    success_url = reverse_lazy('administrarTemasPage')

class AdministrarPalavrasPageView(ProfessorContextMixin, CreateView, ListView):
    model = Palavra
    form_class = PalavraForm
    template_name = 'professor/palavras/palavrasPage.html'
    success_url = reverse_lazy('administrarPalavrasPage')

    def get_queryset(self):
        return Palavra.objects.filter(tema__professor=self.request.user)

    def form_valid(self, form):
        form.instance.tema = get_object_or_404(Tema, pk=self.request.POST.get('tema'))
        return super().form_valid(form)

class EditarPalavraPageView(ProfessorContextMixin, UpdateView):
    model = Palavra
    form_class = PalavraForm
    template_name = 'professor/palavras/editarPalavras.html'
    success_url = reverse_lazy('administrarPalavrasPage')

class DeletarPalavraPageView(ProfessorContextMixin, DeleteView):
    model = Palavra
    template_name = 'professor/palavras/confirmarExcluirPalavras.html'
    success_url = reverse_lazy('administrarPalavrasPage')

def normalize_accented_char(char):
    normalized_char = unicodedata.normalize('NFD', char)
    return ''.join(c for c in normalized_char if unicodedata.category(c) != 'Mn')

class ForcaGameView(ProfessorContextMixin, TemplateView):
    template_name = 'jogo/forcaPage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tema = get_object_or_404(Tema, pk=self.kwargs['pk'])
        palavras = tema.palavras.all()
        palavra_escolhida_id = self.request.session.get('palavra_escolhida')

        if not palavra_escolhida_id:
            palavra_escolhida = random.choice(palavras) if palavras.exists() else None
            if palavra_escolhida:
                self.request.session['palavra_escolhida'] = palavra_escolhida.id
                self.request.session['erros'] = 0  # Inicializa o contador de erros
            else:
                palavra_escolhida = None
        else:
            palavra_escolhida = Palavra.objects.get(id=palavra_escolhida_id)

        if palavra_escolhida:
            palavra = palavra_escolhida.palavra.lower()
            palavra_mascarada = ''.join(['_' if char != ' ' else ' ' for char in palavra])
            self.request.session['palavra_mascarada'] = palavra_mascarada

        erros = self.request.session.get('erros', 0)
        limite_erros = 6
        tentativas_restantes = limite_erros - erros

        context['tema'] = tema
        context['palavra'] = palavra_escolhida
        context['palavra_mascarada'] = palavra_mascarada if palavra_escolhida else ''
        context['tentativas_restantes'] = tentativas_restantes
        return context

    def post(self, request, *args, **kwargs):
        letra = request.POST.get('letra').lower()
        palavra_escolhida_id = request.session.get('palavra_escolhida')

        if palavra_escolhida_id:
            palavra_escolhida = Palavra.objects.get(id=palavra_escolhida_id)
            palavra = palavra_escolhida.palavra.lower()

            palavra_mascarada = self.request.session.get('palavra_mascarada', ''.join(['_' if char != ' ' else ' ' for char in palavra]))
            nova_palavra_mascarada = list(palavra_mascarada)
            mensagem = ""

            erros = self.request.session.get('erros', 0)

            # Normaliza a letra inserida e a palavra
            letra_normalizada = normalize_accented_char(letra)
            palavra_normalizada = normalize_accented_char(palavra)

            if letra_normalizada in palavra_normalizada:
                for idx, char in enumerate(palavra):
                    if normalize_accented_char(char) == letra_normalizada:
                        nova_palavra_mascarada[idx] = char
                palavra_mascarada = ''.join(nova_palavra_mascarada)
                self.request.session['palavra_mascarada'] = palavra_mascarada
                mensagem = "Letra correta!"
            else:
                erros += 1
                self.request.session['erros'] = erros
                mensagem = "Letra incorreta!"

            tentativas_restantes = 6 - erros

            # Verificar se a palavra foi completada ou se as tentativas acabaram
            if '_' not in palavra_mascarada:
                del self.request.session['palavra_escolhida']
                del self.request.session['erros']
                
                # Registro de atividade com resultado de vitória
                Atividade.objects.create(
                    aluno=self.request.user,
                    tema=palavra_escolhida.tema,
                    resultado='vitoria'
                )

                return JsonResponse({
                    'palavra_mascarada': palavra_mascarada,
                    'tentativas_restantes': tentativas_restantes,
                    'mensagem': 'Você ganhou! Redirecionando para a página de vitória.',
                    'redirect': True,
                    'url': self.request.build_absolute_uri(reverse('winPage'))
                })

            if tentativas_restantes <= 0:
                del self.request.session['palavra_escolhida']
                del self.request.session['erros']
                
                # Registro de atividade com resultado de derrota
                Atividade.objects.create(
                    aluno=self.request.user,
                    tema=palavra_escolhida.tema,
                    resultado='derrota'
                )

                return JsonResponse({
                    'palavra_mascarada': palavra_mascarada,
                    'tentativas_restantes': tentativas_restantes,
                    'mensagem': 'Você perdeu! Redirecionando para a página de derrota.',
                    'redirect': True,
                    'url': self.request.build_absolute_uri(reverse('losePage'))
                })

            return JsonResponse({
                'palavra_mascarada': palavra_mascarada,
                'mensagem': mensagem,
                'tentativas_restantes': tentativas_restantes,
                'redirect': False
            })

        return JsonResponse({'mensagem': 'Erro: Nenhuma palavra selecionada.'}, status=400)


class WinPageView(ProfessorContextMixin, TemplateView):
    template_name = 'jogo/winPage.html'

class LosePageView(ProfessorContextMixin, TemplateView):
    template_name = 'jogo/losePage.html'

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Atividade, Tema

class RelatorioAtividadeView(LoginRequiredMixin, ProfessorContextMixin, ListView):
    template_name = 'professor/relatorioAtividade.html'
    context_object_name = 'atividades'
    model = Atividade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['temas'] = Tema.objects.all()
        atividades = self.get_queryset()
        context['atividades_vazias'] = not atividades.exists()
        return context

    def get_queryset(self):
        tema_id = self.request.GET.get('tema')
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        
        queryset = Atividade.objects.all()
        
        if tema_id:
            queryset = queryset.filter(tema_id=tema_id)
        if data_inicio and data_fim:
            queryset = queryset.filter(data__range=[data_inicio, data_fim])
        
        return queryset

    def get(self, request, *args, **kwargs):
        if 'exportar_pdf' in request.GET:
            return self.exportar_pdf()
        return super().get(request, *args, **kwargs)

    def exportar_pdf(self):
        atividades = self.get_queryset()
        if not atividades.exists():
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            p.drawString(100, height - 100, "Relatório de Atividades")
            p.drawString(100, height - 120, "Nenhuma atividade encontrada.")

            p.showPage()
            p.save()
            buffer.seek(0)
            return HttpResponse(buffer, content_type='application/pdf')

        # Se há atividades, gera o relatório normalmente
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.drawString(100, height - 100, "Relatório de Atividades")
        y = height - 120
        for atividade in atividades:
            p.drawString(100, y, f"Aluno: {atividade.aluno.username}, Tema: {atividade.tema.nome}, Data: {atividade.data}, Resultado: {atividade.resultado}")
            y -= 20

        p.showPage()
        p.save()
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')
