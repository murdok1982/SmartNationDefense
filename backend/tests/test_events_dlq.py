"""TASK-028 — Idempotencia de publicación y Dead Letter Queue del EventBus."""
from app.core.events import EventBus


async def test_publish_is_idempotent_per_msg_id():
    bus = EventBus()
    assert await bus.publish("c2.alert", {"v": 1}, msg_id="msg-1") is True
    assert await bus.publish("c2.alert", {"v": 1}, msg_id="msg-1") is False
    assert await bus.publish("c2.alert", {"v": 2}, msg_id="msg-2") is True


async def test_failing_consumer_moves_message_to_dlq():
    bus = EventBus()

    async def failing(_payload):
        raise RuntimeError("consumer exploded")

    await bus.subscribe("telemetry", failing)
    assert await bus.publish("telemetry", {"a": 1}, msg_id="msg-3") is True

    assert len(bus.dead_letters) == 1
    entry = bus.dead_letters[0]
    assert entry["subject"] == "telemetry"
    assert entry["attempts"] == bus.MAX_DELIVERY_ATTEMPTS
    assert "consumer exploded" in entry["reason"]


async def test_successful_consumer_does_not_use_dlq():
    bus = EventBus()
    received = []

    async def ok(payload):
        received.append(payload)

    await bus.subscribe("orders", ok)
    await bus.publish("orders", {"id": "o-1"}, msg_id="msg-4")

    assert received == [{"id": "o-1", "msg_id": "msg-4", "subject": "orders"}]
    assert bus.dead_letters == []
