from django.db import models


class Product(models.Model):
    """
    Model representing a product.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Material(models.Model):
    """
    Model representing a material for a product.
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ProductMaterial(models.Model):
    """
    Model representing the relationship between a product and its materials.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.FloatField()

    class Meta:
        unique_together = ('product', 'material')

    def __str__(self):
        return f"{self.product.name} - {self.material.name} ({self.quantity})"

class Warehouse(models.Model):
    """
    Model representing a warehouse.
    """
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    remainder = models.FloatField()
    price = models.FloatField()

    def __str__(self):
        return f"{self.material.name} - {self.remainder} units at price of {self.price} each"