from messages.maintenance_assessment_request import (
    MaintenanceAssessmentRequest,
)
from messages.maintenance_assessment_response import (
    MaintenanceAssessmentResponse,
)


class MaintenanceAgent:
    CRITICAL_WARNINGS = {
        "spindle_failure",
        "motor_failure",
        "emergency_stop",
        "severe_overheating",
    }

    def __init__(
        self,
        machine_id: str,
        maintenance_condition: float,
        active_warnings: list[str],
    ):
        self.machine_id = machine_id
        self.maintenance_condition = maintenance_condition
        self.active_warnings = active_warnings

    def handle_maintenance_request(
        self,
        request: MaintenanceAssessmentRequest,
    ) -> MaintenanceAssessmentResponse:
        print(
            f"Maintenance Agent assessed machine {self.machine_id}."
        )

        has_critical_warning = any(
            warning in self.CRITICAL_WARNINGS
            for warning in self.active_warnings
        )

        if self.maintenance_condition < 0.5 or has_critical_warning:
            availability_status = "blocked"
            maintenance_action = "immediate maintenance required"

        elif self.maintenance_condition < 0.7:
            availability_status = "risky"
            maintenance_action = "schedule maintenance"

        else:
            availability_status = "available"
            maintenance_action = "none"

        return MaintenanceAssessmentResponse(
            assessments=[
                {
                    "machine_id": self.machine_id,
                    "availability_status": availability_status,
                    "maintenance_action_required": maintenance_action,
                }
            ]
        )