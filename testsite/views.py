from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegistrationForm

# Create your views here.
# Every function here is responsible for 1 html page. These functions open said page.
# Pages with @login_required send a visitor who is not logged in to autorizacija.
def autorizacija(request):
    if request.user.is_authenticated:
        return redirect('testsite:sakumlapa')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        # After login go back to the page that asked for it (?next=...), if it is ours.
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                        require_https=request.is_secure()):
            return redirect(next_url)
        return redirect('testsite:sakumlapa')

    return render(request, 'testsite/autorizacija.html', {'form': form, 'next': request.GET.get('next', '')})

def registracija(request):
    if request.user.is_authenticated:
        return redirect('testsite:sakumlapa')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Reģistrācija veiksmīga!')
        return redirect('testsite:sakumlapa')

    return render(request, 'testsite/registracija.html', {'form': form})

@require_POST
def logout_view(request):
    logout(request)
    return redirect('testsite:autorizacija')

@login_required
def sakumlapa(request):
    return render(request, 'testsite/sakumlapa.html')

@login_required
def meklesana(request):
    return render(request, 'testsite/meklesana.html')

@login_required
def profils(request):
    return render(request, 'testsite/profils.html')

@login_required
def profils_fotogr(request):
    return render(request, 'testsite/profils_fotogr.html')

@login_required
def profils_fotogr_klienta(request):
    return render(request, 'testsite/profils_fotogr_klienta.html')

@login_required
def profila_regid(request):
    return render(request, 'testsite/profila_regid.html')

@login_required
def portfolio_regid(request):
    return render(request, 'testsite/portfolio_regid.html')
