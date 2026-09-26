import multiprocessing

from grazer import cli


def _reserve_once(cache_path, queue):
    queue.put(cli._idempotency_reserve("post", "shared", ttl_seconds=60, path=cache_path))


def test_idempotency_reserve_allows_only_one_process_for_same_key(tmp_path):
    cache_path = tmp_path / "idempotency_keys.json"
    queue = multiprocessing.Queue()
    procs = [multiprocessing.Process(target=_reserve_once, args=(cache_path, queue)) for _ in range(2)]

    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join(timeout=5)

    assert all(proc.exitcode == 0 for proc in procs)
    results = [queue.get(timeout=1) for _ in procs]
    assert sorted(results) == [False, True]


def test_run_idempotent_send_rolls_back_failed_pre_send_reservation(tmp_path, monkeypatch):
    cache_path = tmp_path / "idempotency_keys.json"

    original_reserve = cli._idempotency_reserve
    original_forget = cli._idempotency_forget
    monkeypatch.setattr(cli, "_idempotency_reserve", lambda scope, key, ttl: original_reserve(scope, key, ttl, cache_path))
    monkeypatch.setattr(cli, "_idempotency_forget", lambda scope, key, ttl: original_forget(scope, key, ttl, cache_path))

    def failing_send():
        raise RuntimeError("provider failed before send was confirmed")

    try:
        cli._run_idempotent_send("post", "retry-me", 60, failing_send)
    except RuntimeError:
        pass
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("send failure should be re-raised")

    assert original_reserve("post", "retry-me", 60, cache_path) is True
