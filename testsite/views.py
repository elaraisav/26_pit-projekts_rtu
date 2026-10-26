from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from chat.models import Conversation, can_chat, chat_partners_for, chat_users

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
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        # Create the user only if both are new. The visitor sees the same page
        # in both cases and is not logged in; logging in stands in for verification.
        if not (User.objects.filter(username__iexact=username).exists()
                or User.objects.filter(email__iexact=email).exists()):
            form.save()
        return redirect('testsite:registracija_nosutita')

    return render(request, 'testsite/registracija.html', {'form': form})

def registracija_nosutita(request):
    return render(request, 'testsite/registracija_nosutita.html')

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

# Chat page (design: terzetava.html). With no id it opens the newest conversation.
# Who may chat is decided in chat/models.py (can_chat); admin accounts only see a note.
@login_required
def terzetava(request, conversation_id=None):
    user = request.user
    allowed = can_chat(user)
    # Evaluated once and reused for the sidebar, the active conversation and talked_to.
    conversations = (list(Conversation.objects.for_user(user).usable().select_related('client', 'photographer'))
                     if allowed else [])

    if conversation_id is not None:
        active = next((conversation for conversation in conversations if conversation.pk == conversation_id), None)
        if active is None:
            raise Http404
    else:
        active = conversations[0] if conversations else None

    # People of the other role you don't have a conversation with yet,
    # for the "start a new conversation" list.
    new_contacts = []
    if allowed:
        talked_to = {conversation.other_participant(user).pk for conversation in conversations}
        new_contacts = chat_partners_for(user).exclude(pk__in=talked_to).order_by('first_name', 'last_name', 'username')

    history = []
    if active is not None:
        history = [message.to_json() for message in active.messages.select_related('sender')]

    return render(request, 'testsite/terzetava.html', {
        'chat_allowed': allowed,
        'conversations': [(conversation, conversation.other_participant(user)) for conversation in conversations],
        'active': active,
        'active_other': active.other_participant(user) if active else None,
        'history': history,
        'new_contacts': new_contacts,
    })

# Messages newer than ?after=<id>, as JSON. chat.js calls this whenever its WebSocket
# (re)connects, so messages sent while the page was loading or offline still show up.
@login_required
def chat_messages(request, conversation_id):
    conversation = Conversation.objects.for_user(request.user).usable().filter(pk=conversation_id).first()
    if conversation is None or not can_chat(request.user):
        raise Http404
    after = request.GET.get('after', '0')
    after = int(after) if after.isdigit() else 0
    messages_after = conversation.messages.filter(pk__gt=after).select_related('sender').order_by('pk')
    return JsonResponse({'messages': [message.to_json() for message in messages_after]})

@login_required
@require_POST
def chat_start(request):
    user_id = request.POST.get('user_id', '')
    if not user_id.isdigit():
        raise Http404
    # Only people who may chat can be picked; anyone else (e.g. admin) is "not found".
    other = get_object_or_404(chat_users(), pk=int(user_id))
    try:
        conversation = Conversation.get_or_create_between(request.user, other)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    return redirect('testsite:chat_conversation', conversation_id=conversation.pk)

@login_required
def report_submission(request):
    return render(request, 'testsite/report_submission.html')

def admin_panel(request):
    return render(request, 'testsite/admin_panel.html')
