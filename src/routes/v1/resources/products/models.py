from pydantic import AnyUrl, BaseModel, Field

from generic import models as generic_models


class ProductRequest(BaseModel):
    name: str = Field(min_length=5, max_length=50)
    description: str = Field(
        min_length=10, max_length=65_535
    )  # In accordance with https://mariadb.com/kb/en/text/
    price: float = Field(gt=0)
    image_url: AnyUrl | None = Field(default=None, max_length=250)


class Product(ProductRequest):
    id: int = Field()


class ProductResponse(generic_models.BaseResponse):
    item: Product = Field(title='Product')


class ProductListResponse(generic_models.BasePaginatedResponse):
    items: list[Product] = Field(title='Products')
