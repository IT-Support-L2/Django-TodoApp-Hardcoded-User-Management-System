from django.db.models.query_utils import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from .forms import TodoForm
from django.core.mail import BadHeaderError
from django.http import HttpResponse
from .models import Todo
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from .forms import SignUpForm
from django.contrib.auth.tokens import default_token_generator

def home(request):
    return render(request, 'todo/home.html')

def signupuser(request):
    if request.method  == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user.refresh_from_db()
                user.profile.username = form.cleaned_data.get('username')
                user.profile.email = form.cleaned_data.get('email')
                user.is_active = False
                user.save()
                current_site = get_current_site(request)
                subject = 'Please Activate Your Account'
                body = render_to_string('todo/activation_request.txt', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                email = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [user.profile.email])
                email.fail_silently = False
                email.send()
                return redirect('activation_sent')
            except IntegrityError:
                return render(request, 'todo/signupuser.html', {'form':SignUpForm(), 'error':'That username has already been taken. Please choose a new username'})
        else:
            return render(request, 'todo/signupuser.html', {'form':SignUpForm(), 'error':'Passwords did not match'})
    else:
        form = SignUpForm()
    return render(request, 'todo/signupuser.html', {'form': form})
            
        
def activation_sent_view(request):
    return render(request, 'todo/activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.profile.signup_confirmation = True
        user.save()
        login(request, user)
        return redirect('currenttodos')
    else:
        return render(request, 'todo/activation_invalid.html')
        
def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = PasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():
				for user in associated_users:
					site = get_current_site(request)
					subject = 'Password reset request'
					body = render_to_string('todo/password_reset_email.txt', {
					'user': user,
					'domain': site.domain,
					'uid': urlsafe_base64_encode(force_bytes(user.pk)),
					'token': default_token_generator.make_token(user),
									})
					email = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [user.email])
					email.fail_silently = False
					
					try:
						email.send()
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
					return redirect("password_reset_done")
			else:
			    return redirect('password_reset_failed')
		else:
			return redirect('password_reset_failed')
	password_reset_form = PasswordResetForm()
	return render(request=request, template_name="todo/password_reset.html", context={"password_reset_form":password_reset_form})

def password_reset_failed(request):
    return render(request, 'todo/password_reset_failed.html')

def loginuser(request):
    if request.method == 'GET':
        return render(request, 'todo/loginuser.html', {'form':AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'todo/loginuser.html', {'form':AuthenticationForm(), 'error':'Username and password did not match'})
        else:
            login(request, user)
            return redirect('currenttodos')

@login_required
def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')

@login_required
def createtodo(request):
    if request.method == 'GET':
        return render(request, 'todo/createtodo.html', {'form':TodoForm()})
    else:
        try:
            form = TodoForm(request.POST)
            newtodo = form.save(commit=False)
            newtodo.user = request.user
            newtodo.save()
            return redirect('currenttodos')
        except ValueError:
            return render(request, 'todo/createtodo.html', {'form':TodoForm(), 'error':'Bad data passed in. Try again.'})

@login_required
def view_profile(request, pk=None):
    if pk:
        user = User.objects.get(pk=pk)
    else:
        user = request.user
    args = {'user': user}
    return render(request, 'todo/profile.html', args)

@login_required
def currenttodos(request):
    todos = Todo.objects.filter(user=request.user, datecompleted__isnull=True)
    return render(request, 'todo/currenttodos.html', {'todos':todos})

@login_required
def completedtodos(request):
    todos = Todo.objects.filter(user=request.user, datecompleted__isnull=False).order_by('-datecompleted')
    return render(request, 'todo/completedtodos.html', {'todos':todos})

@login_required
def viewtodo(request, todo_pk):
    todo = get_object_or_404(Todo, pk=todo_pk, user=request.user)
    if request.method == 'GET':
        form = TodoForm(instance=todo)
        return render(request, 'todo/viewtodo.html', {'todo':todo, 'form':form})
    else:
        try:
            form = TodoForm(request.POST, instance=todo)
            form.save()
            return redirect('currenttodos')
        except ValueError:
            return render(request, 'todo/viewtodo.html', {'todo':todo, 'form':form, 'error':'Bad info'})

@login_required
def completetodo(request, todo_pk):
    todo = get_object_or_404(Todo, pk=todo_pk, user=request.user)
    if request.method == 'POST':
        todo.datecompleted = timezone.now()
        todo.save()
        return redirect('currenttodos')

@login_required
def deletetodo(request, todo_pk):
    todo = get_object_or_404(Todo, pk=todo_pk, user=request.user)
    if request.method == 'POST':
        todo.delete()
        return redirect('currenttodos')
