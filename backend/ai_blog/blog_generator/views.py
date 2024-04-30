
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import os
from pytube import YouTube
import assemblyai as aai
import openai

def yt_title(link):
  yt = YouTube(link)
  title = yt.title
  return title  
# Create your views here.
@login_required
def index(request):
  return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
  if request.method == "POST":
    try:
      data = json.loads(request.body)
      yt_link = data['link']
      print(yt_link)
      # return JsonResponse({'content': yt_link})
    except (KeyError, json.JSONDecodeError):
      return JsonResponse({'error': 'Invalid'}, status = 400)
    
      # Get title
    title = yt_title(yt_link)
    print(title)   
  
      # Get transcript
    transciption = get_transcription(yt_link)
    print(f"Start transcript...")
    if not transciption:
      return JsonResponse({'error': "Failure getting YouTube link"}, status = 500)
   
      # Use AI to generate blog
    blog_content = generate_blog_from_transcription(transciption)
  
    if not blog_content:
      return JsonResponse({'error': "Failed to generate blog article"}, status = 500)
      # Save blog to database

      # Return blog as response
    return JsonResponse({'content': blog_content})
  else:
    return JsonResponse({'error': 'Invalid'}, status = 405)
  

def download_audio(link):
  yt =YouTube(link)
  video = yt.streams.filter(only_audio=True).first()
  out_file = video.download(output_path=settings.MEDIA_ROOT)
  base, ext = os.path.splitext(out_file)
  new_file = base + '.mp3'
  os.rename(out_file, new_file)
  return new_file

def get_transcription(link):
  audio_file = download_audio(link)
  aai.settings.api_key = ""
  transcriber = aai.Transcriber()

  transcript = transcriber.transcribe(audio_file)
  return transcript.text

def generate_blog_from_transcription(transcription):
  openai.api_key = ""

  prompt = f"Based on the following video transcript turn it into an Engaging Blog. Craft compelling content from YouTube conversations:\n\n{transcription}\n\nArticle:"
  response =openai.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt= prompt,
    max_tokens=1000
  )

  generated_content = response.choices[0].text.strip()
  return generated_content

def user_login(request):
  if request.method == "POST":
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username = username, password = password)
    if user is not None:
      login(request, user)
      return redirect('/')
    else:
      error_message = 'Invalid credentials'
      return render(request, 'login.html', {'error_message': error_message})
  return render(request, 'login.html')

def user_signup(request):
  if request.method == "POST":
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    confirmPassword = request.POST['confirmPassword']

    if password == confirmPassword:
      try:
        user = User.objects.create_user(username, email, password)
        user.save()
        login(request, user)
        return redirect('/')
      except:
        error_message = 'Error creating new user'
        return render(request, 'signup.html', {'error_message': error_message})
    else:
      error_message = 'Passwords do not match'
      return render(request, 'signup.html', {'error_message': error_message})
  return render(request, 'signup.html')

def user_logout(request):
  logout(request)
  return redirect('/')
  
 