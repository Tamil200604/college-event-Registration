import pandas as pd

def admin_login(username, password):
    admins = pd.read_csv("data/admins.csv")

    user = admins[
        (admins["username"] == username) &
        (admins["password"] == password)
    ]

    return not user.empty
