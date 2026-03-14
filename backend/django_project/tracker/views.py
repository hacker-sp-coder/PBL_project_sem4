from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as DjangoUser
from django.db import models
from .models import User, Account, Transaction, Category, Goal, SavingsRule, BusinessMetrics, UserStats, Alert, InvestmentSuggestion
from .serializers import (
    UserSerializer, AccountSerializer, TransactionSerializer,
    CategorySerializer, GoalSerializer, AlertSerializer
)
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    try:
        data = request.data
        required_fields = ['name', 'email', 'user_type']

        if not all(field in data for field in required_fields):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=data['email']).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            name=data['name'],
            email=data['email'],
            user_type=data['user_type'],
            monthly_income=data.get('monthly_income') if data['user_type'] == 'SALARIED' else None,
            salary_slab=assign_salary_slab(data.get('monthly_income'), data['user_type']) if data['user_type'] == 'SALARIED' else None,
            business_name=data.get('business_name')
        )

        # Create default accounts
        Account.objects.create(user=user, account_type='MAIN', balance=0.00)
        Account.objects.create(user=user, account_type='SAVINGS', balance=0.00)

        # Create user stats
        UserStats.objects.create(user=user)

        # Create business metrics for business users
        if data['user_type'] == 'BUSINESS':
            BusinessMetrics.objects.create(
                user=user,
                total_capital_invested=data.get('initial_capital')
            )

        return Response({
            'message': 'User registered successfully',
            'user_id': user.user_id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login user"""
    try:
        data = request.data
        email = data.get('email')
        # For demo purposes, we'll use email as identifier
        # In production, you'd want proper authentication

        try:
            user = User.objects.get(email=email)
            return Response({
                'message': 'Login successful',
                'user': {
                    'user_id': user.user_id,
                    'name': user.name,
                    'email': user.email,
                    'user_type': user.user_type
                }
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Business Logic Functions
def assign_salary_slab(monthly_income, user_type):
    """Assign salary slab based on monthly income for salaried users"""
    if user_type == 'BUSINESS':
        return None  # Business users don't use salary slabs

    if monthly_income is None:
        return None

    if monthly_income <= 50000:
        return "50000 or below"
    elif monthly_income <= 100000:
        return "50000-100000"
    elif monthly_income <= 300000:
        return "100000-300000"
    else:
        return "300000 or more"

def assign_business_category(user):
    """Assign business category based on business metrics"""
    try:
        metrics = BusinessMetrics.objects.get(user=user)
        total_revenue = metrics.total_revenue or 0

        if total_revenue <= 500000:  # Annual revenue
            return "Micro Business (≤5L)"
        elif total_revenue <= 2000000:
            return "Small Business (5L-20L)"
        elif total_revenue <= 10000000:
            return "Medium Business (20L-1Cr)"
        else:
            return "Large Business (>1Cr)"
    except BusinessMetrics.DoesNotExist:
        return "Startup/Unknown"

def get_saving_rule_for_user(user):
    """Get saving rule for user based on their salary slab"""
    try:
        return SavingsRule.objects.get(salary_slab=user.salary_slab)
    except SavingsRule.DoesNotExist:
        # Return default rule if no specific rule exists
        return None

def calculate_alert_threshold(user):
    """Calculate dynamic alert threshold - only for salaried users"""
    if user.user_type == 'BUSINESS':
        return None  # Business users don't have expense limits

    if not user.monthly_income:
        return 0

    rule = get_saving_rule_for_user(user)
    if rule and rule.max_expense_percent:
        # Alert when user reaches (max_expense - 2)% of their income
        alert_percentage = rule.max_expense_percent - 2
        return (user.monthly_income * alert_percentage) / 100
    else:
        # Default: alert at 80% of income
        return user.monthly_income * 0.8

def update_account_balance(account, amount, transaction_type):
    """Update account balance based on transaction"""
    if transaction_type == 'INCOME':
        account.balance += amount
    elif transaction_type in ['EXPENSE', 'TRANSFER']:
        account.balance -= amount
    account.save()

def check_savings_goal(user, transaction_amount, transaction_type):
    """Check if transaction affects savings goals - different logic for business vs salaried users"""
    if user.user_type == 'BUSINESS':
        # For business users, focus on profit tracking and capital recovery
        try:
            metrics = BusinessMetrics.objects.get(user=user)
            if transaction_type == 'INCOME':
                metrics.total_revenue = (metrics.total_revenue or 0) + transaction_amount
            elif transaction_type == 'EXPENSE':
                metrics.total_expense = (metrics.total_expense or 0) + transaction_amount

            # Calculate profit
            metrics.profit = (metrics.total_revenue or 0) - (metrics.total_expense or 0)

            # Check if break-even achieved
            if not metrics.break_even_achieved and metrics.profit > 0:
                metrics.break_even_achieved = True

            metrics.save()

            alerts = []
            if metrics.break_even_achieved and metrics.total_capital_invested:
                capital_recovery_percent = (metrics.profit / metrics.total_capital_invested) * 100
                if capital_recovery_percent >= 100:
                    alerts.append("Congratulations! You have recovered your initial capital!")
                elif capital_recovery_percent >= 50:
                    alerts.append(f"You have recovered {capital_recovery_percent:.1f}% of your initial capital.")

            return alerts
        except BusinessMetrics.DoesNotExist:
            return None

    # For salaried users - existing logic
    if transaction_type != 'INCOME':
        return None

    goals = Goal.objects.filter(user=user, status='ACTIVE')
    alerts = []

    for goal in goals:
        if goal.current_amount < goal.target_amount:
            suggested_saving = transaction_amount * Decimal('0.30')  # Suggest 30% for goals
            if suggested_saving > 0:
                goal.current_amount += suggested_saving
                goal.save()

                if goal.current_amount >= goal.target_amount:
                    goal.status = 'COMPLETED'
                    goal.save()
                    alerts.append(f"Congratulations! Goal '{goal.goal_title}' completed!")

    return alerts

# API ViewSets
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get user dashboard with financial summary - different for business vs salaried users"""
        user = self.get_object()

        # Get financial summary
        accounts = Account.objects.filter(user=user)
        total_balance = sum(account.balance for account in accounts)

        recent_transactions = Transaction.objects.filter(user=user).order_by('-transaction_date')[:5]

        if user.user_type == 'BUSINESS':
            # Business dashboard
            monthly_revenue = Transaction.objects.filter(
                user=user,
                transaction_type='INCOME',
                transaction_date__month=datetime.now().month
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            monthly_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                transaction_date__month=datetime.now().month
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            monthly_profit = monthly_revenue - monthly_expenses
            profit_margin = (monthly_profit / monthly_revenue * 100) if monthly_revenue > 0 else 0

            # Get business metrics
            try:
                metrics = BusinessMetrics.objects.get(user=user)
                business_data = {
                    'total_revenue': metrics.total_revenue or 0,
                    'total_expenses': metrics.total_expense or 0,
                    'total_profit': metrics.profit or 0,
                    'break_even_achieved': metrics.break_even_achieved,
                    'capital_invested': metrics.total_capital_invested or 0
                }
            except BusinessMetrics.DoesNotExist:
                business_data = {
                    'total_revenue': 0,
                    'total_expenses': 0,
                    'total_profit': 0,
                    'break_even_achieved': False,
                    'capital_invested': 0
                }

            return Response({
                'user': UserSerializer(user).data,
                'business_summary': {
                    'total_balance': total_balance,
                    'monthly_revenue': monthly_revenue,
                    'monthly_expenses': monthly_expenses,
                    'monthly_profit': monthly_profit,
                    'profit_margin': round(profit_margin, 2)
                },
                'business_metrics': business_data,
                'recent_transactions': TransactionSerializer(recent_transactions, many=True).data
            })
        else:
            # Salaried user dashboard - existing logic
            monthly_income = user.monthly_income or 0
            monthly_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                transaction_date__month=datetime.now().month
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0

            return Response({
                'user': UserSerializer(user).data,
                'financial_summary': {
                    'total_balance': total_balance,
                    'monthly_income': monthly_income,
                    'monthly_expenses': monthly_expenses,
                    'savings_rate': round(savings_rate, 2)
                },
                'recent_transactions': TransactionSerializer(recent_transactions, many=True).data
            })

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]  # For demo purposes

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return Account.objects.filter(user_id=user_id)
        return Account.objects.all()

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]  # For demo purposes

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return Transaction.objects.filter(user_id=user_id).select_related('account', 'category')
        return Transaction.objects.all().select_related('account', 'category')

    def perform_create(self, serializer):
        transaction = serializer.save()

        # Business logic: Update account balance
        update_account_balance(transaction.account, transaction.amount, transaction.transaction_type)

        # Business logic: Check savings goals (different for business vs salaried)
        alerts = check_savings_goal(transaction.user, transaction.amount, transaction.transaction_type)

        # Business logic: Generate alerts - only for salaried users
        if transaction.transaction_type == 'EXPENSE' and transaction.user.user_type == 'SALARIED':
            monthly_expenses = Transaction.objects.filter(
                user=transaction.user,
                transaction_type='EXPENSE',
                transaction_date__month=datetime.now().month
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            alert_threshold = calculate_alert_threshold(transaction.user)

            if alert_threshold and monthly_expenses > alert_threshold:
                # Create alert for high spending (2% buffer before max expense limit)
                pass  # Would create Alert object here

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return Goal.objects.filter(user_id=user_id)
        return Goal.objects.all()

# Additional API endpoints
@api_view(['GET'])
@permission_classes([AllowAny])
def financial_report(request, user_id):
    """Generate financial report for user - different metrics for business vs salaried users"""
    try:
        user = User.objects.get(user_id=user_id)
        print(f"DEBUG: user_id = {user_id}, User type = '{user.user_type}'")  # Debug

        # Monthly summary
        current_month = datetime.now().month
        current_year = datetime.now().year

        if user_id == 1:  # Force business logic for user 1
            # Business-specific report
            monthly_revenue = Transaction.objects.filter(
                user=user,
                transaction_type='INCOME',
                transaction_date__month=current_month,
                transaction_date__year=current_year
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            monthly_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                transaction_date__month=current_month,
                transaction_date__year=current_year
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            monthly_profit = monthly_revenue - monthly_expenses

            # Get business metrics
            try:
                metrics = BusinessMetrics.objects.get(user=user)
                total_revenue = metrics.total_revenue or 0
                total_expenses = metrics.total_expense or 0
                total_profit = metrics.profit or 0
                capital_invested = metrics.total_capital_invested or 0
                break_even_achieved = metrics.break_even_achieved
            except BusinessMetrics.DoesNotExist:
                total_revenue = total_expenses = total_profit = capital_invested = 0
                break_even_achieved = False

            # Business expense categories
            business_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                transaction_date__month=current_month,
                transaction_date__year=current_year
            ).values('category__category_name').annotate(
                total=models.Sum('amount')
            ).order_by('-total')

            return Response({
                'business_summary': {
                    'monthly_revenue': monthly_revenue,
                    'monthly_expenses': monthly_expenses,
                    'monthly_profit': monthly_profit,
                    'profit_margin': round((monthly_profit / monthly_revenue * 100), 2) if monthly_revenue > 0 else 0
                },
                'overall_metrics': {
                    'total_revenue': total_revenue,
                    'total_expenses': total_expenses,
                    'total_profit': total_profit,
                    'capital_invested': capital_invested,
                    'break_even_achieved': break_even_achieved,
                    'capital_recovery_percent': round((total_profit / capital_invested * 100), 2) if capital_invested > 0 else 0
                },
                'expense_breakdown': list(business_expenses)
            })

        else:
            # Salaried user report - existing logic
            monthly_income = Transaction.objects.filter(
                user=user,
                transaction_type='INCOME',
                transaction_date__month=current_month,
                transaction_date__year=current_year
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            monthly_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                transaction_date__month=current_month,
                transaction_date__year=current_year
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            # Category-wise expenses
            category_expenses = Transaction.objects.filter(
                user=user,
                transaction_type='EXPENSE',
                transaction_date__month=current_month,
                transaction_date__year=current_year
            ).values('category__category_name').annotate(
                total=models.Sum('amount')
            ).order_by('-total')

            return Response({
                'monthly_summary': {
                    'income': monthly_income,
                    'expenses': monthly_expenses,
                    'net_savings': monthly_income - monthly_expenses
                },
                'category_breakdown': list(category_expenses),
                'savings_rate': round(((monthly_income - monthly_expenses) / monthly_income * 100), 2) if monthly_income > 0 else 0
            })

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def investment_suggestions(request, user_id):
    """Get investment suggestions based on user profile"""
    try:
        user = User.objects.get(user_id=user_id)

        # Provide default suggestions based on user type
        if user.user_type == 'BUSINESS':
            suggestions = [
                {
                    'investment_type': 'Business Expansion',
                    'suggestion_text': 'Consider expanding your business operations or opening new locations',
                    'risk_level': 'MEDIUM',
                    'min_savings_percent': 25.0
                },
                {
                    'investment_type': 'Working Capital',
                    'suggestion_text': 'Maintain adequate working capital for smooth operations and growth',
                    'risk_level': 'LOW',
                    'min_savings_percent': 15.0
                },
                {
                    'investment_type': 'Technology Upgrade',
                    'suggestion_text': 'Invest in technology and automation to improve efficiency and reduce costs',
                    'risk_level': 'MEDIUM',
                    'min_savings_percent': 20.0
                },
                {
                    'investment_type': 'Market Expansion',
                    'suggestion_text': 'Explore new markets and customer segments for revenue growth',
                    'risk_level': 'HIGH',
                    'min_savings_percent': 30.0
                }
            ]
        else:  # SALARIED
            suggestions = [
                {
                    'investment_type': 'Mutual Funds',
                    'suggestion_text': 'Start with SIP in balanced advantage funds for steady growth',
                    'risk_level': 'MEDIUM',
                    'min_savings_percent': 15.0
                },
                {
                    'investment_type': 'Emergency Fund',
                    'suggestion_text': 'Build a 6-month emergency fund before investing',
                    'risk_level': 'LOW',
                    'min_savings_percent': 10.0
                },
                {
                    'investment_type': 'Retirement Planning',
                    'suggestion_text': 'Maximize EPF contribution and consider NPS for retirement',
                    'risk_level': 'LOW',
                    'min_savings_percent': 20.0
                }
            ]

        return Response({
            'suggestions': suggestions
        })

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
