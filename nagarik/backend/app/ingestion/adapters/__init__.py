"""
Adapter registry. The pipeline finds the right adapter for a source by `source.adapter_key`.

Adding a new source means: subclass BaseAdapter, register it here.
"""
from app.ingestion.adapters.base import BaseAdapter, FetchedItem
from app.ingestion.adapters.delhi_gov import DelhiGovAdapter
from app.ingestion.adapters.eci import ECIAffidavitsAdapter
from app.ingestion.adapters.mock import MockAdapter
from app.ingestion.adapters.pib import PIBAdapter
from app.ingestion.adapters.prsindia import PRSIndiaAdapter

REGISTRY: dict[str, type[BaseAdapter]] = {
    PIBAdapter.key: PIBAdapter,
    PRSIndiaAdapter.key: PRSIndiaAdapter,
    ECIAffidavitsAdapter.key: ECIAffidavitsAdapter,
    DelhiGovAdapter.key: DelhiGovAdapter,
    MockAdapter.key: MockAdapter,
}


def get_adapter(adapter_key: str) -> BaseAdapter:
    cls = REGISTRY.get(adapter_key)
    if cls is None:
        raise KeyError(f"No adapter registered for key '{adapter_key}'")
    return cls()


__all__ = ["BaseAdapter", "FetchedItem", "REGISTRY", "get_adapter"]
