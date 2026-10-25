from django.shortcuts import render

# Create your views here.
# Every function here is responsible for 1 html page. These functions open said page.
def autorizacija(request):
    return render(request, 'testsite/autorizacija.html')

def registracija(request):
    return render(request, 'testsite/registracija.html')

def sakumlapa(request):
    return render(request, 'testsite/sakumlapa.html')

def meklesana(request):
    return render(request, 'testsite/meklesana.html')

def profils(request):
    return render(request, 'testsite/profils.html')

def profils_fotogr(request):
    return render(request, 'testsite/profils_fotogr.html')

def profils_fotogr_klienta(request):
    return render(request, 'testsite/profils_fotogr_klienta.html')

def profila_regid(request):
    return render(request, 'testsite/profila_regid.html')

def portfolio_regid(request):
    return render(request, 'testsite/portfolio_regid.html')

def terzetava(request):
    return render(request, 'testsite/terzetava.html')