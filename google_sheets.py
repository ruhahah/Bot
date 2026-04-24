import gspread
import gspread_asyncio

import logging

logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    def __init__(self, credentials_path: str = "credentials.json"):
        self.credentials_path = credentials_path
        self._client = None
        self._spreadsheet = None

    async def authorize(self):
        if self._client is None:
            agcm = gspread_asyncio.AsyncioGspreadClientManager(
                lambda: gspread.service_account(filename=self.credentials_path)
            )
            self._client = await agcm.authorize()
        return self._client

    async def open_spreadsheet(self, key: str = None, title: str = None):
        client = await self.authorize()
        if key:
            self._spreadsheet = await client.open_by_key(key)
        elif title:
            self._spreadsheet = await client.open(title)
        else:
            raise ValueError("Either key or title must be provided")
        return self._spreadsheet

    async def get_worksheet(self, index: int = 0):
        if self._spreadsheet is None:
            raise ValueError("Spreadsheet not opened. Call open_spreadsheet first.")
        worksheet = await self._spreadsheet.get_worksheet(index)
        return worksheet

    async def add_lesson_record(
        self,
        student_name: str,
        username: str,
        day: str,
        time: str,
        worksheet_index: int = 0,
    ) -> None:
        if self._spreadsheet is None:
            raise ValueError("Spreadsheet not opened. Call open_spreadsheet first.")

        worksheet = await self.get_worksheet(worksheet_index)
        
        # Find first free row (first column is empty)
        values = await worksheet.get_values()
        first_free_row = len(values) + 1
        
        # Write data to the first free row
        await worksheet.update_cell(first_free_row, 1, student_name)
        await worksheet.update_cell(first_free_row, 2, username)
        await worksheet.update_cell(first_free_row, 3, day)
        await worksheet.update_cell(first_free_row, 4, time)
        
        logger.info(
            "Added lesson record to Google Sheets: %s (%s) - %s %s (row %d)",
            student_name,
            username,
            day,
            time,
            first_free_row,
        )


# Global instance
_sheets_manager = None


async def get_sheets_manager(credentials_path: str = "credentials.json") -> GoogleSheetsManager:
    global _sheets_manager
    if _sheets_manager is None:
        _sheets_manager = GoogleSheetsManager(credentials_path)
    return _sheets_manager


async def add_lesson_record(
    student_name: str,
    username: str,
    day: str,
    time: str,
    spreadsheet_key: str = None,
    spreadsheet_title: str = None,
    credentials_path: str = "credentials.json",
) -> None:
    manager = await get_sheets_manager(credentials_path)
    await manager.open_spreadsheet(key=spreadsheet_key, title=spreadsheet_title)
    await manager.add_lesson_record(student_name, username, day, time)
