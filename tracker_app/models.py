from django.db import models

# 1. User Account Model
class Users(models.Model):
    UserID = models.AutoField(primary_key=True)
    Username = models.CharField(max_length=255, unique=True)
    Password = models.CharField(max_length=255)
    IsActive = models.BooleanField(default=True)

    class Meta:
        db_table = 'Users'

    def __str__(self):
        return self.Username

# 2. Period Tracking Model
class PeriodLog(models.Model):
    LogID = models.AutoField(primary_key=True)
    # This links the log to a specific user in the Users table
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserID')
    StartDate = models.DateField()
    Duration = models.IntegerField()  # Number of days the period lasted
    CycleLength = models.IntegerField(null=True, blank=True) # Days between cycles
    Notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'PeriodLogs'

# 3. Symptoms Tracking Model
class SymptomLog(models.Model):
    SymptomID = models.AutoField(primary_key=True)
    # This links the symptom to the same Users table
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserID')
    SymptomName = models.CharField(max_length=100)
    Severity = models.IntegerField() # Scale of 1 to 5
    # DateTimeField is used to capture exact time and avoid SQL Server Date conversion errors
    LogDate = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'SymptomLogs'