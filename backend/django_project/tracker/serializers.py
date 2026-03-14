from rest_framework import serializers
from .models import User, Account, Transaction, Category, Goal, Alert

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'user_type', 'monthly_income', 'salary_slab', 'business_name']

class AccountSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Account
        fields = ['account_id', 'user', 'user_name', 'account_type', 'balance', 'created_at']
        read_only_fields = ['account_id', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'category_name', 'category_type', 'applies_to']

class TransactionSerializer(serializers.ModelSerializer):
    account_type = serializers.CharField(source='account.account_type', read_only=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'user', 'user_name', 'account', 'account_type',
            'category', 'category_name', 'transaction_type', 'amount',
            'description', 'transaction_date'
        ]
        read_only_fields = ['transaction_id', 'transaction_date']

    def validate(self, data):
        # Business logic validation
        if data['transaction_type'] == 'EXPENSE' and data['account'].balance < data['amount']:
            raise serializers.ValidationError("Insufficient account balance")

        if data['transaction_type'] == 'TRANSFER' and data['account'].balance < data['amount']:
            raise serializers.ValidationError("Insufficient funds for transfer")

        return data

class GoalSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            'goal_id', 'user', 'user_name', 'goal_title', 'target_amount',
            'current_amount', 'target_date', 'status', 'progress_percentage'
        ]
        read_only_fields = ['goal_id']

    def get_progress_percentage(self, obj):
        if obj.target_amount > 0:
            return round((obj.current_amount / obj.target_amount) * 100, 2)
        return 0

class AlertSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Alert
        fields = ['alert_id', 'user', 'user_name', 'alert_type', 'message', 'severity', 'is_read', 'created_at']
        read_only_fields = ['alert_id', 'created_at']