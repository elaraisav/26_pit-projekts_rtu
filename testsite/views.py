from django.shortcuts import render

# Create your views here.
# Every function here is responsible for 1 html page. These functions open said page.
def autorizacija(request):
    return render(request, 'testsite/autorizacija.html')

def registracija(request):
    return render(request, 'testsite/registracija.html')

def sakumlapa(request):
    return render(request, 'testsite/sakumlapa.html')

def aizmirsu_paroli(request):
    return render(request, 'testsite/aizmirsu-paroli.html')

def meklesana(request):
    return render(request, 'testsite/meklesana.html')

def profils(request):
    return render(request, 'testsite/profils.html')

def profils_fotogr(request):
    return render(request, 'testsite/profils_fotogr.html')

def profils_fotogr_klienta(request):
    return render(request, 'testsite/profils_fotogr_klienta.html')