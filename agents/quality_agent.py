from messages.quality_assessment_request import QualityAssessmentRequest
from messages.quality_assessment_response import QualityAssessmentResponse


class QualityAgent:
    def __init__(self):
        # Simple FMEA knowledge base for the prototype.
        self.fmea_table = {
            "no_warning": {
                "risk_score": 0.0,
                "action": "no quality action required",
            },
            "minor_vibration": {
                "risk_score": 0.3,
                "action": "continue with observation",
            },
            "tool_wear": {
                "risk_score": 0.6,
                "action": "inspect the tool before production",
            },
            "high_temperature": {
                "risk_score": 0.8,
                "action": "perform a quality and maintenance check",
            },
            "spindle_failure": {
                "risk_score": 1.0,
                "action": "block the machine",
            },
        }

    def handle_quality_request(
        self,
        request: QualityAssessmentRequest,
    ) -> QualityAssessmentResponse:
        print(
            f"Quality Agent received an assessment request "
            f"for order {request.order_id}."
        )

        assessments = []

        for machine in request.machine_data:
            machine_id = machine["machine_id"]
            warnings = machine.get("active_warnings", [])

            highest_risk = 0.0
            recommended_action = "no quality action required"

            if not warnings:
                warnings = ["no_warning"]

            for warning in warnings:
                result = self.fmea_table.get(
                    warning,
                    {
                        "risk_score": 0.5,
                        "action": "manual quality inspection required",
                    },
                )

                if result["risk_score"] > highest_risk:
                    highest_risk = result["risk_score"]
                    recommended_action = result["action"]

            # Strict orders use a lower acceptable risk threshold.
            if request.quality_requirement.lower() == "strict":
                is_suitable = highest_risk < 0.5
            else:
                is_suitable = highest_risk < 0.7

            assessments.append(
                {
                    "machine_id": machine_id,
                    "quality_risk_score": highest_risk,
                    "recommended_action": recommended_action,
                    "is_suitable": is_suitable,
                }
            )

        return QualityAssessmentResponse(assessments=assessments)