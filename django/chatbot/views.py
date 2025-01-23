# SYSTEM
import os

# DJANGO
from django.contrib import auth
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import Chat

# LLM
from openai import OpenAI
import openai

# OTHER
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")  # Print the value of
print(f"GROQ_API_KEY: {GROQ_API_KEY}")

LLM = "GROQ"

if LLM == "GROQ":
    client = openai.OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )
    MODEL = "llama-3.3-70b-versatile"

if LLM == "OPENAI":
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL = "gpt-3.5-turbo"

# Print the value of


def ask_openai(message):
    response = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model=MODEL,
        # prompt = message,
        # max_tokens=150,
        # n=1,
        # stop=None,
        # temperature=0.7,
        messages=[
            {"role": "system", "content": "You are an helpful assistant."},
            {"role": "user", "content": message},
        ],
    )
    answer = response.choices[0].message.content.strip()
    return answer


# Create your views here.
def index(request):
    return render(request, "home.html")


def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == "POST":
        message = request.POST.get("message")
        response = ask_openai(message)

        chat = Chat(
            user=request.user,
            message=message,
            response=response,
            created_at=timezone.now,
        )
        chat.save()
        return JsonResponse({"message": message, "response": response})
    return render(request, "chatbot.html", {"chats": chats})


def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("chatbot")
        else:
            error_message = "Invalid username or password"
            return render(request, "login.html", {"error_message": error_message})
    else:
        return render(request, "login.html")


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect("chatbot")
            except:
                error_message = "Error creating account"
            return render(request, "register.html", {"error_message": error_message})
        else:
            error_message = "Password don't match"
            return render(request, "register.html", {"error_message": error_message})
    return render(request, "register.html")


def logout(request):
    auth.logout(request)
    return redirect("login")
