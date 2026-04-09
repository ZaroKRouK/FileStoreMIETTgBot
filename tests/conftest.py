import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Bot, Dispatcher

from FileStoreMIETBot import bot, dp   # ← это главное изменение

@pytest.fixture(scope="session")
def test_bot():
    return bot

@pytest.fixture
def test_dp():
    return dp