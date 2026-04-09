import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat, FSInputFile

from FileStoreMIETBot import (
    cmd_start,
    cmd_help,
    cmd_files,
    cmd_myfiles,
    cmd_get,
    cmd_del,
    register_user,
    files_metadata
)


@pytest.fixture(autouse=True)
def clean_files_metadata():
    """Очищаем метаданные файлов перед каждым тестом"""
    original = files_metadata.copy()
    yield
    files_metadata.clear()
    files_metadata.update(original)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.full_name = "Тестовый Пользователь"
    return user


@pytest.fixture
def mock_message(mock_user):
    msg = MagicMock(spec=Message)
    msg.from_user = mock_user
    msg.chat = MagicMock(spec=Chat)
    msg.chat.id = 123456789
    msg.text = "/start"
    msg.answer = AsyncMock()
    msg.answer_document = AsyncMock()
    return msg


# Базовые команды

@pytest.mark.asyncio
async def test_cmd_start(mock_message):
    await cmd_start(mock_message)
    mock_message.answer.assert_called_once()
    text = mock_message.answer.call_args[0][0]
    assert "Привет" in text
    assert "Тестовый Пользователь" in text


@pytest.mark.asyncio
async def test_cmd_help(mock_message):
    mock_message.text = "/help"
    from FileStoreMIETBot import cmd_help
    await cmd_help(mock_message)

    text = mock_message.answer.call_args[0][0]
    assert all(cmd in text for cmd in ["/start", "/help", "/files", "/myfiles", "/get", "/del"])


@pytest.mark.asyncio
async def test_cmd_files_empty(mock_message):
    """Тест /files когда нет файлов"""
    mock_message.text = "/files"
    from FileStoreMIETBot import cmd_files
    await cmd_files(mock_message)

    text = mock_message.answer.call_args[0][0].lower()
    assert "пока нет" in text or "нет загруженных" in text


@pytest.mark.asyncio
async def test_cmd_files_with_data(mock_message):
    """Тест /files когда есть файлы"""
    files_metadata[111] = {
        "id": 111,
        "original_name": "document.pdf",
        "file_path": "uploads/111_document.pdf",
        "uploader_id": 123456789,
        "upload_time": "2026-04-09",
        "file_size": 2048000
    }

    mock_message.text = "/files"
    from FileStoreMIETBot import cmd_files
    await cmd_files(mock_message)

    text = mock_message.answer.call_args[0][0]
    assert "111" in text
    assert "document.pdf" in text


#Мои файлы

@pytest.mark.asyncio
async def test_cmd_myfiles_no_files(mock_message):
    mock_message.text = "/myfiles"
    from FileStoreMIETBot import cmd_myfiles
    await cmd_myfiles(mock_message)

    text = mock_message.answer.call_args[0][0].lower()
    assert any(word in text for word in ["нет", "пока", "пусто"])


@pytest.mark.asyncio
async def test_cmd_myfiles_with_files(mock_message):
    files_metadata[222] = {
        "id": 222,
        "original_name": "my_report.pdf",
        "file_path": "uploads/222_report.pdf",
        "uploader_id": 123456789,
        "upload_time": "2026-04-09",
        "file_size": 3145728
    }

    mock_message.text = "/myfiles"
    from FileStoreMIETBot import cmd_myfiles
    await cmd_myfiles(mock_message)

    text = mock_message.answer.call_args[0][0]
    assert "222" in text
    assert "my_report.pdf" in text


#Удаление файла

@pytest.mark.asyncio
async def test_cmd_del_own_file(mock_message):
    """Удаление своего файла"""
    file_id = 333
    files_metadata[file_id] = {
        "id": file_id,
        "original_name": "to_delete.pdf",
        "file_path": "uploads/333_to_delete.pdf",
        "uploader_id": 123456789,
        "upload_time": "2026-04-09",
        "file_size": 1024
    }

    mock_message.text = f"/del {file_id}"
    from FileStoreMIETBot import cmd_del
    await cmd_del(mock_message)

    mock_message.answer.assert_called_once()
    text = mock_message.answer.call_args[0][0]
    assert "успешно удалён" in text.lower()
    assert str(file_id) in text
    assert file_id not in files_metadata


@pytest.mark.asyncio
async def test_cmd_del_foreign_file(mock_message):
    """Попытка удалить чужой файл"""
    file_id = 444
    files_metadata[file_id] = {
        "id": file_id,
        "original_name": "foreign.pdf",
        "file_path": "uploads/444_foreign.pdf",
        "uploader_id": 999999999,
        "upload_time": "2026-04-09",
        "file_size": 1024
    }

    mock_message.text = f"/del {file_id}"
    from FileStoreMIETBot import cmd_del
    await cmd_del(mock_message)

    text = mock_message.answer.call_args[0][0]
    assert "не твой файл" in text.lower() or "не можешь" in text.lower()


#Запрос файла (/get)

@pytest.mark.asyncio
async def test_cmd_get_foreign_file(mock_message):
    """Запрос чужого файла — должен отправить запрос владельцу"""
    file_id = 666
    files_metadata[file_id] = {
        "id": file_id,
        "original_name": "secret.pdf",
        "file_path": "uploads/666_secret.pdf",
        "uploader_id": 999999999,   
        "upload_time": "2026-04-09",
        "file_size": 1024000
    }

    mock_message.text = f"/get {file_id}"
    from FileStoreMIETBot import cmd_get

    with patch('FileStoreMIETBot.bot.send_message', new=AsyncMock()) as mock_send:
        await cmd_get(mock_message)
        mock_send.assert_called_once()

    text = mock_message.answer.call_args[0][0]
    assert "запрос отправлен" in text.lower()