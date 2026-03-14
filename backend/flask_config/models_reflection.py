# Flask models using SQLAlchemy - Exact mapping to existing database tables

from flask_config.app_config import db
from sqlalchemy import Enum

class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    user_type = db.Column(Enum('SALARIED', 'BUSINESS', name='user_type_enum'), nullable=False)
    monthly_income = db.Column(db.Numeric(15, 2), nullable=True)
    salary_slab = db.Column(db.String(50), nullable=True)
    business_name = db.Column(db.String(100), nullable=True)

    # Relationships
    accounts = db.relationship('Account', backref='user', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    user_badges = db.relationship('UserBadge', backref='user', lazy=True)
    business_metrics = db.relationship('BusinessMetrics', backref='user', uselist=False)
    user_stats = db.relationship('UserStats', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.name}>'

class Account(db.Model):
    __tablename__ = 'account'

    account_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    account_type = db.Column(Enum('MAIN', 'SAVINGS', 'GOAL', name='account_type_enum'), nullable=True)
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True)

    def __repr__(self):
        return f'<Account {self.account_id} - {self.account_type}>'

class Alert(db.Model):
    __tablename__ = 'alert'

    alert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    alert_type = db.Column(Enum('OVERSPEND', 'LOW_SAVING', 'PROFIT_DROP', name='alert_type_enum'), nullable=True)
    message = db.Column(db.Text, nullable=True)
    severity = db.Column(Enum('LOW', 'MEDIUM', 'HIGH', name='severity_enum'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Alert {self.alert_id} - {self.alert_type}>'

class Badge(db.Model):
    __tablename__ = 'badge'

    badge_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    badge_name = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, nullable=True)
    criteria_type = db.Column(Enum('SAVING', 'STREAK', 'PROFIT', name='criteria_type_enum'), nullable=True)

    # Relationships
    user_badges = db.relationship('UserBadge', backref='badge', lazy=True)

    def __repr__(self):
        return f'<Badge {self.badge_name}>'

class BusinessMetrics(db.Model):
    __tablename__ = 'business_metrics'

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    total_capital_invested = db.Column(db.Numeric(15, 2), nullable=True)
    total_revenue = db.Column(db.Numeric(15, 2), nullable=True)
    total_expense = db.Column(db.Numeric(15, 2), nullable=True)
    profit = db.Column(db.Numeric(15, 2), nullable=True)
    break_even_achieved = db.Column(db.Boolean, default=False)
    cash_runway_months = db.Column(db.Integer, nullable=True)
    last_updated = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<BusinessMetrics for user {self.user_id}>'

class Category(db.Model):
    __tablename__ = 'category'

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50), nullable=False)
    category_type = db.Column(Enum('FIXED', 'VARIABLE', name='category_type_enum'), nullable=True)
    applies_to = db.Column(Enum('SALARIED', 'BUSINESS', 'BOTH', name='applies_to_enum'), nullable=True)

    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.category_name}>'

class Goal(db.Model):
    __tablename__ = 'goal'

    goal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    goal_title = db.Column(db.String(100), nullable=True)
    target_amount = db.Column(db.Numeric(15, 2), nullable=True)
    current_amount = db.Column(db.Numeric(15, 2), default=0.00)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(Enum('ACTIVE', 'COMPLETED', name='status_enum'), default='ACTIVE')

    def __repr__(self):
        return f'<Goal {self.goal_title}>'

class InvestmentSuggestion(db.Model):
    __tablename__ = 'investment_suggestion'

    suggestion_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_type = db.Column(Enum('SALARIED', 'BUSINESS', name='user_type_enum_suggestion'), nullable=True)
    salary_slab = db.Column(db.String(50), nullable=True)
    min_savings_percent = db.Column(db.Numeric(5, 2), nullable=True)
    min_savings_amount = db.Column(db.Numeric(15, 2), nullable=True)
    investment_type = db.Column(db.String(50), nullable=True)
    suggestion_text = db.Column(db.Text, nullable=True)
    risk_level = db.Column(Enum('LOW', 'MEDIUM', 'HIGH', name='risk_level_enum'), nullable=True)

    def __repr__(self):
        return f'<InvestmentSuggestion {self.suggestion_id}>'

class SavingsRule(db.Model):
    __tablename__ = 'savings_rule'

    rule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    salary_slab = db.Column(db.String(50), nullable=False, unique=True)
    min_saving_percent = db.Column(db.Numeric(5, 2), nullable=True)
    max_expense_percent = db.Column(db.Numeric(5, 2), nullable=True)
    alert_threshold = db.Column(db.Numeric(15, 2), nullable=True)
    recommended_investments = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<SavingsRule {self.salary_slab}>'

class Transaction(db.Model):
    __tablename__ = 'transaction'

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.account_id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=True)
    transaction_type = db.Column(Enum('INCOME', 'EXPENSE', 'TRANSFER', name='transaction_type_enum'), nullable=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Transaction {self.transaction_id} - {self.amount}>'

class UserBadge(db.Model):
    __tablename__ = 'user_badge'

    user_badge_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.badge_id'), nullable=True)
    earned_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<UserBadge {self.user_badge_id}>'

class UserStats(db.Model):
    __tablename__ = 'user_stats'

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    total_points = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    monthly_saving_streak = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<UserStats for user {self.user_id}>'