from messages.order_message import OrderMessage


class OrderAgent:
    def create_order(
        self,
        order_id: str,
        priority: str,
        required_capability: str,
        deadline_minutes: int,
        quality_requirement: str,
    ) -> OrderMessage:
        """Create and validate a new urgent production order."""

        order = OrderMessage(
            order_id=order_id,
            priority=priority,
            required_capability=required_capability,
            deadline_minutes=deadline_minutes,
            quality_requirement=quality_requirement,
        )

        print(f"Order Agent created order {order.order_id}.")
        return order

    def push_order(self, order: OrderMessage, coordinator):
        """Push the new order to the Coordinator Agent."""

        print(
            f"Order Agent pushed order {order.order_id} "
            "to the Coordinator Agent."
        )

        return coordinator.handle_order(order)