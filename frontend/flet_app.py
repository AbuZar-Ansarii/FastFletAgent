import flet as ft
import requests
import uuid

API_URL = "http://localhost:8000/chat"


def main(page: ft.Page):
    page.title = "FALCON AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.padding = 0

    session_id = str(uuid.uuid4())

    # -------------------------
    # Header
    # -------------------------

    header = ft.Container(
        bgcolor="#111827",
        padding=15,
        content=ft.Row(
            [
                ft.CircleAvatar(
                    content=ft.Text("🦅"),
                    bgcolor="#1f2937",
                ),
                ft.Text(
                    "FALCON AI",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                ),
                ft.Container(expand=True),
                ft.Dropdown(
                    width=220,
                    value="💭General Chat",
                    options=[
                        ft.dropdown.Option("💭General Chat"),
                        ft.dropdown.Option("🤖AI Tutor"),
                        ft.dropdown.Option("💪Fitness Coach"),
                        ft.dropdown.Option("🎓Career Advisor"),
                        ft.dropdown.Option("👨‍🔬Dr. APJ Abdul Kalam"),
                        ft.dropdown.Option("👴🏻Mahatma Gandhi"),
                    ],
                    border_radius=10,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    character_dropdown = header.content.controls[-1]

    # -------------------------
    # Chat Area
    # -------------------------

    chat_column = ft.Column(
        expand=True,
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )

    def create_message(text, is_user):
        avatar = ft.CircleAvatar(
            content=ft.Text("👤" if is_user else "🤖"),
            bgcolor="#2563eb" if is_user else "#374151",
        )

        bubble = ft.Container(
            content=ft.Text(text, selectable=True, size=14),
            padding=15,
            bgcolor="#2563eb" if is_user else "#1f2937",
            border_radius=20,
            width=500,
        )

        row = ft.Row(
            [
                bubble if is_user else avatar,
                avatar if is_user else bubble,
            ],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
        )

        return row

    # -------------------------
    # Send Message
    # -------------------------

    user_input = ft.TextField(
        hint_text="Type your message...",
        expand=True,
        border_radius=20,
        filled=True,
        bgcolor="#1f2937",
        border_color="transparent",
        text_size=14,
        content_padding=15,
    )

    def send_message(e=None):
        nonlocal session_id

        message = user_input.value.strip()
        if not message:
            return

        character_value = character_dropdown.value or "💭General Chat"

        chat_column.controls.append(create_message(message, True))
        user_input.value = ""
        page.update()

        typing = ft.Text("FALCON is typing...", italic=True, color="#9ca3af")
        chat_column.controls.append(typing)
        page.update()

        try:
            response = requests.post(
                API_URL,
                json={
                    "session_id": session_id,
                    "character": character_value,
                    "query": message,
                },
                timeout=120,
            )

            if response.status_code == 200:
                data = response.json()
                session_id = data["session_id"]
                reply = data["response"]
            else:
                reply = f"Backend Error: {response.text}"

        except Exception as ex:
            reply = f"Connection Error: {str(ex)}"

        chat_column.controls.remove(typing)
        chat_column.controls.append(create_message(reply, False))
        page.update()

    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
        icon_color="white",
        bgcolor="#2563eb",
        on_click=send_message,
    )

    user_input.on_submit = send_message

    # -------------------------
    # Input Bar
    # -------------------------

    input_bar = ft.Container(
        bgcolor="#111827",
        padding=15,
        content=ft.Row(
            [
                user_input,
                send_button,
            ]
        ),
    )

    # -------------------------
    # Layout
    # -------------------------

    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    content=chat_column,
                    padding=20,
                    expand=True,
                ),
                input_bar,
            ],
            expand=True,
        )
    )


ft.app(target=main)