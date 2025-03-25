from math import ceil
from typing import Any

from fastapi import HTTPException
from jinja2 import Environment
from jinjasql import JinjaSql

from . import MySQLStorage

JINJA2_ENV = Environment(extensions=['jinja2.ext.loopcontrols'], autoescape=True)
JINJA2_ENV.filters['is_in'] = lambda m: m.endswith('_in')
JINJA2_ENV.filters['is_like'] = lambda m: m.endswith('_like')
JINJA2_ENV.filters['is_lt'] = lambda m: m.endswith('_lt')
JINJA2_ENV.filters['is_gt'] = lambda m: m.endswith('_gt')
JINJA2_ENV.filters['is_le'] = lambda m: m.endswith('_le')
JINJA2_ENV.filters['is_ge'] = lambda m: m.endswith('_ge')

JINJA2_ENV.filters['strip_action'] = lambda m: m.rsplit('_', 1)[0]


class SQLQueryUtil:
    ENV = JinjaSql(env=JINJA2_ENV, param_style='pyformat')

    @classmethod
    async def apply_query_filters(
        cls,
        query: str,
        filters: dict[str, Any],
        storage: MySQLStorage,
        page: int = 1,
        items_per_page: int = 100,
    ) -> tuple[str, dict, int]:
        """
        Apply filters to SQL query.
        :param query: SQL query.
        :param filters: Query filters.
        :param storage: MySQLStorage instance.
        :param page: Current page number.
        :param items_per_page: Number of items per page.
        :return: Filtered SQL query.
        """
        if any(
            filters[x]
            and any(
                filters.get(f'{x}_{y}') for y in ('in', 'like', 'lt', 'gt', 'le', 'ge')
            )
            for x in filters
        ):
            raise HTTPException(
                status_code=400,
                detail='Same filter may not be provided in multiple forms',
            )

        new_query, args = cls.ENV.prepare_query(
            query
            + '''
            {% if not where_in_query %}
                WHERE 1
            {% endif %}
            {% for filter_name, filter_value in filters.items() %}
                {% if filter_value == None %}
                    {% continue %}
                {% elif filter_name | is_in %}
                    AND {{ filter_name | strip_action | sqlsafe }} IN {{ filter_value | inclause }}
                {% elif filter_name | is_like %}
                    AND {{ filter_name | strip_action | sqlsafe }} LIKE {{ '%' ~ filter_value ~ '%' }}
                {% elif filter_name | is_lt %}
                    AND {{ filter_name | strip_action | sqlsafe }} < {{ filter_value }}
                {% elif filter_name | is_gt %}
                    AND {{ filter_name | strip_action | sqlsafe }} > {{ filter_value }}
                {% elif filter_name | is_le %}
                    AND {{ filter_name | strip_action | sqlsafe }} <= {{ filter_value }}
                {% elif filter_name | is_ge %}
                    AND {{ filter_name | strip_action | sqlsafe }} >= {{ filter_value }}
                {% else %}
                    AND {{ filter_name | sqlsafe }} = {{ filter_value }}
                {% endif %}
            {% endfor %}
            LIMIT {{ limit }}
            OFFSET {{ offset }}
            ''',
            {
                'filters': filters,
                'where_in_query': 'WHERE' in query,
                'offset': (page - 1) * items_per_page,
                'limit': items_per_page,
            },
        )
        return (
            new_query,
            args,
            await SQLQueryUtil.count_pages(query, storage, filters, items_per_page),
        )

    @classmethod
    async def count_pages(
        cls,
        query: str,
        storage: MySQLStorage,
        filters: dict[str, Any],
        items_per_page: int = 100,
    ) -> int:
        """
        Count total available pages.
        :param query: SQL query.
        :param storage: MySQLStorage instance.
        :param filters: Query filters.
        :param items_per_page: Number of items per page.
        :return: Number of available pages.
        """
        new_query, args = cls.ENV.prepare_query(
            query
            + '''
            {% if not where_in_query %}
                WHERE 1
            {% endif %}
            {% for filter_name, filter_value in filters.items() %}
                {% if filter_value == None %}
                    {% continue %}
                {% elif filter_name | is_in %}
                    AND {{ filter_name | strip_action | sqlsafe }} IN {{ filter_value | inclause }}
                {% elif filter_name | is_like %}
                    AND {{ filter_name | strip_action | sqlsafe }} LIKE {{ '%' ~ filter_value ~ '%' }}
                {% elif filter_name | is_lt %}
                    AND {{ filter_name | strip_action | sqlsafe }} < {{ filter_value }}
                {% elif filter_name | is_gt %}
                    AND {{ filter_name | strip_action | sqlsafe }} > {{ filter_value }}
                {% elif filter_name | is_le %}
                    AND {{ filter_name | strip_action | sqlsafe }} <= {{ filter_value }}
                {% elif filter_name | is_ge %}
                    AND {{ filter_name | strip_action | sqlsafe }} >= {{ filter_value }}
                {% else %}
                    AND {{ filter_name | sqlsafe }} = {{ filter_value }}
                {% endif %}
            {% endfor %}
            ''',
            {
                'where_in_query': 'WHERE' in query,
                'filters': filters,
            },
        )
        return max(ceil((await storage.check(new_query, args)) / items_per_page), 1)
