from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout  # Required for the logout function
from django.db.models import Avg
from datetime import date, timedelta
from .models import Users, PeriodLog, SymptomLog

# --- AUTHENTICATION LOGIC ---

def index(request):
    # If a user ID exists in the session, they are logged in.
    # Send them straight to the dashboard!
    if request.session.get("user_id"):
        return redirect('dashboard')
    
    return render(request, 'index.html')

def signup_view(request):
    if request.method == "POST":
        uname = request.POST.get('username')
        uemail = request.POST.get('email')
        upass = request.POST.get('password')
        uconfirm = request.POST.get('confirmPassword')

        if upass != uconfirm:
            messages.error(request, "Passwords do not match!")
            return render(request, "signup.html")

        if Users.objects.filter(Username=uname).exists():
            messages.error(request, "Username already exists!")
            return render(request, "signup.html")

        new_user = Users(
            Username=uname, 
            Password=upass,  # Note: In production use make_password(upass)
            IsActive=True
        )
        new_user.save()
        messages.success(request, "Registration successful!")
        return redirect('login')

    return render(request, "signup.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = Users.objects.get(Username=username, Password=password)
            request.session["user_id"] = user.UserID
            return redirect("dashboard")
        except Users.DoesNotExist:
            messages.error(request, "Invalid username or password")
            return render(request, "login.html")

    return render(request, "login.html")

def logout_user(request):
    # Clears both Django auth and your custom session data
    logout(request) 
    request.session.flush()
    return redirect('login')


# --- TRACKER LOGIC ---

def dashboard(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    last_log = PeriodLog.objects.filter(user_id=user_id).order_by('-StartDate').first()
    
    context = {
        "cycle_day": "--",
        "last_period": "Not Available",
        "next_period": "Not Available",
        "recent_symptoms": "No symptoms logged"
    }

    if last_log:
        today = date.today()
        start_date = last_log.StartDate
        delta = (today - start_date).days + 1
        context["cycle_day"] = delta if delta > 0 else 1
        context["last_period"] = start_date.strftime("%d %b %Y")
        
        cycle_len = last_log.CycleLength if last_log.CycleLength else 28
        prediction_date = start_date + timedelta(days=cycle_len)
        context["next_period"] = prediction_date.strftime("%d %b %Y")

        # Fetch the very last symptom name
        last_symptom = SymptomLog.objects.filter(user_id=user_id).order_by('-LogDate').first()
        if last_symptom:
            context["recent_symptoms"] = f"{last_symptom.SymptomName} (Level {last_symptom.Severity})"

    return render(request, "dashboard.html", context)

def add_period(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    if request.method == "POST":
        current_user = Users.objects.get(UserID=user_id)
        s_date = request.POST.get('startDate')
        dur = request.POST.get('duration')
        c_len = request.POST.get('cycleLength')
        note = request.POST.get('notes')

        PeriodLog.objects.create(
            user=current_user,
            StartDate=s_date,
            Duration=dur,
            CycleLength=c_len if c_len else None,
            Notes=note
        )
        messages.success(request, "Cycle details saved successfully!")
        return redirect("history")

    return render(request, "add_period.html")

def history(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    logs = PeriodLog.objects.filter(user_id=user_id).order_by('-StartDate')

    for log in logs:
        # Calculate EndDate: Start + Duration - 1 day
        log.end_date = log.StartDate + timedelta(days=int(log.Duration) - 1)

    return render(request, "history.html", {"logs": logs})



def prediction(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    avg_cycle = PeriodLog.objects.filter(user_id=user_id).aggregate(Avg('CycleLength'))['CycleLength__avg']
    avg_cycle = int(avg_cycle) if avg_cycle else 28

    last_log = PeriodLog.objects.filter(user_id=user_id).order_by('-StartDate').first()

    context = {
        "avg_cycle": avg_cycle,
        "next_period": None,
        "ovulation_day": None,
        "fertile_start": None,
        "fertile_end": None,
        "days_until": 0,
    }

    if last_log:
        next_period_date = last_log.StartDate + timedelta(days=avg_cycle)
        context["next_period"] = next_period_date
        context["days_until"] = (next_period_date - date.today()).days
        
        ovulation_date = next_period_date - timedelta(days=14)
        context["ovulation_day"] = ovulation_date
        context["fertile_start"] = ovulation_date - timedelta(days=5)
        context["fertile_end"] = ovulation_date + timedelta(days=1)

    return render(request, "prediction.html", context)

def add_symptoms(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    current_user = Users.objects.get(UserID=user_id)

    if request.method == "POST":
        name = request.POST.get('symptomName')
        sev = request.POST.get('severity')

        SymptomLog.objects.create(
            user=current_user,
            SymptomName=name,
            Severity=sev
        )
        messages.success(request, "Symptom recorded!")
        return redirect('add_symptoms')

    symptom_logs = SymptomLog.objects.filter(user=current_user).order_by('-LogDate')
    return render(request, "add_symptoms.html", {"symptom_logs": symptom_logs})

def reports(request):
    if "user_id" not in request.session:
        return redirect("login")
    return render(request, "Reports.html")

from django.db.models import Avg, Count
from datetime import timedelta

def reports(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    # 1. Calculate Summary Stats
    period_stats = PeriodLog.objects.filter(user_id=user_id).aggregate(
        avg_cycle=Avg('CycleLength'),
        avg_dur=Avg('Duration')
    )

    # 2. Get Symptoms and their counts (Data for Bar Chart)
    # This groups symptoms by name and counts occurrences
    symptom_counts = SymptomLog.objects.filter(user_id=user_id).values('SymptomName').annotate(
        total=Count('SymptomName')
    ).order_by('-total')

    # 3. Get Period Logs (Data for Table & Line Chart)
    # We use .order_by('StartDate') for the graph to show time moving forward
    logs_for_chart = PeriodLog.objects.filter(user_id=user_id).order_by('StartDate')
    
    # We use -StartDate for the table so the user sees recent entries first
    logs_for_table = PeriodLog.objects.filter(user_id=user_id).order_by('-StartDate')

    context = {
        "avg_cycle": period_stats['avg_cycle'] or 0,
        "avg_duration": period_stats['avg_dur'] or 0,
        "symptom_counts": symptom_counts,
        "logs_chart": logs_for_chart,  # Chronological order for the graph
        "logs_table": logs_for_table,  # Newest first for the table
    }

    return render(request, "Reports.html", context)