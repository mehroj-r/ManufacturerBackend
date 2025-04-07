from typing import Dict, List, Any
from app.models import Product, ProductMaterial, Material, Warehouse


class ProductMaterialService:
    """
    Service for handling product materials operations.
    """

    @staticmethod
    def get_products_by_ids(product_ids: List[int]) -> Dict[int, Product]:
        """
        Get products by their IDs.

        :param product_ids: List of product IDs.
        :return: Dictionary mapping product IDs to Product objects.
        """
        return {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    @staticmethod
    def get_required_materials(product_quantities: Dict[int, int]) -> Dict[int, List[ProductMaterial]]:
        """
        Retrieve the required materials for the given products.

        :param product_quantities: A dictionary mapping product IDs to their quantities.
        :return: A dictionary mapping material IDs to lists of ProductMaterial objects.
        """
        materials = (ProductMaterial.objects.filter(product_id__in=product_quantities.keys())
                     .select_related('material'))
        materials_by_id = {}

        # Group the materials by their IDs
        for material in materials:
            if material.material_id not in materials_by_id:
                materials_by_id[material.material_id] = []

            material.quantity *= product_quantities[material.product_id]
            materials_by_id[material.material_id].append(material)

        return materials_by_id


class WarehouseService:
    """
    Service for handling warehouse operations.
    """

    @staticmethod
    def get_stock_for_materials(material_ids: List[int]) -> Dict[int, List[Warehouse]]:
        """
        Get the stock materials for the required materials.

        :param material_ids: List of material IDs.
        :return: A dictionary mapping material IDs to lists of Warehouse objects.
        """
        stock_data = (Warehouse.objects.filter(material_id__in=material_ids)
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

    @staticmethod
    def get_stock_distribution(
            stock: Dict[int, List[Warehouse]],
            material: Material,
            quantity: float
    ) -> List[Dict[str, Any]]:
        """
        Get the stock for a specific material with given quantity.

        :param stock: A dictionary mapping material IDs to lists of Warehouse objects.
        :param material: The Material object for which to get the stock.
        :param quantity: The quantity of the material needed.
        :return: A list of dictionaries containing warehouse ID, material name, quantity, and price.
        """
        # If the material is not in stock, return appropriate response
        if material.id not in stock:
            return [{
                "warehouse_id": None,
                "material": material.name,
                "qty": quantity,
                "price": None
            }]

        stock_distribution = []
        remaining_quantity = quantity

        for warehouse_item in stock[material.id]:
            # If the stock is empty, skip
            if warehouse_item.remainder <= 0:
                continue

            # If the remainder is less than the quantity needed, take all of it
            # Otherwise, take the quantity needed
            take_quantity = min(warehouse_item.remainder, remaining_quantity)

            stock_distribution.append({
                "warehouse_id": warehouse_item.id,
                "material": material.name,
                "qty": take_quantity,
                "price": warehouse_item.price
            })

            # Update quantity and remainder
            warehouse_item.remainder -= take_quantity
            remaining_quantity -= take_quantity

            # If we've fulfilled the quantity requirement, break out of the loop
            if remaining_quantity <= 0:
                break

        # If there is still quantity left, add it with None values to indicate not enough stock
        if remaining_quantity > 0:
            stock_distribution.append({
                "warehouse_id": None,
                "material": material.name,
                "qty": remaining_quantity,
                "price": None
            })

        return stock_distribution