def emailResetPasswordTemplate(name, link):
    return f"""<!DOCTYPE html>
        <html lang="cs">

        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resetování zapomenutého hesla - INOSU</title>
        </head>

        <body style="font-family: Arial, sans-serif; background-color: #ffffff; padding: 0; margin: 20px 0 0;">
        <div class="container" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden;">
        <div class="header" style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;">
            <h1 style="color: #000000; margin: 0; font-size: 24px;">Zdravím, <span style="color: #752BDFFF;">{name}</span>!</h1>
        </div>
        <div class="content" style="padding: 20px 0; text-align: center;">
            <p style="margin: 0 0 15px 0; line-height: 1.6;">Klikněte na tlačítko níže pro resetování hesla - za 1 hodinu odkaz vyprší:</p>
            <a href= {link} class="button" style="display: inline-block; padding: 10px 20px; margin-top: 20px; margin-bottom: 20px; background-color: #752BDFFF; color: #ffffff; text-decoration: none; border-radius: 5px;">Klikněte zde</a>
            <p style="margin: 0 0 15px 0; line-height: 1.6;">Pokud tlačítko nefunguje, zkopírujte a vložte následující odkaz do svého prohlížeče:</p>
            <p class="link" style="max-width: 580px; overflow: hidden; word-break: break-all;"><a href="{link}" style="color: #752BDFFF;">{link}</a></p>
        </div>
        <div class="footer" style="margin-top: 20px; font-size: 12px; color: #999999; text-align: center;">
            <p>© 2025 INOSU. Všechna práva vyhrazena.</p>
        </div>
        </div>
        </body>

        </html>"""