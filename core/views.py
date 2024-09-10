from django.shortcuts import get_object_or_404, redirect
from django.views.generic import *
from django.urls import *
from .models import *
from .forms import *
import random
from django.http import HttpResponseRedirect, JsonResponse
import unicodedata
from .mixins import ProfessorContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

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
        palavras = list(tema.palavras.all())  # Converter para lista

        palavra_escolhida_id = self.request.session.get('palavra_escolhida')

        if not palavra_escolhida_id:
            if palavras:
                random.shuffle(palavras)  # Embaralhar a lista
                palavra_escolhida = palavras[0]  # Selecionar a primeira palavra
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



class RelatorioAtividadeView(LoginRequiredMixin, ListView):
    template_name = 'professor/relatorioAtividade.html'
    context_object_name = 'atividades'
    model = Atividade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['temas'] = Tema.objects.filter(professor=self.request.user)
        atividades = self.get_queryset()
        context['atividades_vazias'] = not atividades.exists()
        return context

    def get_queryset(self):
        tema_id = self.request.GET.get('tema')
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')

        queryset = Atividade.objects.filter(tema__professor=self.request.user)

        if tema_id:
            queryset = queryset.filter(tema_id=tema_id)
        if data_inicio and data_fim:
            queryset = queryset.filter(data__range=[data_inicio, data_fim])
        
        # Ordenar por nome de usuário em ordem alfabética
        queryset = queryset.order_by('aluno__username')

        return queryset

    def get(self, request, *args, **kwargs):
        if 'exportar_pdf' in request.GET:
            return self.exportar_pdf()
        return super().get(request, *args, **kwargs)

    def exportar_pdf(self):
        atividades = self.get_queryset()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        content = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=18,
            alignment=1,
            spaceAfter=20
        )
        subtitle_style = ParagraphStyle(
            name='SubtitleStyle',
            fontName='Helvetica',
            fontSize=14,
            alignment=1,
            spaceAfter=10
        )
        normal_style = ParagraphStyle(
            name='NormalStyle',
            fontName='Helvetica',
            fontSize=10,
            alignment=0,
            spaceAfter=10
        )
        
        # Adiciona o título
        title = Paragraph("Relatório de Atividades", title_style)
        content.append(title)

        if not atividades.exists():
            no_data = Paragraph("Nenhuma atividade registrada.", normal_style)
            content.append(no_data)
        else:
            content.append(Paragraph("<br/><br/>", normal_style))
            
            # Adiciona o cabeçalho da tabela
            data = [['Aluno', 'Tema', 'Data', 'Resultado']]
            
            for atividade in atividades:
                data.append([
                    atividade.aluno.username,
                    atividade.tema.nome,
                    atividade.data.strftime('%d/%m/%Y'),
                    atividade.resultado
                ])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#0044cc'),
                ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 1), (-1, -1), '#f4f4f4'),
                ('GRID', (0, 0), (-1, -1), 0.5, '#dddddd'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#fafafa'),
            ]))
            
            content.append(table)

        doc.build(content)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')
