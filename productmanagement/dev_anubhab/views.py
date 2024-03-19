from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from productapp.models import Basic_Info, Department, PriceCost
from productapp.serializers import BasicInfoSerializer, DepartmentSerializer, PriceCostSerializer
from django.http import JsonResponse
from django.db.models import Count
#### just for getting the data for the uuid field ####
class GetAllApi(GenericAPIView):
    queryset = Basic_Info.objects.select_related('department_id').all()
    def get(self,request):
        items = self.get_queryset()

        search_query = request.query_params.get('search', None)

        if search_query:
            items = items.filter(Q(product_name__icontains=search_query) | Q(sku__icontains=search_query) | Q(department_id__name__icontains=search_query))

        sort_by = request.query_params.get('sort_by', None)
        sort_order = request.query_params.get('sort_order', None)

        if sort_by:
            if sort_order == 'descending':
                sort_by = '-' + sort_by
            items = items.order_by(sort_by)

        basic_info_serializer = BasicInfoSerializer(items, many=True).data
        department_serializer = DepartmentSerializer([item.department_id for item in items], many=True).data
        price_cost_serializer = []
        for item in items:
            price_cost_serializer.extend(PriceCostSerializer(item.pricecost_set.all(), many=True).data)
        
        context = []
        for basic_info, department, price_cost in zip(basic_info_serializer, department_serializer, price_cost_serializer):
            department_instance = Department.objects.get(id=department['id'])
            basic_info['department_id'] = department_instance.id if department_instance else None
            context.append({
                "basic_info": basic_info,
                "department": DepartmentSerializer(department_instance).data if department_instance else {},
                "price_cost": price_cost,
            })


        return Response(context)

class CreateAllProductModelView(GenericAPIView):
    def post(self, request):
        data = request.data
        

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
            
            try:
                with transaction.atomic():
                    # Check if basic info exists
                    basic_info_data = data.get('basic_info', {})
                    existing_basic_info = Basic_Info.objects.filter(sku = basic_info_data.get('sku')).first()
                    if existing_basic_info:
                        return Response({"message": "Basic info already exists."}, status=status.HTTP_400_BAD_REQUEST)
                    
                    basic_info_data['department_id'] = department_instance.id
                    
                    basic_info_serializer = BasicInfoSerializer(data=basic_info_data)
                    if basic_info_serializer.is_valid():
                        basic_info_instance = basic_info_serializer.save()
                        
                        price_cost_data = data.get('price_cost', {})
                        print("------------->>>", price_cost_data)
                        price_cost_data['basic_info_id'] = basic_info_instance.product_id
                        price_cost_serializer = PriceCostSerializer(data=price_cost_data)
                        if price_cost_serializer.is_valid():
                            price_cost_serializer.save()
                            response_data = {
                                "department_info": DepartmentSerializer(department_instance).data,
                                "basic_info": basic_info_serializer.data,
                                "price_cost": price_cost_serializer.data,
                            }
                            return Response({"message": department_message, "data": response_data}, status=status.HTTP_201_CREATED)
                    else:
                        raise Exception(basic_info_serializer.errors)
            except Exception as e:
                return Response({"message": str(e), "error": basic_info_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"message": "Department data is invalid.", "error": department_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class UpdateProductsView(GenericAPIView):
    def put(self, request, product_id):
        try:
            with transaction.atomic():
                basic_info_instance = Basic_Info.objects.get(product_id=product_id)
                
                basic_info_serializer = BasicInfoSerializer(basic_info_instance, data=request.data.get('basic_info', {}), partial=True)
                if basic_info_serializer.is_valid():
                    basic_info_instance = basic_info_serializer.save()
                else:
                    return Response(basic_info_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                department_instance = basic_info_instance.department_id
                department_data = Department.objects.annotate(num_basic_info=Count('basic_info'))
                position_in_department = department_data.get(id=department_instance.id).num_basic_info
                
                price_cost_data = request.data.get('price_cost', {})
                if price_cost_data:
                    price_cost_instance = PriceCost.objects.get(basic_info_id=basic_info_instance.product_id)
                    price_cost_serializer = PriceCostSerializer(price_cost_instance, data=price_cost_data, partial=True)
                    if price_cost_serializer.is_valid():
                        price_cost_instance = price_cost_serializer.save()
                    else:
                        return Response(price_cost_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "Price cost data is required"}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    "position_in_department": position_in_department,
                    "department_info": DepartmentSerializer(department_instance).data,
                    "basic_info": basic_info_serializer.data,
                    "price_cost": PriceCostSerializer(price_cost_instance).data if price_cost_data else None
                    
                }, status=status.HTTP_200_OK)
            
        except Basic_Info.DoesNotExist:
            return Response({"message": "Basic_Info with specified product ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
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