#!/usr/bin/env python3
"""Showcase for graphes.models.ESQuery."""

from graphes.models import ESQuery, print_qdsl


def build_sample_query() -> dict:
    return {
        "_source": ["doc_id", "doc_type", "name.en", "name.fr"],
        "size": 10,
        "query": {
            "function_score": {
                "score_mode": "multiply",
                "query": {
                    "bool": {
                        "filter": [{"terms": {"doc_type.keyword": ["Course", "Person"]}}],
                        "should": [
                            {"term": {"doc_id.keyword": {"value": "MATH-101", "boost": 10}}},
                            {
                                "multi_match": {
                                    "query": "numerical methods",
                                    "type": "bool_prefix",
                                    "fields": ["name.en", "name.fr"],
                                }
                            },
                        ],
                        "minimum_should_match": 1,
                    }
                },
            }
        },
    }


def main() -> None:
    payload = build_sample_query()

    q = ESQuery.from_dict(
        payload,
        title="ES Query Showcase",
        db="test",
        params={"lang": "en", "token": "super-secret"},
    )

    print("\n=== aligned_qdsl ===")
    print(q.aligned_qdsl())

    print("\n=== canonical_qdsl ===")
    print(q.canonical_qdsl())

    print("\n=== one_line_qdsl ===")
    print(q.one_line_qdsl(max_len=120))

    print("\n=== rich print() ===")
    q.print()

    print("\n=== print_qdsl() compatibility wrapper ===")
    print_qdsl(
        query=q.query,
        params={"api_key": "abc123"},
        db="test",
        title="Wrapper Example",
        show_header=True,
        copyable=True,
    )


if __name__ == "__main__":
    main()
