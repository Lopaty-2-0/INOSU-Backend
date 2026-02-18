def email_conversation_message(name, sender_name, task_name):
    return f"""<html lang="cs">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nová zpráva - INOSU</title>
            </head>

            <body style="font-family: Arial, sans-serif; background-color: #ffffff; padding: 0; margin: 20px 0 0;">
            <div class="container" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden;">

            <div class="header" style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;">
            <h1 style="color: #000000; margin: 0; font-size: 24px;">
            Zdravím, <span style="color: #752BDFFF;">{name}</span>!
            </h1>
            </div>

            <div class="content" style="padding: 20px 0; text-align: center;">
            <p style="margin: 0 0 15px 0; line-height: 1.6;">
            Máte novou zprávu od uživatele:
            </p>

            <div style="margin: 20px 0; padding: 15px; background-color: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb;">
            <p style="margin: 0 0 10px 0; font-size: 16px;">
            <strong>{sender_name}</strong>
            </p>

            <p style="margin: 0; font-size: 13px; color: #777;">
            Úkol: {task_name}
            </p>
            </div>

            <p style="margin: 15px 0 0 0; font-size: 14px;">
            Pro zobrazení celé zprávy se přihlaste do systému.
            </p>
            </div>

            <div class="footer" style="margin-top: 20px; font-size: 12px; color: #999999; text-align: center;">
            <p>© 2026 INOSU. Všechna práva vyhrazena.</p>
            </div>

            </div>
            </body>
            </html>"""