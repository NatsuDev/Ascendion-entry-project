from fastapi import APIRouter, Depends, HTTPException, Path, Query

from generic import dependencies as generic_deps
from generic import models as generic_models
from modules import MySQLStorage, SQLQueryUtil

from . import models

ROUTER = APIRouter(prefix='/products', tags=['Products'])


@ROUTER.get(
    '',
    name='List Products',
    description='List all products',
    responses={
        200: {'model': models.ProductListResponse, 'description': 'Success'},
    },
)
async def _(
    storage: MySQLStorage = Depends(generic_deps.get_storage),
    id_: int | None = Query(default=None, alias='id', gt=0, title='ID filter'),
    id_in: list[int] | None = Query(default=None, min_length=1, title='ID list filter'),
    name: str | None = Query(default=None, title='Name filter'),
    name_in: list[str] | None = Query(
        default=None, min_length=1, title='Name list filter'
    ),
    name_like: str | None = Query(default=None, title='Name alike filter'),
    price_lt: float | None = Query(default=None, title='Price less filter', gt=0),
    price_gt: float | None = Query(default=None, title='Price greater filter', ge=0),
    price_le: float | None = Query(default=None, title='Price less equal filter', gt=0),
    price_ge: float | None = Query(
        default=None, title='Price greater equal filter', gt=0
    ),
    page: int = Query(default=1, title='Page number', gt=0),
    items_per_page: int = Query(
        default=100, title='Number of items per page', gt=0, le=1000
    ),
):
    query, args, total_pages = await SQLQueryUtil.apply_query_filters(
        'SELECT id, name, description, price, image_url FROM products',
        {
            'id': id_,
            'id_in': id_in,
            'name': name,
            'name_in': name_in,
            'name_like': name_like,
            'price_lt': price_lt,
            'price_gt': price_gt,
            'price_le': price_le,
            'price_ge': price_ge,
        },
        storage,
        page,
        items_per_page,
    )

    return models.ProductListResponse(
        items=[models.Product(**i) async for i in storage.select(query, args)],
        page=page,
        items_per_page=items_per_page,
        total_pages=total_pages,
    )


@ROUTER.get(
    '/{id}',
    name='Get Product',
    description='Get a single product',
    responses={
        200: {'model': models.ProductResponse, 'description': 'Success'},
        404: {'model': generic_models.Error404Response, 'description': 'Not Found'},
    },
)
async def _(
    product_id: int = Path(alias='id', title='Product ID', gt=0),
    storage: MySQLStorage = Depends(generic_deps.get_storage),
):
    item = await storage.get(
        'SELECT id, name, description, price, image_url FROM products WHERE id = %s',
        product_id,
    )
    if not item:
        raise HTTPException(status_code=404, detail='Product not found')
    return models.ProductResponse(item=models.Product(**item))


@ROUTER.post(
    '',
    name='Create Product',
    description='Create a single product',
    responses={
        201: {'model': models.ProductResponse, 'description': 'Success'},
    },
    status_code=201,
)
async def _(
    data: models.ProductRequest,
    storage: MySQLStorage = Depends(generic_deps.get_storage),
):
    item_id = await storage.apply(
        'INSERT INTO products (name, description, price, image_url) VALUES (%s, %s, %s, %s)',
        (data.name, data.description, data.price, data.image_url),
    )
    return models.ProductResponse(item=models.Product(id=item_id, **data.model_dump()))


@ROUTER.put(
    '/{id}',
    name='Update Product',
    description='Update a single product',
    responses={
        200: {'model': models.ProductResponse, 'description': 'Success'},
        404: {'model': generic_models.Error404Response, 'description': 'Not Found'},
    },
)
async def _(
    data: models.ProductRequest,
    product_id: int = Path(alias='id', title='Product ID', gt=0),
    storage: MySQLStorage = Depends(generic_deps.get_storage),
):
    if not await storage.check('SELECT id FROM products WHERE id = %s', product_id):
        raise HTTPException(status_code=404, detail='Product not found')

    await storage.apply(
        'UPDATE products SET name = %s, description = %s, price = %s, image_url = %s WHERE id = %s',
        (data.name, data.description, data.price, data.image_url, product_id),
    )
    return models.ProductResponse(item=models.Product(id=product_id, **data.model_dump()))


@ROUTER.delete(
    '/{id}',
    name='Delete Product',
    description='Delete a single product',
    responses={
        200: {'model': models.ProductResponse, 'description': 'Success'},
        404: {'model': generic_models.Error404Response, 'description': 'Not Found'},
    },
)
async def _(
    product_id: int = Path(alias='id', title='Product ID', gt=0),
    storage: MySQLStorage = Depends(generic_deps.get_storage),
):
    item = await storage.get(
        'SELECT id, name, description, price, image_url FROM products WHERE id = %s',
        product_id,
    )
    if not item:
        raise HTTPException(status_code=404, detail='Product not found')

    await storage.apply('DELETE FROM products WHERE id = %s', product_id)

    return models.ProductResponse(item=models.Product(**item))
