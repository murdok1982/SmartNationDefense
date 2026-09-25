import asyncio
import pytest
from app.core.audit import AuditChain


@pytest.mark.asyncio
class TestAuditChainPersistence:
    async def test_hash_chaining_continuity(self):
        chain = AuditChain()
        event1 = await chain.record("USER_LOGIN", "operator-1", "session:001")
        assert event1["previous_hash"] == "0" * 64
        assert len(event1["hash"]) == 64

        event2 = await chain.record("VIEW_COP", "operator-1", "map:tactical")
        assert event2["previous_hash"] == event1["hash"]
        assert len(event2["hash"]) == 64

        event3 = await chain.record("EXPORT_INTEL", "operator-1", "report:001")
        assert event3["previous_hash"] == event2["hash"]

        # Verify chain integrity
        entries = [event1, event2, event3]
        assert chain.verify_chain(entries) is True

    async def test_tamper_detection(self):
        chain = AuditChain()
        event1 = await chain.record("USER_LOGIN", "operator-1", "session:001")
        event2 = await chain.record("VIEW_COP", "operator-1", "map:tactical")
        entries = [event1, event2]
        assert chain.verify_chain(entries) is True

        # Tampering with details of event1
        tampered_entries = [
            {**event1, "details": {"modified": "illegitimate_injection"}},
            event2,
        ]
        assert chain.verify_chain(tampered_entries) is False

        # Tampering by reordering events
        reordered_entries = [event2, event1]
        assert chain.verify_chain(reordered_entries) is False

    async def test_concurrency_locking(self):
        chain = AuditChain()
        tasks = [
            chain.record("CONCURRENT_EVENT", f"actor-{i}", f"resource-{i}")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        # Verify valid ordering
        for i in range(1, 10):
            assert results[i]["previous_hash"] == results[i - 1]["hash"]
