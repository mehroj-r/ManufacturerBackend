from pprint import pprint
from typing import List, Dict, Any

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from app.models import Product, ProductMaterial, Warehouse, Material


class ProductMaterialsAPIView(APIView):
    """
    API view to retrieve product materials.
    """

    def validate_request(self) -> None:
        """"
        Validates the incoming request.

        :raises ValidationError: If the request data is invalid.

        """

        request = self.request

        # Check if the data is provided
        if not request.data:
            raise ValidationError({"error": "No data provided."})

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

    def get_required_materials(self, product_quantities: Dict[int, int]) -> Dict[int, List[ProductMaterial]]:
        """
        Retrieve the required materials for the given products.

        :param product_quantities: A dictionary mapping product IDs to their quantities.
        :return: A dictionary mapping material IDs to lists of ProductMaterial objects.

        """

        materials = (ProductMaterial.objects.filter(product_id__in=product_quantities.keys())
                     .select_related('material'))
        materials_by_type = {}

        # Group the materials by their IDs
        for material in materials:

            if material.material_id not in materials_by_type:
                materials_by_type[material.material_id] = []

            material.quantity *= product_quantities[material.product_id]

            materials_by_type[material.material_id].append(material)

        return materials_by_type

    def get_stock_for_materials(self, product_materials: Dict[int, List[ProductMaterial]]) -> Dict[int, List[Warehouse]]:
        """
        Get the stock materials for the required materials.

        :param product_materials: A dictionary mapping material IDs to lists of ProductMaterial objects.
        :return: A dictionary mapping material IDs to lists of Warehouse objects.

        """
        stock_data = (Warehouse.objects.filter(material_id__in=product_materials.keys())
                      .order_by('price')
                      .select_related('material'))

        stock = {}

        # Group the stock data by material ID
        for stock_item in stock_data:
            material_id = stock_item.material_id

            if material_id not in stock:
                stock[material_id] = []

            stock[material_id].append(stock_item)

        return stock

    def get_stock_distribution(self, stock: Dict[int, List[Warehouse]], material: Material, quantity: float) -> List[Dict[str, Any]]:
        """
        Get the stock for a specific material with given quantity.

        :param stock: A dictionary mapping material IDs to lists of Warehouse objects.
        :param material: The Material object for which to get the stock.
        :param quantity: The quantity of the material needed.

        :return: A list of dictionaries containing warehouse ID, material name, quantity, and price.

        """

        # if the material is not in stock, return None
        if material.id not in stock:
            return [{
                "warehouse_id": None,
                "material": material.name,
                "qty": quantity,
                "price": None
            }]

        stock_distribution = []

        for warehouse_item in stock[material.id]:

            # if the stock is empty, skip
            if warehouse_item.remainder <= 0:
                continue

            # If the remainder is less than the quantity needed, take all of it
            # Otherwise, take the quantity needed
            take_quantity = min(warehouse_item.remainder, quantity)

            stock_distribution.append({
                "warehouse_id": warehouse_item.id,
                "material": material.name,
                "qty": take_quantity,
                "price": warehouse_item.price
            })

            # Update quantity and remainder
            warehouse_item.remainder -= take_quantity
            quantity -= take_quantity

        # if there is still quantity left, add it with None values to indicate not enough stock
        if quantity > 0:
            stock_distribution.append({
                "warehouse_id": None,
                "material": material.name,
                "qty": quantity,
                "price": None
            })

        return stock_distribution

    def post(self, request, *args, **kwargs) -> Response:
        """
        Handle POST requests to receive request details.
        """

        # Validate the request
        self.validate_request()

        # Extract the products from the request data
        products_data = request.data

        # Get the product details
        product_ids = [p["product"] for p in products_data]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        product_quantities = {p["product"]: p["quantity"] for p in products_data}


        # Get the required materials for the products
        product_materials = self.get_required_materials(product_quantities)

        # Get the stock materials
        stock = self.get_stock_for_materials(product_materials)

        # Prepare the response data
        result = []

        # Iterate through the products and their materials
        for product_id in product_quantities:

            if product_id not in products:
                continue

            product_name = products[product_id].name
            product_qty = product_quantities[product_id]
            current_product_materials = []

            # Iterate through the materials for the current product
            for material_list in product_materials.values():
                for product_material in material_list:
                    if product_material.product_id == product_id:
                        quantity = product_material.quantity

                        # Get the stock distribution for the material
                        stock_distribution = self.get_stock_distribution(stock, product_material.material, quantity)

                        current_product_materials.extend(stock_distribution)

            # Add the product details to the result
            result.append({
                "product_name": product_name,
                "product_qty": product_qty,
                "product_materials": current_product_materials
            })


        return Response({"result": result})