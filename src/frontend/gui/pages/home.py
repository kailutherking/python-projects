from nicegui import APIRouter, ui

router = APIRouter()


@router.page('/')
def home() -> None:
    with ui.column().classes('items-center w-full gap-6 p-8'):
        ui.label('Odds Scraper').classes('text-4xl font-bold')
        ui.label('NBA odds scraping with always-on EV analysis').classes('text-gray-500')

        with ui.row().classes('gap-4'):
            ui.button(
                'Live Odds', icon='sports_basketball', on_click=lambda: ui.navigate.to('/odds')
            ).props('size=lg')
