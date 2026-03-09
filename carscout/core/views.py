from django.shortcuts import render,redirect
from .forms import UserSignupForm,UserLoginForm
from django.contrib.auth import authenticate,login,logout
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from scout.models import Listing
import os

# Create your views here.

def UserSignupView(request):
    if request.method=='POST':
        form=UserSignupForm(request.POST or None)
        if form.is_valid():
            html_content=render_to_string('welcome.html',{'user':form.cleaned_data['email']})
            email=EmailMessage(
                subject='Welcome to CarScout',
                body=html_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[form.cleaned_data['email']],
            )   
            email.content_subtype='html'
            pdf_path=os.path.join(settings.BASE_DIR,'templates','Car Scout - Welcome Guide.pdf')     
            with open(pdf_path,'rb') as f:
                email.attach('Car Scout - Welcome Guide.pdf',f.read(),'application/pdf')
            email.send(fail_silently=False)
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
                    if user.role=='Admin' or user.is_admin:
                        return redirect('admin_dashboard')
                    elif user.role=='Seller':
                        return redirect('seller_dashboard')
                    elif user.role=='Buyer':
                        return redirect('buyer_dashboard')
                else:
                    form.add_error(None, 'Invalid email or password')
                    return render(request,'core/login.html',{'form':form})
        else:
            form=UserLoginForm()
        return render(request,'core/login.html',{'form':form})


def user_logout(request):
    logout(request)
    return redirect('login')

def home(request):
    listings = Listing.objects.filter(
        status='live',
        seller__isnull=False       # ← only listings with a valid seller
    ).select_related('vehicle', 'seller').order_by('-id')  # ← efficient DB query
    return render(request, 'home.html', {'listings': listings})


