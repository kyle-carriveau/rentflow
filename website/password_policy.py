import re
from datetime import datetime, timedelta

class PasswordPolicy:
    """
    Enterprise-grade password policy enforcement for RE2.
    Implements comprehensive password strength validation and security features.
    """

    # Password requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    MIN_SPECIAL_CHARS = 1

    # Special characters allowed
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

    # Common weak passwords to reject
    COMMON_WEAK_PASSWORDS = {
        'password', 'password123', '123456789', 'qwerty', 'abc123',
        'password1', 'admin', 'administrator', 'root', 'guest', 'user',
        '12345678', 'iloveyou', 'welcome', 'monkey', 'dragon', 'master',
        'shadow', 'letmein', 'football', 'baseball', 'superman', 'batman'
    }

    @classmethod
    def validate_password_strength(cls, password):
        """
        Validate password against comprehensive strength requirements.
        Returns (is_valid, errors_list)
        """
        errors = []

        if not password:
            errors.append("Password is required")
            return False, errors

        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password cannot exceed {cls.MAX_LENGTH} characters")

        # Character requirements
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        if cls.REQUIRE_SPECIAL_CHARS:
            special_count = sum(1 for char in password if char in cls.SPECIAL_CHARS)
            if special_count < cls.MIN_SPECIAL_CHARS:
                errors.append(f"Password must contain at least {cls.MIN_SPECIAL_CHARS} special character(s): {cls.SPECIAL_CHARS}")

        # Common password check (case insensitive)
        if password.lower() in cls.COMMON_WEAK_PASSWORDS:
            errors.append("Password is too common and easily guessable")

        # Sequential character check
        if cls._has_sequential_chars(password):
            errors.append("Password cannot contain sequential characters (e.g., 'abc', '123')")

        # Repeating character check
        if cls._has_repeating_chars(password):
            errors.append("Password cannot contain more than 2 consecutive identical characters")

        return len(errors) == 0, errors

    @classmethod
    def _has_sequential_chars(cls, password, min_sequence=3):
        """Check for sequential characters like 'abc' or '123'."""
        password_lower = password.lower()

        # Check for alphabetic sequences
        for i in range(len(password_lower) - min_sequence + 1):
            chars = password_lower[i:i+min_sequence]
            if len(chars) == min_sequence:
                # Check if characters are sequential
                if all(ord(chars[j+1]) - ord(chars[j]) == 1 for j in range(len(chars)-1)):
                    return True
                # Check reverse sequential
                if all(ord(chars[j]) - ord(chars[j+1]) == 1 for j in range(len(chars)-1)):
                    return True

        # Check for numeric sequences
        for i in range(len(password) - min_sequence + 1):
            chars = password[i:i+min_sequence]
            if chars.isdigit():
                digits = [int(c) for c in chars]
                # Check ascending sequence
                if all(digits[j+1] - digits[j] == 1 for j in range(len(digits)-1)):
                    return True
                # Check descending sequence
                if all(digits[j] - digits[j+1] == 1 for j in range(len(digits)-1)):
                    return True

        return False

    @classmethod
    def _has_repeating_chars(cls, password, max_repeat=2):
        """Check for excessive character repetition."""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                count += 1
                if count > max_repeat:
                    return True
            else:
                count = 1
        return False

    @classmethod
    def get_password_strength_score(cls, password):
        """
        Calculate password strength score (0-100).
        Returns score and descriptive strength level.
        """
        if not password:
            return 0, "No Password"

        score = 0

        # Base score for length
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10

        # Character variety bonus
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[^a-zA-Z0-9]', password):
            score += 20

        # Penalty for common patterns
        if password.lower() in cls.COMMON_WEAK_PASSWORDS:
            score -= 30
        if cls._has_sequential_chars(password):
            score -= 15
        if cls._has_repeating_chars(password):
            score -= 10

        # Ensure score is within bounds
        score = max(0, min(100, score))

        # Determine strength level
        if score < 30:
            strength = "Very Weak"
        elif score < 50:
            strength = "Weak"
        elif score < 70:
            strength = "Fair"
        elif score < 85:
            strength = "Good"
        else:
            strength = "Strong"

        return score, strength

    @classmethod
    def generate_password_requirements_message(cls):
        """Generate a user-friendly message describing password requirements."""
        requirements = [
            f"At least {cls.MIN_LENGTH} characters long",
            "At least one uppercase letter (A-Z)" if cls.REQUIRE_UPPERCASE else None,
            "At least one lowercase letter (a-z)" if cls.REQUIRE_LOWERCASE else None,
            "At least one number (0-9)" if cls.REQUIRE_DIGITS else None,
            f"At least {cls.MIN_SPECIAL_CHARS} special character(s): {cls.SPECIAL_CHARS}" if cls.REQUIRE_SPECIAL_CHARS else None,
            "No common or easily guessable passwords",
            "No sequential characters (e.g., 'abc', '123')",
            "No more than 2 consecutive identical characters"
        ]

        # Filter out None values
        requirements = [req for req in requirements if req is not None]

        message = "Password Requirements:\n• " + "\n• ".join(requirements)
        return message


class PasswordHistory:
    """
    Track password history to prevent reuse of recent passwords.
    """

    @classmethod
    def add_password_to_history(cls, user_id, password_hash):
        """Add a password hash to user's password history."""
        from . import db
        from .models import PasswordHistoryModel

        # Create new password history entry
        history_entry = PasswordHistoryModel(
            user_id=user_id,
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        db.session.add(history_entry)

        # Clean up old entries (keep only last 5 passwords)
        old_entries = db.session.query(PasswordHistoryModel)\
            .filter_by(user_id=user_id)\
            .order_by(PasswordHistoryModel.created_at.desc())\
            .offset(5)\
            .all()

        for entry in old_entries:
            db.session.delete(entry)

        db.session.commit()

    @classmethod
    def check_password_reuse(cls, user_id, new_password):
        """Check if password has been used recently."""
        from . import db
        from .models import PasswordHistoryModel
        from werkzeug.security import check_password_hash

        recent_passwords = db.session.query(PasswordHistoryModel)\
            .filter_by(user_id=user_id)\
            .order_by(PasswordHistoryModel.created_at.desc())\
            .limit(5)\
            .all()

        for entry in recent_passwords:
            if check_password_hash(entry.password_hash, new_password):
                return True

        return False