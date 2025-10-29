def test_standardize_challenge_handles_strings_and_fractions():
    from srd_builder.postprocess import standardize_challenge

    monster = {"challenge_rating": "1/2"}
    assert standardize_challenge(monster)["challenge_rating"] == 0.5

    monster = {"challenge_rating": "10"}
    assert standardize_challenge(monster)["challenge_rating"] == 10

    monster = {"challenge_rating": 3.0}
    assert standardize_challenge(monster)["challenge_rating"] == 3
