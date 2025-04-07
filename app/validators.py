from rest_framework.exceptions import ValidationError
from typing import Dict, List, Any


class ProductRequestValidator:
    """
    Validator for product-related requests.
    """

    @staticmethod
    def validate_product_request(data: List[Dict[str, Any]]) -> None:
        """
        Validates the product request data.

        :param data: The request data to validate.
        :raises ValidationError: If the request data is invalid.
        """

        # Check if the data is provided
        if not data:
            raise ValidationError({"error": "No data provided."})

        # Check if products are provided
        if not isinstance(data, list) or len(data) == 0:
            raise ValidationError({"error": "No products provided."})

        # Validate each product entry
        for product in data:
            if not isinstance(product, dict):
                raise ValidationError({"error": "Invalid product data."})

            if "product" not in product or "quantity" not in product:
                raise ValidationError({"error": "Request must include 'product' and 'quantity'."})

            if not isinstance(product["product"], int):
                raise ValidationError({"error": "Product ID must be an integer."})

            if not isinstance(product["quantity"], (int, float)):
                raise ValidationError({"error": "Quantity must be a number."})