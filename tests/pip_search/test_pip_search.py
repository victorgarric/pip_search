from __future__ import annotations

from pip_search import pip_search


def test_search_initializes_solver_and_calls_ensure_access(mocker) -> None:
    client = mocker.Mock()
    client.get.return_value = mocker.Mock(text="<html></html>")

    solver_cls = mocker.patch("pip_search.pip_search.FastlyChallengeSolver")
    solver_instance = solver_cls.return_value
    solver_instance.ensure_access.return_value = True

    list(pip_search.search("requests", client=client))

    solver_cls.assert_called_once_with(client, base_url=pip_search.CONFIG.base_url)
    solver_instance.ensure_access.assert_called_once_with(
        pip_search.CONFIG.search_url,
        referer=pip_search.CONFIG.search_url,
    )
