"""Keyword-based fallback for classifying support tickets."""


def decide(ticket: dict[str, str]) -> dict[str, str | bool]:
    """Classify a ticket with ordered keyword rules as an API fallback."""
    text = f"{ticket['subject']} {ticket['body']}".lower()

    has_credential = any(
        term in text
        for term in ("token", "credential", "api key", "secret key", "password")
    )
    has_exposure_action = any(
        term in text
        for term in (
            "leak",
            "expos",
            "pasted",
            "posted",
            "committed",
            "published",
            "stolen",
            "compromis",
        )
    )
    has_live_or_public_context = any(
        term in text
        for term in (
            "active",
            "public",
            "production",
            "someone may be using",
            "using it right now",
        )
    )
    explicit_nonincident = any(
        phrase in text
        for phrase in (
            "no token actually leaked",
            "no token leaked",
            "no live credential",
            "no credential was exposed",
            "no customer data was exposed",
            "nothing actually leaked",
            "no real security incident",
            "nothing was exposed",
        )
    )

    suspicious_login = any(
        phrase in text
        for phrase in ("suspicious login", "unrecognized login", "unauthorized login")
    )
    login_not_mine = any(
        phrase in text
        for phrase in ("not me", "wasn't me", "was not me", "did not make this login")
    )
    account_compromise = any(
        phrase in text
        for phrase in (
            "account compromised",
            "account was compromised",
            "account hacked",
            "account was hacked",
            "account takeover",
            "unauthorized access",
        )
    ) or (suspicious_login and login_not_mine)

    customer_data_exposure = any(
        phrase in text
        for phrase in (
            "customer data leaked",
            "customer data exposed",
            "customer records exposed",
            "personal data leaked",
            "personal data exposed",
            "data breach",
        )
    )
    credential_exposure = (
        has_credential and has_exposure_action and has_live_or_public_context
    ) or any(
        phrase in text
        for phrase in (
            "leaked credential",
            "leaked credentials",
            "credential leaked",
            "credentials leaked",
            "token exposed",
            "credentials exposed",
        )
    )
    real_security_incident = (
        account_compromise or customer_data_exposure or credential_exposure
    ) and not explicit_nonincident

    if real_security_incident:
        route, action, priority = "safety", "escalate", "urgent"
    else:
        asks_for_data = any(
            term in text
            for term in (
                "usage logs",
                "access history",
                "email address",
                "private data",
                "personal data",
                "credentials",
                "records",
            )
        )
        mentions_another_person = any(
            phrase in text
            for phrase in (
                "coworker's",
                "colleague's",
                "another employee",
                "another person's",
                "someone else's",
                "my coworker",
                "my colleague",
            )
        )
        asks_to_share_data = any(
            phrase in text
            for phrase in ("send me", "give me", "share", "show me", "provide")
        )

        if asks_for_data and mentions_another_person and asks_to_share_data:
            route, action, priority = "privacy", "refuse", "normal"
        else:
            requests_privacy_action = any(
                term in text
                for term in (
                    "delete",
                    "deletion",
                    "erase",
                    "remove my",
                    "export",
                    "send me a copy",
                    "copy of all",
                    "correct",
                    "rectify",
                )
            )
            concerns_own_data = any(
                phrase in text
                for phrase in (
                    "personal data",
                    "my data",
                    "data about me",
                    "data you hold about me",
                    "information you hold about me",
                    "my information",
                )
            )
            asks_privacy_policy = any(
                phrase in text
                for phrase in ("privacy policy", "retention policy", "retention terms")
            )

            if requests_privacy_action and concerns_own_data:
                route, action, priority = "privacy", "verify_identity", "normal"
            elif asks_privacy_policy:
                route, action, priority = "privacy", "reply", "normal"
            else:
                account_change = any(
                    phrase in text
                    for phrase in (
                        "reset my password",
                        "reset password",
                        "change my password",
                        "change my email",
                        "change the email address",
                        "update my email",
                        "disable mfa",
                        "turn off mfa",
                        "disable two-factor",
                        "turn off two-factor",
                        "unlock my account",
                        "unlock the account",
                        "unlock my workspace",
                    )
                )
                sign_in_help = any(
                    phrase in text
                    for phrase in (
                        "sign-in",
                        "sign in",
                        "login screen",
                        "login page",
                        "can't log in",
                        "cannot log in",
                        "troubleshooting",
                    )
                )

                if account_change:
                    route, action, priority = "access", "verify_identity", "normal"
                elif sign_in_help:
                    route, action, priority = "access", "reply", "normal"
                elif any(
                    term in text
                    for term in (
                        "invoice",
                        "charged",
                        "charge",
                        "refund",
                        "billing",
                        "plan price",
                        "pricing",
                        "cost",
                    )
                ):
                    route, action, priority = "billing", "reply", "normal"
                else:
                    route, action, priority = "general", "reply", "normal"

    return {
        "id": ticket["id"],
        "route": route,
        "action": action,
        "priority": priority,
        "escalate": action == "escalate",
    }
