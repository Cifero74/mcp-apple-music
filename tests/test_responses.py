from mcp_apple_music.responses import AppleMusicAPIError, clean_params, structured_response


def test_structured_response_preserves_raw_payload_and_next_link():
    payload = structured_response(
        method="get",
        path="/me/library/songs",
        params={"limit": 10, "offset": 0, "include": None},
        payload={
            "data": [{"id": "i.1"}],
            "meta": {"total": 20},
            "next": "/v1/me/library/songs?offset=10",
        },
    )

    assert payload["request"] == {
        "method": "GET",
        "path": "/me/library/songs",
        "params": {"limit": 10, "offset": 0},
    }
    assert payload["data"] == [{"id": "i.1"}]
    assert payload["next"] == "/v1/me/library/songs?offset=10"
    assert payload["raw"]["meta"] == {"total": 20}


def test_clean_params_keeps_falsey_values():
    assert clean_params({"empty": "", "zero": 0, "false": False, "none": None}) == {
        "empty": "",
        "zero": 0,
        "false": False,
    }


def test_api_error_string_includes_request_context():
    error = AppleMusicAPIError(
        method="GET",
        path="/me/storefront",
        status_code=401,
        message="Unauthorized",
    )

    assert str(error) == "GET /me/storefront failed with HTTP 401: Unauthorized"
