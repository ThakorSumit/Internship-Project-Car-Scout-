from django.shortcuts import render,redirect
from .forms import UserSignupForm,UserLoginForm
from django.contrib.auth import authenticate,login,logout
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

# Create your views here.

def UserSignupView(request):
    if request.method=='POST':
        form=UserSignupForm(request.POST or None)
        if form.is_valid():
            send_mail(
                subject='Welcome to CarScout',
                message=render_to_string('welcome.html',{'user':form.cleaned_data['email']}),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[form.cleaned_data['email']],
                fail_silently=False,
            )        
            form.save()
            return redirect('login')
        else:
            print(form.errors)
            return render(request,'core/signup.html',{'form':form})
    else:
        form=UserSignupForm()
    return render(request,'core/signup.html',{'form':form})


def UserLoginView(request):
        if request.method=='POST':
            form=UserLoginForm(request.POST or None)
            if form.is_valid():
                email=form.cleaned_data['email']
                password=form.cleaned_data['password']
                user=authenticate(request,email=email,password=password)
                if user:
                    login(request,user)
                    if user.role=='Admin':
                        return redirect('admin_dashboard')
                    elif user.role=='Seller':
                        return redirect('seller_dashboard')
                    elif user.role=='Buyer':
                        return redirect('buyer_dashboard')
                else:
                    return render(request,'core/login.html',{'form':form})
        else:
            form=UserLoginForm()
        return render(request,'core/login.html',{'form':form})


def user_logout(request):
    logout(request)
    return redirect('login')


def home(request):
    return render(request,'home.html')
