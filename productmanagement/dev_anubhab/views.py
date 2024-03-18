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
      # Save Department
        department_data = data.get('department_info', {})
        department_serializer = DepartmentSerializer(data=department_data)
        department_serializer.is_valid(raise_exception=True)
        department_instance = department_serializer.save()
        
        try:
            with transaction.atomic():    # Save Basic_Info
                basic_info_data = data.get('basic_info', {})
                basic_info_data['department_id'] = department_instance.id
                basic_info_serializer = BasicInfoSerializer(data=basic_info_data)
                basic_info_serializer.is_valid(raise_exception=True)
                basic_info_instance = basic_info_serializer.save()

                # Save PriceCost
                price_cost_data = data.get('price_cost', {})
                price_cost_data['basic_info_id'] = basic_info_instance.product_id
                price_cost_serializer = PriceCostSerializer(data=price_cost_data)
                price_cost_serializer.is_valid(raise_exception=True)
                price_cost_serializer.save()

            return Response({"message": "Products created successfully", "data" : {
                    "department_info" : department_serializer.data,
                    "basic_info" : basic_info_serializer.data,
                    "price_cost" : price_cost_serializer.data
                }}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateProductsView(GenericAPIView):
    ##### Updating the data from the product_id and returing the whole data of that items #####
    def put(self, request, product_id):
        try:
            basic_info_instance = Basic_Info.objects.get(product_id=product_id)

            basic_info_serializer = BasicInfoSerializer(basic_info_instance, data=request.data.get('basic_info', {}), partial=True)
            if basic_info_serializer.is_valid():
                basic_info_instance = basic_info_serializer.save()
            else:
                return Response(basic_info_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            

            department_data = request.data.get('department', {})
            if department_data:
                department_instance = basic_info_instance.department_id
                department_serializer = DepartmentSerializer(department_instance, data=department_data, partial=True)
                if department_serializer.is_valid():
                    department_instance = department_serializer.save()
                else:
                    return Response(department_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            price_cost_data = request.data.get('price_cost', {})
            if price_cost_data:
                price_cost_instance = PriceCost.objects.get(basic_info_id=basic_info_instance.product_id)
                price_cost_serializer = PriceCostSerializer(price_cost_instance, data=price_cost_data, partial=True)
                if price_cost_serializer.is_valid():
                    price_cost_instance = price_cost_serializer.save()
                else:
                    return Response(price_cost_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse({
                "department": DepartmentSerializer(department_instance).data if department_data else None,
                "basic_info": basic_info_serializer.data,
                "price_cost": PriceCostSerializer(price_cost_instance).data if price_cost_data else None
            }, status=status.HTTP_200_OK)
        
        except Basic_Info.DoesNotExist:
            return Response({"message": "Basic_Info with specified product ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except PriceCost.DoesNotExist:
            return Response({"message": "PriceCost associated with specified Basic_Info ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
class DeleteProductView(GenericAPIView):
    def delete(self, request, product_id):
        try:
            # Retrieve Basic_Info object by product_id
            basic_info_instance = Basic_Info.objects.get(product_id=product_id)
            
            # Retrieve Department object associated with the Basic_Info
            department_instance = basic_info_instance.department_id
            
            # Retrieve PriceCost object associated with the Basic_Info
            price_cost_instance = PriceCost.objects.get(basic_info_id=product_id)
            
            # Delete all related data
            basic_info_instance.delete()
            department_instance.delete()
            price_cost_instance.delete()
            
            return Response({"message": "Product and related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
        except Basic_Info.DoesNotExist:
            return Response({"message": "Basic_Info with specified product ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Department.DoesNotExist:
            return Response({"message": "Department associated with specified Basic_Info does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except PriceCost.DoesNotExist:
            return Response({"message": "PriceCost associated with specified Basic_Info does not exist"}, status=status.HTTP_404_NOT_FOUND)