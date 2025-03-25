import pytest

from modules import MySQLStorage

product_payload_fixture = {
    'name': 'string',
    'description': 'a very long string',
    'price': 1.0,
    'image_url': None,
}


async def create_product(storage: MySQLStorage) -> int:
    return await storage.apply(
        'INSERT INTO products (name, description, price, image_url) VALUES (%s, %s, %s, %s)',
        (
            product_payload_fixture['name'],
            product_payload_fixture['description'],
            product_payload_fixture['price'],
            product_payload_fixture['image_url'],
        ),
    )


@pytest.mark.asyncio
async def test_create_product(app):
    """Test creating a product."""
    async with app as client, client.app.extra['storage'].pool.acquire() as connection:
        storage = MySQLStorage(connection)

        try:
            response = client.post('/v1/products/', json=product_payload_fixture)
            assert response.status_code == 201
            data = response.json()
            assert 'item' in data
            assert data['item']['name'] == product_payload_fixture['name']
        finally:
            await storage.apply('DELETE FROM products')


@pytest.mark.asyncio
async def test_list_products(app):
    """Test listing and filtering products."""
    async with app as client, client.app.extra['storage'].pool.acquire() as connection:
        storage = MySQLStorage(connection)
        await create_product(storage)

        try:
            response = client.get('/v1/products/')
            assert response.status_code == 200
            data = response.json()
            assert len(data['items']) == 1

            response = client.get('/v1/products/', params={'price_gt': 0})
            assert response.status_code == 200
            data = response.json()
            assert len(data['items']) == 1

            response = client.get('/v1/products/', params={'price_gt': 5})
            assert response.status_code == 200
            data = response.json()
            assert len(data['items']) == 0
        finally:
            await storage.apply('DELETE FROM products')


@pytest.mark.asyncio
async def test_update_product(app):
    """Test updating a product."""
    async with app as client, client.app.extra['storage'].pool.acquire() as connection:
        storage = MySQLStorage(connection)

        try:
            product_id = await create_product(storage)

            updated_payload = {**product_payload_fixture, 'name': 'updated string'}
            response = client.put(f'/v1/products/{product_id}', json=updated_payload)
            assert response.status_code == 200
            updated_data = response.json()
            assert updated_data['item']['name'] == 'updated string'
        finally:
            await storage.apply('DELETE FROM products')


@pytest.mark.asyncio
async def test_delete_product(app):
    """Test deleting a product."""
    async with app as client, client.app.extra['storage'].pool.acquire() as connection:
        storage = MySQLStorage(connection)

        try:
            product_id = await create_product(storage)

            response = client.delete(f'/v1/products/{product_id}')
            assert response.status_code == 200
        finally:
            await storage.apply('DELETE FROM products')
