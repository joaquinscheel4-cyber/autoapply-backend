from user_profile_schema import merge_user_answers


def get_profile_value(profile: dict, key: str, default=None):
    value = profile.get(key, {})
    if isinstance(value, dict):
        return value.get("value", default)
    return value if value is not None else default


def build_application_profile(parsed_profile: dict, user_answers: dict | None) -> dict:
    answers = merge_user_answers(user_answers)

    years_experience = get_profile_value(parsed_profile, "years_experience", 0)
    override_years = answers.get("years_experience_override")

    if override_years is not None:
        years_experience = override_years

    final_profile = {
        "personal_info": {
            "name": get_profile_value(parsed_profile, "name"),
            "email": get_profile_value(parsed_profile, "email"),
            "phone": get_profile_value(parsed_profile, "phone"),
            "linkedin": get_profile_value(parsed_profile, "linkedin"),
        },
        "professional_info": {
            "current_role": get_profile_value(parsed_profile, "current_role"),
            "skills": get_profile_value(parsed_profile, "skills", []),
            "languages": get_profile_value(parsed_profile, "languages", []),
            "years_experience": years_experience,
            "seniority": get_profile_value(parsed_profile, "seniority"),
        },
        "job_preferences": {
            "target_roles": answers.get("target_roles", []),
            "preferred_locations": answers.get("preferred_locations", []),
            "remote_preference": answers.get("remote_preference", ""),
            "salary_expectation": answers.get("salary_expectation", ""),
            "industries_of_interest": answers.get("industries_of_interest", []),
            "must_have_conditions": answers.get("must_have_conditions", []),
            "nice_to_have_conditions": answers.get("nice_to_have_conditions", []),
            "excluded_roles": answers.get("excluded_roles", []),
            "excluded_companies": answers.get("excluded_companies", []),
            "job_search_mode": answers.get("job_search_mode", "conservative"),
        },
        "application_answers": {
            "work_authorization": answers.get("work_authorization", ""),
            "english_level": answers.get("english_level", ""),
        }
    }

    return final_profile