from django.urls import *
from .views import *

urlpatterns = [
    path("", HomePageView.as_view(), name="homePage"),
    path("desenvolvedores", DesenvolvedoresPageView.as_view(), name="desenvolvedoresPage"),
    path("professor/pagina-geral", ProfessorGeralPageView.as_view(), name="professorGeralPage"),
    path("professor/administrar-temas", AdministrarTemasPageView.as_view(), name="administrarTemasPage"),
    path("professor/tema/<int:pk>/editar/", EditarTemaPageView.as_view(), name="editarTema"),
    path("professor/tema/<int:pk>/deletar/", DeletarTemaPageView.as_view(), name="deletarTema"),
]