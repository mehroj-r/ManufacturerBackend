from rest_framework.response import Response
from rest_framework.views import APIView

from app.validators import ProductRequestValidator
from app.services import ProductMaterialService, WarehouseService


class ProductMaterialsAPIView(APIView):
    """
    API view to retrieve product materials.
    """

    def post(self, request, *args, **kwargs) -> Response:
        """
        Handle POST requests to receive request details.
        """
        # Validate the request
        ProductRequestValidator.validate_product_request(request.data)

        # Extract the products from the request data
        products_data = request.data

        # Get the product details
        product_ids = [p["product"] for p in products_data]
        product_quantities = {p["product"]: p["quantity"] for p in products_data}

        # Get products by IDs
        products = ProductMaterialService.get_products_by_ids(product_ids)

        # Get the required materials for the products
        product_materials = ProductMaterialService.get_required_materials(product_quantities)

        # Get the warehouse stock for materials
        material_ids = list(product_materials.keys())
        stock = WarehouseService.get_stock_for_materials(material_ids)

        # Prepare the response data
        result = self._prepare_result(products, product_quantities, product_materials, stock)

        return Response({"result": result})

    def _prepare_result(self, products, product_quantities, product_materials, stock):
        """
        Prepare the response result.

        :param products: Dictionary mapping product IDs to Product objects.
        :param product_quantities: Dictionary mapping product IDs to quantities.
        :param product_materials: Dictionary mapping material IDs to lists of ProductMaterial objects.
        :param stock: Dictionary mapping material IDs to lists of Warehouse objects.
        :return: List of dictionaries containing product details.
        """
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
                        stock_distribution = WarehouseService.get_stock_distribution(
                            stock,
                            product_material.material,
                            quantity
                        )

                        current_product_materials.extend(stock_distribution)

            # Add the product details to the result
            result.append({
                "product_name": product_name,
                "product_qty": product_qty,
                "product_materials": current_product_materials
            })

        return result