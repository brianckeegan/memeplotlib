"""Verify the autouse fixture really blocks real socket use."""

from __future__ import annotations

import socket

import pytest


def test_real_socket_is_blocked():
    """Without @allow_network, opening a TCP socket must fail."""
    pytest_socket = pytest.importorskip("pytest_socket")
    with pytest.raises(pytest_socket.SocketBlockedError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


@pytest.mark.allow_network
def test_real_socket_allowed_with_marker():
    """The opt-out marker should restore TCP socket creation."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.close()
