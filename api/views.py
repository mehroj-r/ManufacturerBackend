from pprint import pprint

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from app.models import Product, ProductMaterial, Warehouse, Material


class ProductMaterialsAPiView(APIView):
    """
    API view to retrieve product materials.
    """

    def validate_request(self, request):
        """"
        Validate the request data.
        """

        products = request.data

        # Check if products are provided
        if not products:
            raise ValidationError({"error": "No products provided."})

        # Validate the products data
        for product in products:
            if not isinstance(product, dict):
                raise ValidationError({"error": "Invalid product data."})

            if "product" not in product or "quantity" not in product:
                raise ValidationError({"error": "Request must include 'product' and 'quantity'."})

    def get_required_materials(self, product_quantities):
        """
        Retrieve the required materials for the given products.
        {
        "shim": [],
        "mato": [],
        }
        """

        materials = ProductMaterial.objects.filter(product_id__in=product_quantities.keys()).select_related('material')
        materials_by_type = {}

        for material in materials:
            if material.material_id not in materials_by_type:
                materials_by_type[material] = []
            material.quantity *= product_quantities[material.product_id]
            materials_by_type[material].append(material)


        return materials_by_type

    def get_stock_materials(self, materials):
        """
        Get the stock materials for the given materials.
        """
        material_ids = [material.material_id for material in materials.keys()]
        stock_data = Warehouse.objects.filter(material_id__in=material_ids).order_by('price').select_related('material')

        stock = {}

        for stock_item in stock_data:
            material = stock_item.material

            if material not in stock:
                stock[material] = []

            stock[material].append(stock_item)

        return stock

    def get_stock_for_material_quantity(self, stock, material, quantity):
        """
        Get the stock for a specific material with given quantity.
        """

        # if the material is not in stock, return None
        if material not in stock:
            return [{
                "warehouse_id": None,
                "material": material.name,
                "qty": quantity,
                "price": None
            }]

        stock_distribution = []

        for item in stock[material]:

            # if the stock is empty, skip
            if item.remainder <= 0:
                continue

            # if the stock is enough, take whole and stop
            if item.remainder >= quantity:
                stock_distribution.append({
                    "warehouse_id": item.id,
                    "material": material.name,
                    "qty": quantity,
                    "price": item.price
                })
                item.remainder -= quantity
                quantity = 0
                break
            else: # if the stock is not enough, take all of it and continue
                stock_distribution.append({
                    "warehouse_id": item.id,
                    "material": material.name,
                    "qty": item.remainder,
                    "price": item.price
                })
                quantity -= item.remainder
                item.remainder = 0

        # if there is still quantity left, add it with None values to indicate not enough stock
        if quantity > 0:
            stock_distribution.append({
                "warehouse_id": None,
                "material": material.name,
                "qty": quantity,
                "price": None
            })

        return stock_distribution

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to receive request details.
        """

        # Validate the request data
        self.validate_request(request)

        # Extract the products from the request data
        products_data = request.data

        # Get the product details
        product_ids = [p["product"] for p in products_data]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        product_quantities = {p["product"]: p["quantity"] for p in products_data}


        # Get the required materials for the products
        materials = self.get_required_materials(product_quantities)

        # Get the stock materials
        stock = self.get_stock_materials(materials)

        # Prepare the response data
        result = []

        # Iterate through the products and their materials
        for product_id in product_quantities:

            if product_id not in products:
                continue

            product_name = products[product_id].name
            product_qty = product_quantities[product_id]
            product_materials = []

            for material_list in materials.values():
                for product_material in material_list:
                    if product_material.product_id == product_id:
                        quantity = product_material.quantity

                        stock_distribution = self.get_stock_for_material_quantity(stock, product_material.material, quantity)

                        product_materials.extend(stock_distribution)

            # Add the product details to the result
            result.append({
                "product_name": product_name,
                "product_qty": product_qty,
                "product_materials": product_materials
            })


        return Response({"result": result})