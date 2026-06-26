"""Tests for the EventBus — pub/sub, wildcard matching, threading, lifecycle."""
import sys; sys.path.insert(0, '.')
from shared.events.event_bus import EventBus, Event


def test_publish_calls_subscriber():
    bus = EventBus()
    results = []
    bus.subscribe("test.topic", lambda e: results.append(e.payload))
    bus.publish("test.topic", {"msg": "hello"})
    assert len(results) == 1
    assert results[0] == {"msg": "hello"}
    bus.shutdown()


def test_multiple_subscribers_same_topic():
    bus = EventBus()
    r1, r2 = [], []
    bus.subscribe("test.topic", lambda e: r1.append(e.payload.get("id")))
    bus.subscribe("test.topic", lambda e: r2.append(e.payload.get("id")))
    bus.publish("test.topic", {"id": 42})
    assert r1 == [42]
    assert r2 == [42]
    bus.shutdown()


def test_unsubscribe():
    bus = EventBus()
    results = []
    sid = bus.subscribe("test.topic", lambda e: results.append(1))
    bus.unsubscribe(sid)
    bus.publish("test.topic", {})
    assert results == []


def test_wildcard_star():
    bus = EventBus()
    results = []
    bus.subscribe("*", lambda e: results.append(e.topic))
    bus.publish("a.b", {})
    bus.publish("c.d.e", {})
    assert results == ["a.b", "c.d.e"]


def test_wildcard_prefix():
    bus = EventBus()
    results = []
    bus.subscribe("vision.*", lambda e: results.append(e.topic))
    bus.publish("vision.hand.landmarks", {})
    bus.publish("vision.eye.blink", {})
    bus.publish("gesture.event", {})
    assert results == ["vision.hand.landmarks", "vision.eye.blink"]


def test_wildcard_doublestar():
    bus = EventBus()
    results = []
    bus.subscribe("vision.**", lambda e: results.append(e.topic))
    bus.publish("vision", {})
    bus.publish("vision.hand", {})
    bus.publish("vision.hand.landmarks", {})
    assert results == ["vision", "vision.hand", "vision.hand.landmarks"]


def test_exact_match_only():
    bus = EventBus()
    results = []
    bus.subscribe("exact.topic", lambda e: results.append(1))
    bus.publish("exact.topic.extra", {})
    bus.publish("exact", {})
    assert results == []


def test_once_subscription():
    bus = EventBus()
    results = []
    bus.subscribe("test", lambda e: results.append(1), once=True)
    bus.publish("test", {})
    bus.publish("test", {})
    assert results == [1]


def test_event_has_timestamp_and_id():
    bus = EventBus()
    events = []
    bus.subscribe("test", lambda e: events.append(e))
    bus.publish("test", {"k": "v"}, source="src", confidence=0.9)
    e = events[0]
    assert e.topic == "test"
    assert e.source == "src"
    assert e.confidence == 0.9
    assert e.payload == {"k": "v"}
    assert e.event_id != ""
    assert e.timestamp > 0


def test_shutdown_clears():
    bus = EventBus()
    results = []
    bus.subscribe("test", lambda e: results.append(1))
    bus.shutdown()
    bus.publish("test", {})
    assert results == []


def test_subscribe_all():
    bus = EventBus()
    results = []
    bus.subscribe_all(lambda e: results.append(e.topic))
    bus.publish("a", {})
    bus.publish("b.c", {})
    bus.publish("d.e.f", {})
    assert len(results) == 3
    bus.shutdown()
