"""Re-export every model so `Base.metadata.create_all` sees them."""
from app.models.audit import AuditLog, IngestionRun
from app.models.document import Document, DocumentSnapshot, ExtractedFact, Summary
from app.models.feedback import CitizenFeedback, FeedbackCluster
from app.models.geography import Constituency, District, State
from app.models.manifesto import ManifestoItem, ManifestoProgressUpdate
from app.models.politician import Candidacy, Politician
from app.models.source import Source
from app.models.topic import Topic

__all__ = [
    "AuditLog",
    "Candidacy",
    "CitizenFeedback",
    "Constituency",
    "District",
    "Document",
    "DocumentSnapshot",
    "ExtractedFact",
    "FeedbackCluster",
    "IngestionRun",
    "ManifestoItem",
    "ManifestoProgressUpdate",
    "Politician",
    "Source",
    "State",
    "Summary",
    "Topic",
]
