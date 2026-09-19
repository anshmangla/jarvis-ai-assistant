import flet as ft
from assistant.agent import Agent
from utils.logger import logger

def main(page: ft.Page):
    page.title = "J.A.R.V.I.S. Command Center"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 800
    page.window_height = 800
    
    logger.info("Initializing Agent for UI...")
    agent = Agent()
    
    chat_list = ft.ListView(
        expand=True, 
        spacing=15,
        auto_scroll=True
    )
    
    # Optional: load recent history to populate UI
    recent = agent.memory.get_recent_history(turns=5)
    if recent:
        chat_list.controls.append(
            ft.Text("Loaded recent conversation history...", color=ft.Colors.GREY_500, italic=True)
        )
    
    user_input = ft.TextField(
        hint_text="Type a command for Jarvis...",
        expand=True,
        border_radius=20,
        filled=True,
        on_submit=lambda e: send_message_click(e)
    )
    
    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.BLUE_200,
        on_click=lambda e: send_message_click(e)
    )
    
    progress_bar = ft.ProgressBar(width=400, color="amber", bgcolor="#eeeeee")
    progress_row = ft.Row([progress_bar, ft.Text("Thinking...", color=ft.Colors.GREY_400)], visible=False, alignment=ft.MainAxisAlignment.CENTER)

    def send_message_click(e):
        text = user_input.value.strip()
        if not text:
            return
            
        # Disable input
        user_input.value = ""
        user_input.disabled = True
        send_btn.disabled = True
        progress_row.visible = True
        
        # Add User Message to Chat
        chat_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(text, weight=ft.FontWeight.W_500, size=16),
                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_200, size=30),
                ], alignment=ft.MainAxisAlignment.END),
                padding=10
            )
        )
        page.update()
        
        # Process via Agent (blocks the event thread, but Flet runs events in background threads automatically)
        try:
            response = agent.process_command(text)
        except Exception as ex:
            response = f"Error processing command in agent: {ex}"
            
        # Add Assistant Message to Chat (Using Markdown for rich text)
        chat_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.PURPLE_300, size=30),
                    ft.Markdown(response, selectable=True, extension_set="gitHubWeb", fit_content=True),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
                padding=10,
                bgcolor=ft.Colors.SURFACE_VARIANT,
                border_radius=10
            )
        )
        
        # Re-enable input
        user_input.disabled = False
        send_btn.disabled = False
        progress_row.visible = False
        page.update()
        user_input.focus()

    # Build View
    page.add(
        ft.Row([
            ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, color=ft.Colors.PURPLE_400),
            ft.Text("J.A.R.V.I.S.", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200)
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        chat_list,
        progress_row,
        ft.Row([user_input, send_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )
    
    # Focus input on start
    page.update()
    user_input.focus()

if __name__ == "__main__":
    ft.app(target=main)
