from rest_framework import serializers
from .models import Department, Basic_Info, PriceCost

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
    def create(self, validated_data):
        return Department.objects.create(**validated_data)

class BasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basic_Info
        fields = "__all__"


class PriceCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceCost
        fields = "__all__"