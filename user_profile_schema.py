DEFAULT_USER_ANSWERS = {
    "target_roles": [],
    "preferred_locations": [],
    "remote_preference": "",
    "salary_expectation": "",
    "work_authorization": "",
    "years_experience_override": None,
    "english_level": "",
    "industries_of_interest": [],
    "must_have_conditions": [],
    "nice_to_have_conditions": [],
    "excluded_roles": [],
    "excluded_companies": [],
    "job_search_mode": "conservative"
}


def merge_user_answers(user_answers: dict | None) -> dict:
    if not user_answers:
        return DEFAULT_USER_ANSWERS.copy()

    merged = DEFAULT_USER_ANSWERS.copy()

    for key in DEFAULT_USER_ANSWERS.keys():
        if key in user_answers:
            merged[key] = user_answers[key]

    return merged