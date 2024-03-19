from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from productapp.models import Basic_Info, Department, PriceCost
from productapp.serializers import BasicInfoSerializer, DepartmentSerializer, PriceCostSerializer
from django.http import JsonResponse

#### just for getting the data for the uuid field ####
class GetAllApi(GenericAPIView):
    def get(self, request):
        try:
            # Retrieve all Basic_Info objects
            basic_info_instances = Basic_Info.objects.all()
            
            # Serialize Basic_Info objects
            basic_info_serializer = BasicInfoSerializer(basic_info_instances, many=True)
            
            # Retrieve all Department objects
            department_instances = Department.objects.all()
            
            # Serialize Department objects
            department_serializer = DepartmentSerializer(department_instances, many=True)
            
            # Retrieve all PriceCost objects
            price_cost_instances = PriceCost.objects.all()
            
            # Serialize PriceCost objects
            price_cost_serializer = PriceCostSerializer(price_cost_instances, many=True)
            
            # Return serialized data for all items
            return Response({
                "basic_info": basic_info_serializer.data,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateAllProductModelView(GenericAPIView):
    def post(self, request):
        data = request.data
        
        # Check if department exists
        department_data = data.get('department_info', {})
        department_serializer = DepartmentSerializer(data=department_data)
        if department_serializer.is_valid():
            try:
                existing_department = Department.objects.get(name=department_data['name'])
                department_instance = existing_department
                department_message = "Department already exists. Basic info and price cost added."
            except Department.DoesNotExist:
                department_serializer.is_valid(raise_exception=True)
                department_instance = department_serializer.save()
                department_message = "New department added. Basic info and price cost created."
            
            # Save basic info in a transaction
            try:
                with transaction.atomic():
                    # Check if basic info exists
                    basic_info_data = data.get('basic_info', {})
                    existing_basic_info = Basic_Info.objects.filter(product_name=basic_info_data.get('product_name')).first()
                    if existing_basic_info:
                        return Response({"message": "Basic info already exists."}, status=status.HTTP_400_BAD_REQUEST)
                    
                    basic_info_data['department_id'] = department_instance.id
                    basic_info_serializer = BasicInfoSerializer(data=basic_info_data)
                    if basic_info_serializer.is_valid():
                        basic_info_instance = basic_info_serializer.save()
                        
                        # Save price cost
                        price_cost_data = data.get('price_cost', {})
                        price_cost_data['basic_info_id'] = basic_info_instance.product_id
                        price_cost_serializer = PriceCostSerializer(data=price_cost_data)
                        if price_cost_serializer.is_valid():
                            price_cost_serializer.save()
                            response_data = {
                                "department_info": DepartmentSerializer(department_instance).data,
                                "basic_info": basic_info_serializer.data,
                                "price_cost": price_cost_serializer.data
                            }
                            return Response({"message": department_message, "data": response_data}, status=status.HTTP_201_CREATED)
                        else:
                            raise Exception(price_cost_serializer.errors)
                    else:
                        raise Exception(basic_info_serializer.errors)
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(department_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateProductsView(GenericAPIView):
    def put(self, request, product_id):
        try:
            with transaction.atomic():
                # Retrieve Basic_Info object by product_id
                basic_info_instance = Basic_Info.objects.get(product_id=product_id)
                
                # Update Basic_Info data
                basic_info_serializer = BasicInfoSerializer(basic_info_instance, data=request.data.get('basic_info', {}), partial=True)
                basic_info_serializer.is_valid(raise_exception=True)
                basic_info_instance = basic_info_serializer.save()
                
                # Retrieve associated Department and PriceCost
                department_instance = basic_info_instance.department_id
                price_cost_instance = PriceCost.objects.get(basic_info_id=basic_info_instance.product_id)
            
                # Update Department if provided
                department_data = request.data.get('department', {})
                if department_data:
                    department_serializer = DepartmentSerializer(department_instance, data=department_data, partial=True)
                    department_serializer.is_valid(raise_exception=True)
                    department_instance = department_serializer.save()
                
                # Update PriceCost if provided
                price_cost_data = request.data.get('price_cost', {})
                if price_cost_data:
                    price_cost_serializer = PriceCostSerializer(price_cost_instance, data=price_cost_data, partial=True)
                    price_cost_serializer.is_valid(raise_exception=True)
                    price_cost_instance = price_cost_serializer.save()
                
            # Return updated data along with associated Department and PriceCost
            return Response({
                "department_info": DepartmentSerializer(department_instance).data,
                "basic_info": basic_info_serializer.data,
                "price_cost": PriceCostSerializer(price_cost_instance).data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class DeleteProductView(GenericAPIView):
    def delete(self, request, product_id):
        try:
            # Filter Basic_Info object by product_id
            basic_info_instance = Basic_Info.objects.filter(product_id=product_id).first()
            
            if not basic_info_instance:
                return Response({"message": "Basic_Info with specified product ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
            # Delete Basic_Info and associated PriceCost
            basic_info_instance.delete()
            
            return Response({"message": "Basic_Info and associated PriceCost deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
        except (Basic_Info.DoesNotExist, PriceCost.DoesNotExist) as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)