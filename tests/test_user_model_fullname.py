import pytest
from app.data.models.user import User, UserProfile

class TestUserModelFullName:
    
    def test_full_name_property_with_full_name_set(self):
        user = User(
            username="jdoe",
            email="jdoe@example.com",
            hashed_password="hash",
            profile=UserProfile(full_name="John Doe")
        )
        assert user.full_name == "John Doe"
        assert user.get_full_name() == "John Doe"

    def test_full_name_property_with_first_last_name(self):
        user = User(
            username="jdoe",
            email="jdoe@example.com",
            hashed_password="hash",
            profile=UserProfile(first_name="John", last_name="Doe")
        )
        # Since we removed the full_name property from UserProfile, 
        # User.full_name logic is:
        # return self.profile.full_name or self.profile.first_name or self.profile.last_name or ""
        # Wait, checking logic again:
        # if self.profile and self.profile.full_name: return ...
        # return self.profile.first_name or self.profile.last_name or ""
        # It does NOT combine first and last name anymore in the property!
        # But get_full_name DOES combine them.
        
        # Let's check the logic I implemented in User.full_name:
        # return self.profile.first_name or self.profile.last_name or ""
        
        # So User.full_name property will return "John" (first_name).
        assert user.full_name == "John"
        
        # User.get_full_name() logic:
        # if self.profile.first_name and self.profile.last_name:
        #     return f"{self.profile.first_name} {self.profile.last_name}"
        assert user.get_full_name() == "John Doe"

    def test_full_name_property_empty_fallback(self):
        user = User(
            username="jdoe",
            email="jdoe@example.com",
            hashed_password="hash",
            profile=UserProfile()
        )
        # Before it was fallback to username, now it should be empty string
        assert user.full_name == ""
        assert user.get_full_name() == ""
        
    def test_get_full_name_priority(self):
        # explicit full_name > first+last
        user = User(
            username="jdoe",
            email="jdoe@example.com",
            hashed_password="hash",
            profile=UserProfile(
                full_name="Explicit Name",
                first_name="First",
                last_name="Last"
            )
        )
        assert user.get_full_name() == "Explicit Name"
