from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError, ApiError
from sqlalchemy import event

from config.settings import settings
from database.models import Supplier

_es_client: Optional[AsyncElasticsearch] = None


def _get_es_client() -> AsyncElasticsearch:
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(
            settings.elasticsearch_url,
            request_timeout=3,
            max_retries=0,
            retry_on_timeout=False,
            retry_on_status=(),
        )
    return _es_client


SUPPLIERS_INDEX: str = (
    getattr(settings, "elasticsearch_suppliers_index", None) or "suppliers"
)


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if isinstance(value, datetime) else None


def _merge_text_fields(supplier: Supplier) -> str:
    values: List[str] = []
    candidate_fields: List[str] = [
        "full_name",
        "gender",
        "city",
        "area",
        "special_features",
        "brand_experience",
        "additional_notes",
        "hair_color",
        "eye_color",
        "skin_color",
        "instagram_id",
        "phone_number",
        "top_size",
        "bottom_size",
    ]
    for field_name in candidate_fields:
        value = getattr(supplier, field_name, None)
        if value:
            values.append(str(value))

    # JSON list fields
    list_fields: List[str] = ["cooperation_types", "work_styles"]
    for field_name in list_fields:
        list_value = getattr(supplier, field_name, None)
        if isinstance(list_value, list):
            values.extend([str(v) for v in list_value if v])

    return " ".join(values)


def _build_supplier_document(supplier: Supplier) -> Dict[str, Any]:
    return {
        "id": supplier.id,
        "user_id": supplier.user_id,
        "full_name": supplier.full_name,
        "gender": supplier.gender,
        "age": supplier.age,
        "phone_number": supplier.phone_number,
        "instagram_id": supplier.instagram_id,
        "height": supplier.height,
        "weight": supplier.weight,
        "hair_color": supplier.hair_color,
        "eye_color": supplier.eye_color,
        "skin_color": supplier.skin_color,
        "top_size": supplier.top_size,
        "bottom_size": supplier.bottom_size,
        "special_features": supplier.special_features,
        "pricing_data": supplier.pricing_data,
        # فیلدهای مسطح شده برای فیلتر و سورت ساده روی ES
        "price_hourly": (supplier.pricing_data or {}).get("hourly"),
        "price_daily": (supplier.pricing_data or {}).get("daily"),
        "price_per_cloth": (supplier.pricing_data or {}).get("per_cloth"),
        "city": supplier.city,
        "area": supplier.area,
        "cooperation_types": supplier.cooperation_types,
        "work_styles": supplier.work_styles,
        "brand_experience": supplier.brand_experience,
        "additional_notes": supplier.additional_notes,
        "portfolio_photos": supplier.portfolio_photos,
        "search_text": _merge_text_fields(supplier),
        "created_at": _serialize_datetime(supplier.created_at),
        "updated_at": _serialize_datetime(supplier.updated_at),
    }


async def ensure_suppliers_index() -> None:
    es = _get_es_client()
    exists = await es.indices.exists(index=SUPPLIERS_INDEX)
    if not exists:
        await es.indices.create(
            index=SUPPLIERS_INDEX,
            settings={
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "char_filter": {
                            "zwnj_to_space": {
                                "type": "pattern_replace",
                                "pattern": "\u200C",
                                "replacement": " "
                            },
                            "arabic_variants_to_persian": {
                                "type": "mapping",
                                "mappings": [
                                    "\u064A=>\u06CC",  # ARABIC YEH to FARSI YEH
                                    "\u0643=>\u06A9"   # ARABIC KAF to KEHEH
                                ]
                            },
                            "remove_diacritics": {
                                "type": "pattern_replace",
                                "pattern": "[\u064B-\u0652]",
                                "replacement": ""
                            }
                        },
                        "filter": {
                            "persian_edge_ngram": {
                                "type": "edge_ngram",
                                "min_gram": 2,
                                "max_gram": 20
                            }
                        },
                        "analyzer": {
                            "persian_index_analyzer": {
                                "type": "custom",
                                "char_filter": [
                                    "zwnj_to_space",
                                    "arabic_variants_to_persian",
                                    "remove_diacritics"
                                ],
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "arabic_normalization",
                                    "persian_normalization",
                                    "persian_edge_ngram"
                                ]
                            },
                            "persian_search_analyzer": {
                                "type": "custom",
                                "char_filter": [
                                    "zwnj_to_space",
                                    "arabic_variants_to_persian",
                                    "remove_diacritics"
                                ],
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "arabic_normalization",
                                    "persian_normalization"
                                ]
                            }
                        },
                        "normalizer": {
                            "persian_keyword_normalizer": {
                                "type": "custom",
                                "filter": [
                                    "lowercase",
                                    "arabic_normalization",
                                    "persian_normalization"
                                ]
                            }
                        }
                    }
                }
            },
            mappings={
                "dynamic": True,
                "properties": {
                    "search_text": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer"
                    },
                    "full_name": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "normalizer": "persian_keyword_normalizer"
                            }
                        }
                    },
                    "gender": {"type": "keyword"},
                    "age": {"type": "integer"},
                    "phone_number": {"type": "keyword"},
                    "instagram_id": {"type": "keyword", "normalizer": "persian_keyword_normalizer"},
                    "height": {"type": "integer"},
                    "weight": {"type": "integer"},
                    "hair_color": {"type": "keyword", "normalizer": "persian_keyword_normalizer"},
                    "eye_color": {"type": "keyword", "normalizer": "persian_keyword_normalizer"},
                    "skin_color": {"type": "keyword", "normalizer": "persian_keyword_normalizer"},
                    "top_size": {"type": "keyword"},
                    "bottom_size": {"type": "keyword"},
                    "special_features": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer"
                    },
                    "city": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword", "normalizer": "persian_keyword_normalizer"}
                        }
                    },
                    "area": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword", "normalizer": "persian_keyword_normalizer"}
                        }
                    },
                    "cooperation_types": {"type": "keyword", "normalizer": "persian_keyword_normalizer"},
                    "work_styles": {"type": "keyword", "normalizer": "persian_keyword_normalizer"},
                    "brand_experience": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer"
                    },
                    "additional_notes": {
                        "type": "text",
                        "analyzer": "persian_index_analyzer",
                        "search_analyzer": "persian_search_analyzer"
                    },
                    "portfolio_photos": {"type": "keyword"},
                    # قیمت‌های تکی برای کوئری‌پذیری بهتر
                    "price_hourly": {"type": "integer"},
                    "price_daily": {"type": "integer"},
                    "price_per_cloth": {"type": "integer"},
                    "created_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                    "updated_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"}
                }
            },
        )


async def index_supplier_document(supplier: Supplier) -> None:
    es = _get_es_client()
    await es.index(index=SUPPLIERS_INDEX, id=supplier.id, document=_build_supplier_document(supplier), refresh="false")


async def update_supplier_document(supplier: Supplier) -> None:
    es = _get_es_client()
    doc = _build_supplier_document(supplier)
    await es.index(index=SUPPLIERS_INDEX, id=supplier.id, document=doc, refresh="false")


async def delete_supplier_document(supplier_id: int) -> None:
    es = _get_es_client()
    try:
        await es.delete(index=SUPPLIERS_INDEX, id=supplier_id, refresh="false")
    except NotFoundError:
        # Ignore if not found
        return


async def search_suppliers(
    query: Optional[str],
    filters: Optional[Dict[str, Any]] = None,
    from_: int = 0,
    size: int = 10,
    should: Optional[List[Dict[str, Any]]] = None,
    min_should_match: Optional[int] = None,
    sort: Optional[List[Dict[str, Any]]] = None,
    filter_should: Optional[List[Dict[str, Any]]] = None,
    filter_min_should_match: Optional[int] = None,
) -> Dict[str, Any]:
    es = _get_es_client()
    must_clauses: List[Dict[str, Any]] = []
    filter_clauses: List[Dict[str, Any]] = []

    if query:
        must_clauses.append(
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "search_text^5",
                        "full_name^4",
                        "brand_experience^2",
                        "additional_notes^2",
                        "city^2",
                        "area^2"
                    ],
                    "type": "most_fields",
                    "operator": "and",
                    "fuzziness": "AUTO",
                    "analyzer": "persian_search_analyzer"
                }
            }
        )

    if filters:
        for key, value in filters.items():
            if value is None:
                continue
            # Range filter support: value like {"gte": x, "lte": y}
            if isinstance(value, dict) and ("gte" in value or "lte" in value):
                filter_clauses.append({"range": {key: value}})
            elif isinstance(value, list):
                filter_clauses.append({"terms": {key: value}})
            else:
                filter_clauses.append({"term": {key: value}})

    # Ensure 'must' is always a list of clauses
    must_list: List[Dict[str, Any]] = must_clauses if must_clauses else [{"match_all": {}}]
    bool_query: Dict[str, Any] = {
        "must": must_list,
        "filter": filter_clauses,
    }

    if should:
        bool_query["should"] = should
        if min_should_match is not None:
            bool_query["minimum_should_match"] = min_should_match

    body: Dict[str, Any] = {
        "query": {"bool": bool_query},
        "from": from_,
        "size": size,
        "highlight": {
            "fields": {
                "search_text": {},
                "full_name": {},
                "brand_experience": {},
                "additional_notes": {},
                "city": {},
                "area": {}
            },
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"]
        }
    }

    if sort:
        body["sort"] = sort

    # If there are OR-ed filters that must be satisfied by at least one, add them as a bool filter
    if filter_should:
        or_filter: Dict[str, Any] = {"bool": {"should": filter_should}}
        if filter_min_should_match is not None:
            or_filter["bool"]["minimum_should_match"] = filter_min_should_match
        # Append into existing filter list
        if isinstance(body["query"]["bool"]["filter"], list):
            body["query"]["bool"]["filter"].append(or_filter)
        else:
            body["query"]["bool"]["filter"] = [body["query"]["bool"]["filter"], or_filter]

    # Lightweight manual retry for transient 5xx
    last_exc = None
    for attempt in range(2):  # at most 1 retry
        try:
            return await es.search(index=SUPPLIERS_INDEX, body=body)
        except ApiError as e:
            last_exc = e
            status = getattr(e, 'status', None)
            if status in (502, 503, 504) and attempt == 0:
                await asyncio.sleep(0.3)
                continue
            raise
        except Exception as e:
            last_exc = e
            raise
    if last_exc:
        raise last_exc


def _schedule(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        # No running loop; best-effort fallback
        asyncio.run(coro)


def _after_insert(mapper, connection, target: Supplier):
    _schedule(index_supplier_document(target))


def _after_update(mapper, connection, target: Supplier):
    _schedule(update_supplier_document(target))


def _after_delete(mapper, connection, target: Supplier):
    _schedule(delete_supplier_document(target.id))


async def init_elastic_indexing() -> None:
    await ensure_suppliers_index()
    # Register event listeners once
    event.listen(Supplier, "after_insert", _after_insert, propagate=True)
    event.listen(Supplier, "after_update", _after_update, propagate=True)
    event.listen(Supplier, "after_delete", _after_delete, propagate=True)


async def close_elastic() -> None:
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None


async def reindex_all_suppliers(fetch_suppliers_callable) -> None:
    """
    Reindex all suppliers using the provided async callable that returns an
    iterable of Supplier objects. This is useful after changing analyzers.

    fetch_suppliers_callable: async function that yields/returns Supplier objects
    """
    await ensure_suppliers_index()
    es = _get_es_client()
    actions: List[Dict[str, Any]] = []
    async for supplier in fetch_suppliers_callable():
        actions.append({
            "index": {
                "_index": SUPPLIERS_INDEX,
                "_id": supplier.id,
                "document": _build_supplier_document(supplier)
            }
        })
        # flush in chunks
        if len(actions) >= 500:
            await asyncio.gather(*[
                es.index(index=a["index"]["_index"], id=a["index"]["_id"], document=a["index"]["document"]) for a in actions
            ])
            actions.clear()
    if actions:
        await asyncio.gather(*[
            es.index(index=a["index"]["_index"], id=a["index"]["_id"], document=a["index"]["document"]) for a in actions
        ])

