import os
from django.contrib import auth
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from openai import OpenAI
import openai
from .models import Chat
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")  # Print the value of
print(f"GROQ_API_KEY: {GROQ_API_KEY}")  # Print the value of

openai_api_key = OPENAI_API_KEY
# client = OpenAI(api_key=openai_api_key)
client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)


def ask_groq(message):

    # original prompt
    system_message = """
    You are an assistant that is great at telling jokes.
    """

    # Here is where we can do some prompt engineering - we are adding to the system message
    prompt_engineering = """
    A joke worthy of publishing is a joke that has a rating of 8.5/10 or above.

    If the joke is worthy of publishing also include next: PUBLISH otherwise next: RETRY

    Here is an example of a joke worth of publishing:
    Supply the response in the following JSON format:
    {"setup": "The setup of the joke",
    "punchline": "The punchline of the joke",   
    "rating": "9.0",
    "next": "PUBLISH"
    }

    Remove all back ticks and other unnecessary characters and just print the JSON format and nothing else.

    Please ensure jokes are not repeated on retries

    Thank you.

    """

    system_message += prompt_engineering

    user_prompt = "Tell a light-hearted joke for an audience of Pythonistas"
    prompts = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt},
    ]
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Explain the importance of fast language models",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    answer = response.choices[0].message.content.strip()
    return answer


def ask_openai(message):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
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
