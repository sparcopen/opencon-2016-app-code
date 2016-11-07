#!/usr/bin/env python
import os
import sys

import dotenv

if __name__ == "__main__":
    dotenv.read_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencon_project.settings.developer")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
