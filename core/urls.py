from django.urls import *
from .views import *

urlpatterns = [
    path("", HomePageView.as_view(), name="homePage"),
    path("desenvolvedores", DesenvolvedoresPageView.as_view(), name="desenvolvedoresPage"),
    path("professor/pagina-geral", ProfessorGeralPageView.as_view(), name="professorGeralPage"),
    path("professor/administrar-temas", AdministrarTemasPageView.as_view(), name="administrarTemasPage"),
    path("professor/tema/<int:pk>/editar/", EditarTemaView.as_view(), name="editar_tema"),
    path("professor/tema/<int:pk>/deletar/", DeletarTemaView.as_view(), name="deletar_tema"),
]