from models.incident import Incident


class IncidentDocumentBuilder:
    """
    Builds a deterministic textual representation of an Incident.

    The resulting document is used as input to the embedding layer.
    """

    def build(self, incident: Incident) -> str:
        """
        Convert an incident into stable, human-readable text.

        Only available incident information is included.
        """

        sections: list[str] = [
            f"Incident ID: {incident.incident_id}",
            f"Started At: {incident.started_at.isoformat()}",
        ]

        if incident.ended_at is not None:
            sections.append(
                f"Ended At: {incident.ended_at.isoformat()}"
            )

        if incident.dna is not None:
            dna = incident.dna

            self._append_if_present(
                sections,
                "Trigger",
                dna.trigger,
            )
            self._append_if_present(
                sections,
                "Failure",
                dna.failure,
            )
            self._append_if_present(
                sections,
                "Restart Pattern",
                dna.restart_pattern,
            )
            self._append_if_present(
                sections,
                "Readiness",
                dna.readiness,
            )
            self._append_if_present(
                sections,
                "Affected Workload",
                dna.affected_workload,
            )
            self._append_if_present(
                sections,
                "Duration",
                dna.duration,
            )
            self._append_if_present(
                sections,
                "Severity",
                dna.severity,
            )

        if incident.diagnosis is not None:
            diagnosis = incident.diagnosis

            self._append_if_present(
                sections,
                "Diagnosis",
                diagnosis.summary,
            )
            self._append_if_present(
                sections,
                "Root Cause",
                diagnosis.root_cause,
            )

        if incident.resolution is not None:
            resolution = incident.resolution

            self._append_if_present(
                sections,
                "Resolution Action",
                resolution.action,
            )
            self._append_if_present(
                sections,
                "Resolution Description",
                resolution.description,
            )

        if incident.outcome is not None:
            outcome = incident.outcome

            self._append_if_present(
                sections,
                "Outcome Status",
                outcome.status,
            )
            self._append_if_present(
                sections,
                "Outcome Description",
                outcome.description,
            )
            sections.append(
                f"Outcome Verified: {outcome.verified}"
            )

        return "\n".join(sections)

    @staticmethod
    def _append_if_present(
        sections: list[str],
        label: str,
        value: object,
    ) -> None:
        """
        Append a field only when meaningful data is available.
        """

        if value is None:
            return

        if isinstance(value, str) and not value.strip():
            return

        sections.append(f"{label}: {value}")