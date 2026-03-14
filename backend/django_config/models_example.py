# Django models.py - Exact mapping to existing database tables
# These models are defined based on your provided schema with managed = False

from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    user_type = models.CharField(
        max_length=10,
        choices=[('SALARIED', 'SALARIED'), ('BUSINESS', 'BUSINESS')]
    )
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_slab = models.CharField(max_length=50, null=True, blank=True)
    business_name = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'user'

    def __str__(self):
        return self.name

class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    account_type = models.CharField(
        max_length=7,
        choices=[('MAIN', 'MAIN'), ('SAVINGS', 'SAVINGS'), ('GOAL', 'GOAL')],
        null=True, blank=True
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'account'

    def __str__(self):
        return f"{self.user.name} - {self.account_type}"

class Alert(models.Model):
    alert_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    alert_type = models.CharField(
        max_length=11,
        choices=[('OVERSPEND', 'OVERSPEND'), ('LOW_SAVING', 'LOW_SAVING'), ('PROFIT_DROP', 'PROFIT_DROP')],
        null=True, blank=True
    )
    message = models.TextField(null=True, blank=True)
    severity = models.CharField(
        max_length=6,
        choices=[('LOW', 'LOW'), ('MEDIUM', 'MEDIUM'), ('HIGH', 'HIGH')],
        null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'alert'

    def __str__(self):
        return f"Alert for {self.user.name if self.user else 'Unknown'}: {self.alert_type}"

class Badge(models.Model):
    badge_id = models.AutoField(primary_key=True)
    badge_name = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    points = models.IntegerField(null=True, blank=True)
    criteria_type = models.CharField(
        max_length=7,
        choices=[('SAVING', 'SAVING'), ('STREAK', 'STREAK'), ('PROFIT', 'PROFIT')],
        null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'badge'

    def __str__(self):
        return self.badge_name or f"Badge {self.badge_id}"

class BusinessMetrics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    total_capital_invested = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_expense = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    profit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    break_even_achieved = models.BooleanField(default=False)
    cash_runway_months = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'business_metrics'

    def __str__(self):
        return f"Business Metrics for {self.user.name}"

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50)
    category_type = models.CharField(
        max_length=8,
        choices=[('FIXED', 'FIXED'), ('VARIABLE', 'VARIABLE')],
        null=True, blank=True
    )
    applies_to = models.CharField(
        max_length=8,
        choices=[('SALARIED', 'SALARIED'), ('BUSINESS', 'BUSINESS'), ('BOTH', 'BOTH')],
        null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'category'

    def __str__(self):
        return self.category_name

class Goal(models.Model):
    goal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    goal_title = models.CharField(max_length=100, null=True, blank=True)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=9,
        choices=[('ACTIVE', 'ACTIVE'), ('COMPLETED', 'COMPLETED')],
        default='ACTIVE'
    )

    class Meta:
        managed = False
        db_table = 'goal'

    def __str__(self):
        return self.goal_title or f"Goal {self.goal_id}"

class InvestmentSuggestion(models.Model):
    suggestion_id = models.AutoField(primary_key=True)
    user_type = models.CharField(
        max_length=8,
        choices=[('SALARIED', 'SALARIED'), ('BUSINESS', 'BUSINESS')],
        null=True, blank=True
    )
    salary_slab = models.CharField(max_length=50, null=True, blank=True)
    min_savings_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_savings_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    investment_type = models.CharField(max_length=50, null=True, blank=True)
    suggestion_text = models.TextField(null=True, blank=True)
    risk_level = models.CharField(
        max_length=6,
        choices=[('LOW', 'LOW'), ('MEDIUM', 'MEDIUM'), ('HIGH', 'HIGH')],
        null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'investment_suggestion'

    def __str__(self):
        return f"Suggestion {self.suggestion_id}"

class SavingsRule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    salary_slab = models.CharField(max_length=50, unique=True)
    min_saving_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_expense_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    alert_threshold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    recommended_investments = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'savings_rule'

    def __str__(self):
        return f"Rule for {self.salary_slab}"

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='account_id', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id', null=True, blank=True)
    transaction_type = models.CharField(
        max_length=8,
        choices=[('INCOME', 'INCOME'), ('EXPENSE', 'EXPENSE'), ('TRANSFER', 'TRANSFER')],
        null=True, blank=True
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'transaction'

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"

class UserBadge(models.Model):
    user_badge_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, db_column='badge_id', null=True, blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'user_badge'

    def __str__(self):
        return f"{self.user.name if self.user else 'Unknown'} - {self.badge.badge_name if self.badge else 'Unknown Badge'}"

class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    total_points = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    monthly_saving_streak = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'user_stats'

    def __str__(self):
        return f"Stats for {self.user.name}"