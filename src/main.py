import click


# Disable click.edit globally
def _forbidden_edit(*args, **kwargs):
    raise RuntimeError("click.edit() is disabled for security reasons")


click.edit = _forbidden_edit

# Now import the rest of your app
# from my_project import app

# if __name__ == "__main__":
#     app.run()
