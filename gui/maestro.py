from nicegui import ui

@ui.page('/')
def main_page():
    ui.label('🧪 Lab Acquisition Control Panel')
    ui.button('▶️ Start Acquisition', on_click=lambda: ui.notify('✅ Acquisition started!'))

ui.run()
