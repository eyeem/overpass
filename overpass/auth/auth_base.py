from abc import ABC, abstractmethod


class AuthBase(ABC):
    @abstractmethod
    def get_token(self):
        pass


class MockAuth(AuthBase):
    def get_token(self):
        return "TOKEN"
