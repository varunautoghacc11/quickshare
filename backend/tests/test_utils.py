import pytest
from app.utils import (
    generate_secure_code,
    sanitize_filename,
    validate_extension,
    get_redis_key,
    validate_code_format,
)


class TestGenerateSecureCode:
    def test_returns_string(self):
        code = generate_secure_code()
        assert isinstance(code, str)

    def test_exactly_six_chars(self):
        code = generate_secure_code()
        assert len(code) == 6

    def test_all_digits(self):
        code = generate_secure_code()
        assert code.isdigit()

    def test_within_valid_range(self):
        code = generate_secure_code()
        assert 0 <= int(code) <= 999999

    def test_zero_padded(self):
        # Run many times to check padding
        for _ in range(100):
            code = generate_secure_code()
            assert len(code) == 6

    def test_bulk_valid_format(self):
        codes = [generate_secure_code() for _ in range(1000)]
        for code in codes:
            assert len(code) == 6
            assert code.isdigit()
            assert 0 <= int(code) <= 999999

    def test_bulk_uniqueness(self):
        codes = [generate_secure_code() for _ in range(1000)]
        # Not all same (statistically impossible if random)
        assert len(set(codes)) > 1


class TestSanitizeFilename:
    def test_normal_filename(self):
        result = sanitize_filename("document.pdf")
        assert "." in result
        assert len(result) > 0

    def test_strips_path(self):
        result = sanitize_filename("/etc/passwd")
        assert "/" not in result
        assert "etc" in result or "passwd" in result

    def test_strips_windows_path(self):
        result = sanitize_filename("C:\\Windows\\system32\\evil.exe")
        assert "\\" not in result

    def test_strips_dot_dot(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result

    def test_replaces_special_chars(self):
        result = sanitize_filename("file name (1).pdf")
        assert " " not in result
        assert "(" not in result

    def test_empty_filename(self):
        result = sanitize_filename("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_long_filename_truncated(self):
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_preserves_extension(self):
        result = sanitize_filename("myfile.docx")
        assert result.endswith(".docx")


class TestValidateExtension:
    def test_accepts_pdf(self):
        assert validate_extension("document.pdf", ["pdf", "txt", "png"]) is True

    def test_accepts_png(self):
        assert validate_extension("image.PNG", ["pdf", "txt", "png"]) is True

    def test_rejects_exe(self):
        assert validate_extension("malware.exe", ["pdf", "txt", "png"]) is False

    def test_rejects_sh(self):
        assert validate_extension("script.sh", ["pdf", "txt", "png"]) is False

    def test_rejects_php(self):
        assert validate_extension("shell.php", ["pdf", "txt", "png"]) is False

    def test_rejects_js(self):
        assert validate_extension("evil.js", ["pdf", "txt", "png"]) is False

    def test_rejects_html(self):
        assert validate_extension("xss.html", ["pdf", "txt", "png"]) is False

    def test_rejects_py(self):
        assert validate_extension("backdoor.py", ["pdf", "txt", "png"]) is False

    def test_case_insensitive(self):
        assert validate_extension("file.PDF", ["pdf"]) is True

    def test_no_extension(self):
        assert validate_extension("noextension", ["pdf", "txt"]) is False


class TestGetRedisKey:
    def test_correct_prefix(self):
        key = get_redis_key("123456")
        assert key == "share:123456"

    def test_rejects_invalid_code(self):
        with pytest.raises(ValueError):
            get_redis_key("abc123")

    def test_rejects_short_code(self):
        with pytest.raises(ValueError):
            get_redis_key("12345")

    def test_rejects_long_code(self):
        with pytest.raises(ValueError):
            get_redis_key("1234567")

    def test_rejects_injection(self):
        with pytest.raises(ValueError):
            get_redis_key("share:123456")


class TestValidateCodeFormat:
    def test_valid_code(self):
        # Should not raise
        validate_code_format("000000")
        validate_code_format("999999")
        validate_code_format("123456")

    def test_rejects_alpha(self):
        with pytest.raises(ValueError):
            validate_code_format("abc123")

    def test_rejects_too_short(self):
        with pytest.raises(ValueError):
            validate_code_format("12345")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError):
            validate_code_format("1234567")

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_code_format("")

    def test_rejects_with_spaces(self):
        with pytest.raises(ValueError):
            validate_code_format("12 456")

    def test_rejects_injection(self):
        with pytest.raises(ValueError):
            validate_code_format("12*456")
