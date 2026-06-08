"""Per-pixel audit trail — the auditability layer."""

from .audit_trail import AuditPixel, build_audit_trail

__all__ = ["AuditPixel", "build_audit_trail"]
