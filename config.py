from discord import Embed, Colour
token = "YOUR TOKEN"

dbconfig = {
    "host": "host",
    "port": 3306,
    "user": "user",
    "password": "password",
    "db": "db"
}

rows = [ # [name, db column name]
    ["Enabled", "is_enabled"],
    ["Level-Up Channel", "level_up_channel"],
    ["Level-Up Message", "level_up_message"],
    ["AntiSpam", "antispam"]
]

err = Embed(
    title="Error! ❌",
    description="You can only use this command in a server.",
    color=Colour.red()
)
noadmin = err.copy()
noadmin.description = "You need the `Administrator` permission to perform this action."